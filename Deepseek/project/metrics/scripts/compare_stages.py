"""Compare the C port against the Python oracle stage by stage.

Reads the float32 dumps written by `vc_stream --dump DIR` and the `stages.npz`
written by ref_port.py, and reports per-stage absolute/relative error and
correlation, plus the final waveform SNR after aligning the best integer lag.

Usage:
    compare_stages.py --ref out/ref_nopitch --c out/c_nopitch
    compare_stages.py --ref out/ref_nopitch --export-x16 out/c_nopitch/x16.f32
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

# (C dump name, npz key, label, tolerance for "match")
STAGES = [
    ("f0.f32", "f0", "f0 (Hz)", 1e-4),
    ("logsp.f32", "logsp", "logsp (WORLD, T x 513)", 1e-4),
    ("ap.f32", "ap", "aperiodicity D4C", 1e-4),
    ("feats.f32", "feats", "frame features (T x 68)", 1e-5),
    ("stats.f32", "stats", "utterance stats (34)", 1e-5),
    ("xn.f32", "Xn", "normalised input (T x 646)", 1e-4),
    ("res.f32", "res", "MLP residual (T x 48)", 1e-4),
    ("logsp_pred.f32", "logsp_pred", "predicted envelope (T x 513)", 1e-3),
    ("logsp_den.f32", "logsp_b", "denominator envelope (T x 513)", 1e-4),
    ("diff_db.f32", "diff_db", "gain after clamp (T x 513 dB)", 1e-3),
    ("mask.f32", "mask", "silence mask (T)", 1e-6),
    ("xb16.f32", "xB", "pitch-shifted signal", 1e-6),
    ("y16.f32", "y", "final 16 kHz output", 1e-4),
]


def load_c(path: Path) -> np.ndarray:
    return np.fromfile(path, dtype="<f4").astype(np.float64)


def snr_db(ref: np.ndarray, est: np.ndarray) -> float:
    n = min(len(ref), len(est))
    e = ref[:n] - est[:n]
    num = float(np.sum(ref[:n] ** 2))
    den = float(np.sum(e ** 2))
    return 99.0 if den <= 1e-30 else 10.0 * np.log10(num / den)


def best_lag(ref: np.ndarray, est: np.ndarray, max_lag: int = 400) -> int:
    """lag L such that est[n] ~ ref[n - L] (positive = est is delayed)."""
    n = min(len(ref), len(est))
    a = ref[:n] - ref[:n].mean()
    best, bl = -1e30, 0
    for L in range(-max_lag, max_lag + 1):
        if L >= 0:
            x, y = a[L:], est[:n - L]
        else:
            x, y = a[:n + L], est[-L:n]
        y = y - y.mean()
        c = float(np.dot(x, y))
        if c > best:
            best, bl = c, L
    return bl


def align(ref: np.ndarray, est: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    if lag >= 0:
        return ref[lag:], est[:len(ref) - lag]
    return ref[:len(ref) + lag], est[-lag:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="ref_port.py output dir")
    ap.add_argument("--c", default=None, help="vc_stream --dump dir")
    ap.add_argument("--export-x16", default=None, help="write the oracle x as raw f32")
    ap.add_argument("--json", default=None, help="also write the table as JSON")
    ap.add_argument("--strict", action="store_true", help="non-zero exit on any tolerance miss")
    args = ap.parse_args()

    z = np.load(Path(args.ref) / "stages.npz")
    if args.export_x16:
        x = z["x"].astype("<f4")
        Path(args.export_x16).parent.mkdir(parents=True, exist_ok=True)
        x.tofile(args.export_x16)
        print(f"wrote {args.export_x16}  {len(x)} samples ({len(x)/16000:.3f} s)")
        return
    if not args.c:
        ap.error("--c or --export-x16 required")

    rows, ok = [], True
    cdir = Path(args.c)
    print(f"{'stage':38s} {'shape':>14s} {'max_abs':>11s} {'rms_err':>11s} "
          f"{'rel_rms':>10s} {'corr':>9s}  verdict")
    for fname, key, label, tol in STAGES:
        p = cdir / fname
        if not p.exists() or key not in z:
            print(f"{label:38s} {'(missing)':>14s}")
            continue
        c = load_c(p)
        r = z[key].astype(np.float64).ravel()
        if c.size != r.size:
            print(f"{label:38s} {'size mismatch':>14s}  C={c.size} py={r.size}")
            ok = False
            continue
        d = np.abs(c - r)
        rms_e = float(np.sqrt(np.mean(d ** 2)))
        ref_rms = float(np.sqrt(np.mean(r ** 2))) + 1e-30
        corr = float(np.corrcoef(c, r)[0, 1]) if c.size > 2 and np.std(c) > 0 and np.std(r) > 0 else 1.0
        maxa = float(d.max())
        verdict = "OK" if (maxa <= tol or rms_e / ref_rms <= 1e-3) else "CHECK"
        if verdict != "OK":
            ok = False
        rows.append(dict(stage=key, label=label, n=int(c.size), max_abs=maxa,
                         rms_err=rms_e, rel_rms=rms_e / ref_rms, corr=corr,
                         tol=tol, verdict=verdict))
        print(f"{label:38s} {str(r.shape):>14s} {maxa:11.3e} {rms_e:11.3e} "
              f"{rms_e/ref_rms:10.3e} {corr:9.5f}  {verdict}")

    # ---- final waveform SNR with the best integer lag
    if (cdir / "y16.f32").exists() and "y" in z:
        c = load_c(cdir / "y16.f32")
        r = z["y"].astype(np.float64)
        L = best_lag(r, c)
        ra, ca = align(r, c, L)
        s = snr_db(ra, ca)
        print(f"\nwaveform: best lag {L:+d} samples ({L/16.0:+.2f} ms)  "
              f"SNR {s:.2f} dB  corr {np.corrcoef(ra, ca)[0,1]:.6f}")
        rows.append(dict(stage="waveform_aligned", lag=L, snr_db=s))
        if s < 30.0:
            ok = False

    if args.json:
        Path(args.json).write_text(json.dumps({"stages": rows, "all_ok": ok}, indent=2),
                                   encoding="utf-8")
    print("\nALL_OK" if ok else "\nSOME_STAGES_NEED_ATTENTION")
    if args.strict and not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
