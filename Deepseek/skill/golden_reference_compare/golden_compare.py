#!/usr/bin/env python3
"""golden_compare.py - compare a device-under-test output against a golden reference.

Why this exists
---------------
"It sounds right" and "the diff looks small" are not acceptance criteria.  This
tool turns a comparison into a *verdict* plus a *mismatch shape*, because the
shape is what tells you which layer is broken:

    32-byte zero runs, first transfer only     -> cache writeback (see dma_cache_coherency)
    every bin of every frame wrong, same scale -> missing/incorrect LUT interpolation
    one frame at each block boundary           -> overlap / TLAST / state carry bug
    1-2 LSB everywhere, no structure           -> rounding mode of the fixed-point model
    lag != 0                                   -> group delay / resampler offset

Two-level acceptance (borrowed from the project's own gate discipline):
    strict  : max|diff| == 0                      (bit-exact, e.g. RTL vs integer model)
    numeric : max|diff| <= tol  or  SNR >= snr_min (float pipelines: tol=2 LSB, snr>=100 dB)

Supported inputs (chosen so you never have to convert by hand):
    .f32/.bin32  raw little-endian float32      .raw/.pcm  raw little-endian int16
    .npy         numpy array                    .csv/.txt  whitespace/comma separated
    .wav         16-bit PCM RIFF                dtype is inferred from the suffix

Exit code: 0 = pass, 1 = fail, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import wave
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------- loaders
def load_any(path: Path, dtype: str | None, count: int | None, offset: int) -> np.ndarray:
    suf = path.suffix.lower()
    if dtype is None:
        dtype = {".f32": "f32", ".bin32": "f32", ".raw": "i16", ".pcm": "i16",
                 ".wav": "wav"}.get(suf, "auto")
    if dtype == "wav":
        with wave.open(str(path), "rb") as w:
            if w.getsampwidth() != 2:
                raise SystemExit("%s: only 16-bit PCM wav supported (%d bytes/sample)"
                                 % (path, w.getsampwidth()))
            ch = w.getnchannels()
            a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64)
        return a.reshape(-1, ch).mean(axis=1) if ch > 1 else a
    if suf == ".npy" or dtype == "npy":
        a = np.load(path).astype(np.float64)
        return a
    if suf in (".csv", ".txt") or dtype == "text":
        a = np.loadtxt(path, delimiter="," if suf == ".csv" else None, ndmin=1)
        return np.asarray(a, dtype=np.float64).ravel()
    raw = np.fromfile(path, dtype="<f4" if dtype == "f32" else "<i2")
    if offset:
        raw = raw[offset:]
    if count:
        raw = raw[:count]
    return raw.astype(np.float64)


# ---------------------------------------------------------------- alignment
def best_lag(ref: np.ndarray, dut: np.ndarray, max_lag: int) -> tuple[int, float]:
    """Integer lag that maximises correlation; used to separate 'algorithm differs'
    from 'the pipeline is just delayed'."""
    n = min(len(ref), len(dut))
    if n == 0:
        return 0, 0.0
    r = ref[:n] - ref[:n].mean()
    best, bestv = 0, -2.0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a, b = r[lag:], dut[:n - lag]
        else:
            a, b = r[:n + lag], dut[-lag:n]
        m = min(len(a), len(b))
        if m < 16:
            continue
        a, b = a[:m], b[:m] - b[:m].mean()
        den = np.linalg.norm(a) * np.linalg.norm(b)
        v = float(a @ b / den) if den > 0 else 0.0
        if v > bestv:
            best, bestv = lag, v
    return best, bestv


def apply_lag(ref: np.ndarray, dut: np.ndarray, lag: int):
    if lag >= 0:
        return ref[lag:], dut[:len(ref) - lag]
    return ref[:len(ref) + lag], dut[-lag:]


# ---------------------------------------------------------------- analysis
def analyse(ref: np.ndarray, dut: np.ndarray, tol: float, snr_min: float) -> dict:
    """ref/dut must have the same shape. 2-D input is treated as (frames, bins)."""
    flat_r, flat_d = ref.ravel(), dut.ravel()
    diff = flat_d - flat_r
    ad = np.abs(diff)
    rms_d = float(np.sqrt(np.mean(diff ** 2))) if diff.size else 0.0
    rms_r = float(np.sqrt(np.mean(flat_r ** 2))) if flat_r.size else 0.0
    snr = math.inf if rms_d == 0 else (20 * math.log10(rms_r / rms_d) if rms_r > 0 else -math.inf)
    corr = float(np.corrcoef(flat_r, flat_d)[0, 1]) if flat_r.size > 1 and flat_r.std() > 0 else 1.0

    bad = np.nonzero(diff != 0)[0]
    rec = {
        "samples": int(flat_d.size),
        "max_abs_diff": float(ad.max()) if ad.size else 0.0,
        "rms_diff": rms_d,
        "snr_db": None if math.isinf(snr) else round(snr, 2),
        "inf_snr": math.isinf(snr),
        "corr": round(corr, 9),
        "mismatch_count": int(bad.size),
        "mismatch_frac": round(float(bad.size) / flat_d.size, 6) if flat_d.size else 0.0,
        "first_bad": int(bad[0]) if bad.size else None,
        "rms_ref": rms_r,
        "rel_max_diff": (float(ad.max()) / rms_r) if (ad.size and rms_r > 0) else 0.0,
    }

    # --- mismatch shape
    if bad.size:
        runs, lens, allzero = [], [], []
        start = prev = int(bad[0])
        for i in bad[1:]:
            i = int(i)
            if i == prev + 1:
                prev = i
                continue
            runs.append((start, prev))
            start = prev = i
        runs.append((start, prev))
        for a, b in runs:
            lens.append(b - a + 1)
            allzero.append(bool(np.all(flat_d[a:b + 1] == 0)))
        zero_len = [l for l, z in zip(lens, allzero) if z]
        rec["mismatch_runs"] = len(runs)
        rec["first_run"] = {"start": runs[0][0], "len": lens[0],
                            "all_zero": allzero[0]}
        rec["max_run_len"] = int(max(lens))
        rec["zero_runs"] = len(zero_len)
        rec["zero_run_lengths"] = sorted(set(zero_len))
        if ref.ndim == 2 and ref.shape[1] > 1:
            bad_frames = np.unique(bad // ref.shape[1])
            bad_bins = np.unique(bad % ref.shape[1])
            rec["frames_total"] = int(ref.shape[0])
            rec["frames_bad"] = int(bad_frames.size)
            rec["bins_total"] = int(ref.shape[1])
            rec["bins_bad"] = int(bad_bins.size)
    rec["shape"] = list(ref.shape)
    rec["gate"] = {
        "bit_exact": rec["max_abs_diff"] == 0.0,
        "within_tol": rec["max_abs_diff"] <= tol,
        "snr_ok": rec["inf_snr"] or (rec["snr_db"] is not None and rec["snr_db"] >= snr_min),
    }
    rec["pass"] = bool(rec["gate"]["bit_exact"] or
                       (rec["gate"]["snr_ok"] and rec["gate"]["within_tol"]))
    return rec


def verdict_text(rec: dict) -> str:
    if rec["pass"] and rec["gate"]["bit_exact"]:
        return "PASS (bit-exact)"
    if rec["pass"]:
        return "PASS (numeric: max %.3g <= tol, snr %s dB)" % (
            rec["max_abs_diff"], rec["snr_db"])
    if rec.get("zero_runs") and rec.get("mismatch_frac", 1.0) < 0.01:
        return ("FAIL - small all-zero runs (len %s) on <1%% of samples: "
                "cache-line writeback, see skill/dma_cache_coherency" %
                (rec.get("zero_run_lengths"),))
    if rec.get("bins_total") and rec.get("bins_bad") == rec["bins_total"] and \
            rec.get("frames_bad") == rec.get("frames_total"):
        return "FAIL - every bin of every frame: systematic (LUT interpolation / scaling / index)"
    if rec.get("mismatch_frac", 0) > 0.5 and rec.get("rel_max_diff", 1) < 1e-2:
        return ("FAIL - differs almost everywhere but only by <=%.1e of signal RMS: "
                "numeric axis (1-ulp input amplification, rounding mode), not a "
                "structural bug" % rec["rel_max_diff"])
    if rec.get("rms_ref", 0) > 100 and rec.get("max_abs_diff", 0) <= 4:
        return "FAIL - only %d LSB: rounding mode of the fixed-point model, not a logic bug" % \
               rec["max_abs_diff"]
    return "FAIL"


# ---------------------------------------------------------------- cli
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference")
    ap.add_argument("dut")
    ap.add_argument("--dtype", choices=["f32", "i16", "npy", "text", "wav", "auto"], default="auto")
    ap.add_argument("--shape", default=None, help="reshape both, e.g. 401x513")
    ap.add_argument("--offset", type=int, default=0, help="skip N samples at the start (both)")
    ap.add_argument("--count", type=int, default=None)
    ap.add_argument("--tol", type=float, default=2.0, help="max|diff| allowed (default 2 LSB)")
    ap.add_argument("--snr-min", type=float, default=100.0)
    ap.add_argument("--max-lag", type=int, default=512, help="0 disables lag search")
    ap.add_argument("--json", default=None)
    ap.add_argument("--md", default=None, help="append a markdown row to this file")
    ap.add_argument("--label", default=None)
    args = ap.parse_args(argv)

    ref = load_any(Path(args.reference), None if args.dtype == "auto" else args.dtype,
                   args.count, args.offset)
    dut = load_any(Path(args.dut), None if args.dtype == "auto" else args.dtype,
                   args.count, args.offset)
    if args.shape:
        fr, fb = (int(x) for x in args.shape.lower().split("x"))
        if ref.size == fr * fb:
            ref = ref.reshape(fr, fb)
        if dut.size == fr * fb:
            dut = dut.reshape(fr, fb)

    n = min(ref.size, dut.size)
    if ref.size != dut.size:
        print("WARN length mismatch: ref=%d dut=%d, comparing first %d"
              % (ref.size, dut.size, n), file=sys.stderr)
    ref, dut = ref.ravel()[:n], dut.ravel()[:n]

    lag, lagcorr = 0, 1.0
    if args.max_lag > 0 and ref.size:
        lag, lagcorr = best_lag(ref, dut, args.max_lag)
        if lag:
            ref, dut = apply_lag(ref, dut, lag)

    # reshape only for the per-frame / per-bin localisation, after alignment
    if args.shape:
        fr, fb = (int(x) for x in args.shape.lower().split("x"))
        if ref.size == fr * fb:
            ref, dut = ref.reshape(fr, fb), dut.reshape(fr, fb)
        else:
            print("WARN --shape %dx%d does not match %d samples, keeping 1-D"
                  % (fr, fb, ref.size), file=sys.stderr)

    rec = analyse(np.asarray(ref), np.asarray(dut), args.tol, args.snr_min)
    rec.update({"reference": str(args.reference), "dut": str(args.dut),
                "label": args.label or Path(args.dut).stem,
                "lag": lag, "lag_corr": round(lagcorr, 9),
                "tol": args.tol, "snr_min": args.snr_min})
    rec["verdict"] = verdict_text(rec)

    print(json.dumps(rec, indent=2, ensure_ascii=False))
    if args.json:
        Path(args.json).write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    if args.md:
        row = "| %s | %s | %d | %s | %s | %d | %s |\n" % (
            rec["label"], rec["shape"], rec["samples"],
            ("%.3g" % rec["max_abs_diff"]),
            ("inf" if rec["inf_snr"] else rec["snr_db"]),
            rec["mismatch_count"], rec["verdict"])
        p = Path(args.md)
        header = ("| dut | shape | samples | max_abs_diff | snr_db | mismatches | verdict |\n"
                  "|---|---|---|---|---|---|---|\n")
        if not p.exists():
            p.write_text(header, encoding="utf-8")
        with p.open("a", encoding="utf-8") as f:
            f.write(row)
    return 0 if rec["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
