"""Analyse the board run: verify the S24 raw output, build WAVs, and quantify the
agreement with the Python reference.

    analyze_board.py --board out/board --ref16 out/ref_pitch --out-wav out/audio

`--board` must contain the files downloaded from /tmp/vc:
    out.raw, dump/x16.f32, dump/xb16.f32, dump/y16.f32

Reported metrics
  * raw container/format checks (S24_LE 32 kHz stereo, length, clipping)
  * board y16 vs desk-side y16      -> ARM vs x86 build equivalence
  * board y16 vs Python oracle on the board's own x16/xB
                                    -> algorithmic parity of the shipped binary
  * board output vs the Python reference chain (librosa pitch shift)
                                    -> end-to-end difference, which is dominated by
                                       the pitch algorithm and the resampler, so it is
                                       reported in the envelope domain, not as SNR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

SR = 16000
SR32 = 32000
NBINS = 513


def read_s24_stereo(path: Path) -> np.ndarray:
    b = np.fromfile(path, dtype="<u4")
    if b.size % 2:
        raise SystemExit(f"{path}: odd sample count")
    q = b.astype(np.int32) >> 8            # 24 valid bits, left justified
    return q.reshape(-1, 2)


def best_lag_snr(ref: np.ndarray, est: np.ndarray, max_lag: int = 600):
    n = min(len(ref), len(est))
    a = ref[:n] - ref[:n].mean()
    best, bl = -1e30, 0
    for L in range(-max_lag, max_lag + 1):
        if L >= 0:
            x, y = a[L:], est[:n - L]
        else:
            x, y = a[:n + L], est[-L:n]
        c = float(np.dot(x, y - y.mean()))
        if c > best:
            best, bl = c, L
    if bl >= 0:
        x, y = ref[bl:n], est[:n - bl]
    else:
        x, y = ref[:n + bl], est[-bl:n]
    e = x - y
    snr = 10 * np.log10(float((x ** 2).sum()) / max(float((e ** 2).sum()), 1e-30))
    return bl, snr, float(np.corrcoef(x, y)[0, 1])


def world_logsp(x: np.ndarray):
    import pyworld as pw
    x = np.ascontiguousarray(x, dtype=np.float64)
    f0, t = pw.dio(x, SR, f0_floor=75.0, f0_ceil=400.0, frame_period=10.0, speed=4)
    f0 = pw.stonemask(x, f0, t, SR)
    sp = pw.cheaptrick(x, f0, t, SR, fft_size=1024, f0_floor=75.0)
    return f0, np.log(np.maximum(sp, 1e-16))


def band_profile(logsp: np.ndarray) -> np.ndarray:
    """Mean log spectrum in 10 perceptual bands (dB)."""
    edges = [0, 4, 8, 16, 32, 64, 128, 192, 256, 384, 513]
    out = []
    for i in range(len(edges) - 1):
        seg = logsp[:, edges[i]:edges[i + 1]]
        out.append(float(10.0 / np.log(10.0) * seg.mean()))
    return np.array(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--ref-same", default=None,
                    help="ref_port.py dir built from THIS board dump (--in-f32 x16 --xB-f32 xb16): "
                         "same-input comparison, sample-accurate SNR is meaningful")
    ap.add_argument("--ref16", default=None,
                    help="ref_port.py dir for the desk-side 16 kHz reference chain: different pitch "
                         "algorithm (librosa phase vocoder), so only the envelope is comparable")
    ap.add_argument("--host-y16", default=None, help="desk-side y16.f32 built from the same input")
    ap.add_argument("--out-wav", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    bd = Path(args.board)
    rep: dict = {}

    # ---------------------------------------------------------------- container
    raw = read_s24_stereo(bd / "out.raw")
    n_frames = raw.shape[0]
    left = raw[:, 0].astype(np.float64) / 8388608.0
    right = raw[:, 1].astype(np.float64) / 8388608.0
    rep["raw"] = {
        "bytes": (bd / "out.raw").stat().st_size,
        "frames": int(n_frames),
        "seconds": round(n_frames / SR32, 4),
        "channels": 2,
        "format": "S24_LE, 32-bit container, 24 valid bits left justified",
        "peak_left_fs": round(float(np.abs(left).max()), 6),
        "peak_right_fs": round(float(np.abs(right).max()), 6),
        "rms_left_fs": round(float(np.sqrt((left ** 2).mean())), 6),
        "clipped_samples": int(np.sum(np.abs(raw) >= 8388607)),
        "silent": bool(np.all(raw == 0)),
        "lr_identical": bool(np.array_equal(raw[:, 0], raw[:, 1])),
    }
    print("raw output:", json.dumps(rep["raw"], indent=2))

    y16 = np.fromfile(bd / "dump" / "y16.f32", dtype="<f4").astype(np.float64)
    x16 = np.fromfile(bd / "dump" / "x16.f32", dtype="<f4").astype(np.float64)
    xb16 = np.fromfile(bd / "dump" / "xb16.f32", dtype="<f4").astype(np.float64)
    rep["dump"] = {"x16": int(x16.size), "xb16": int(xb16.size), "y16": int(y16.size)}
    print(f"dumps: x16 {x16.size}, xb16 {xb16.size}, y16 {y16.size} samples")

    # ------------------------------------------------- ARM build vs x86 build
    if args.host_y16:
        h = np.fromfile(args.host_y16, dtype="<f4").astype(np.float64)
        if h.size == y16.size:
            d = np.abs(h - y16)
            snr = 10 * np.log10(float((h ** 2).sum()) / max(float((d ** 2).sum()), 1e-30))
            rep["arm_vs_x86"] = {"max_abs": float(d.max()), "rms": float(np.sqrt((d ** 2).mean())),
                                 "snr_db": float(snr), "bit_identical": bool(np.array_equal(h, y16))}
            print(f"\nARM vs x86 build (same input): max|d| {d.max():.3e}  SNR {snr:.2f} dB  "
                  f"bit_identical={rep['arm_vs_x86']['bit_identical']}")

    # --------------------------------------- shipped binary vs Python oracle
    if args.ref_same:
        z = np.load(Path(args.ref_same) / "stages.npz")
        y = z["y"].astype(np.float64)
        if y.size == y16.size:
            lag, snr, corr = best_lag_snr(y, y16)
            rep["board_vs_oracle_same_input"] = {
                "lag_samples": lag, "snr_db": round(snr, 3), "corr": corr,
                "max_abs": float(np.abs(y - y16).max()),
                "note": "oracle fed the board\x27s own x16/xB float32 dumps, so this isolates "
                        "the shipped binary from input rounding and from the pitch algorithm",
            }
            print(f"\nboard y16 vs oracle on the board dumps (includes float32 dump rounding): lag {lag:+d}  "
                  f"SNR {snr:.2f} dB  corr {corr:.6f}")

    if args.ref16:
        z = np.load(Path(args.ref16) / "stages.npz")
        y = z["y"].astype(np.float64)
        if y.size == y16.size:
            # end-to-end: envelope comparison against the 16k reference signal.
            # A sample-accurate SNR is NOT meaningful here: librosa shifts pitch with
            # a phase vocoder and SoundTouch with WSOLA, so the two waveforms have
            # different time structure (and librosa\x27s path loses 3.2 dB of level).
            f0c, lsc = world_logsp(y16)
            f0r, lsr = world_logsp(y)
            n = min(len(lsc), len(lsr))
            ls_c, ls_r = lsc[:n], lsr[:n]
            band_c, band_r = band_profile(ls_c), band_profile(ls_r)
            vu_c, vu_r = f0c[:n] > 0, f0r[:n] > 0
            rep["envelope_vs_reference"] = {
                "frames": int(n),
                "mean_abs_logsp_diff_db": round(float(np.abs(10 / np.log(10) * (ls_c - ls_r)).mean()), 3),
                "band_edges_bins": [0, 4, 8, 16, 32, 64, 128, 192, 256, 384, 513],
                "band_db_board": [round(v, 2) for v in band_c],
                "band_db_ref": [round(v, 2) for v in band_r],
                "band_db_diff": [round(float(a - b), 2) for a, b in zip(band_c, band_r)],
                "median_f0_board": round(float(np.median(f0c[vu_c])), 2) if vu_c.any() else 0.0,
                "median_f0_ref": round(float(np.median(f0r[vu_r])), 2) if vu_r.any() else 0.0,
            }
            print("\nenvelope vs 16 kHz reference (both pitch-shifted ~1.4x):")
            print("  band edges (bins):", [0, 4, 8, 16, 32, 64, 128, 192, 256, 384, 513])
            print("  board dB        :", [round(v, 1) for v in band_c])
            print("  reference dB    :", [round(v, 1) for v in band_r])
            print("  median F0 board %.1f Hz / ref %.1f Hz" % (
                rep["envelope_vs_reference"]["median_f0_board"],
                rep["envelope_vs_reference"]["median_f0_ref"]))

    # ---------------------------------------------------------------- WAVs out
    if args.out_wav:
        import soundfile as sf
        od = Path(args.out_wav)
        od.mkdir(parents=True, exist_ok=True)
        # 32 kHz stereo, same S24 container bits, as a float WAV for listening
        st = np.stack([left, right], axis=1)
        st = st - st.mean()
        sf.write(str(od / "board_out_32k.wav"), st.astype(np.float32), SR32, subtype="FLOAT")
        # 16 kHz mono of the internal output (what the algorithm actually produced)
        p = float(np.abs(y16).max())
        yw = y16 * (0.99 / p) if p > 0.99 else y16
        sf.write(str(od / "board_out_16k.wav"), yw.astype(np.float32), SR, subtype="PCM_16")
        # source for A/B
        pw16 = x16
        p = float(np.abs(pw16).max())
        sf.write(str(od / "source_16k.wav"), (pw16 * (0.99 / p) if p > 0.99 else pw16).astype(np.float32),
                 SR, subtype="PCM_16")
        p = float(np.abs(xb16).max())
        sf.write(str(od / "pitchshifted_16k.wav"), (xb16 * (0.99 / p) if p > 0.99 else xb16).astype(np.float32),
                 SR, subtype="PCM_16")
        rep["wav"] = sorted(p.name for p in od.glob("*.wav"))
        print("\nwrote WAVs:", rep["wav"])

    if args.json:
        Path(args.json).write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        print("json ->", args.json)


if __name__ == "__main__":
    main()
