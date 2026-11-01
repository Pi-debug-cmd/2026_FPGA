"""RMS-normalise a raw f32 signal exactly like psola_20261025.normalise() and
write a 16 kHz PCM16 wav (same protocol as the reference O64.wav).

  f32_norm_wav.py in.f32 out.wav [--target-dbfs -23] [--peak-ceil 0.99]
"""
from __future__ import annotations

import argparse

import numpy as np
import soundfile as sf
from scipy.ndimage import minimum_filter1d

SR = 16000


def normalise(y: np.ndarray, target_dbfs: float, peak_ceil: float) -> tuple[np.ndarray, dict]:
    y = np.asarray(y, dtype=np.float64)
    g0 = 10.0 ** (target_dbfs / 20.0) / max(np.sqrt(np.mean(y * y)), 1e-12)
    y = y * g0
    info = {"gain_db": round(float(20 * np.log10(g0)), 3), "peak_guard": False}
    peak = float(np.abs(y).max())
    if peak > peak_ceil:
        g = np.minimum(1.0, peak_ceil / np.maximum(np.abs(y), 1e-12))
        g = minimum_filter1d(g, size=max(int(0.003 * SR) | 1, 3), mode="nearest")
        g = minimum_filter1d(g, size=max(int(0.020 * SR) | 1, 3), mode="nearest")
        k = max(int(0.005 * SR) | 1, 3)
        w = np.hanning(k)
        g = np.convolve(g, w / w.sum(), mode="same")
        y = y * np.minimum(g, 1.0)
        info["peak_guard"] = True
        info["peak_after"] = float(np.abs(y).max())
    info["rms_after_dbfs"] = round(float(20 * np.log10(np.sqrt(np.mean(y * y)) + 1e-12)), 2)
    return y, info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--target-dbfs", type=float, default=-23.0)
    ap.add_argument("--peak-ceil", type=float, default=0.99)
    args = ap.parse_args()
    y = np.fromfile(args.src, dtype="<f4").astype(np.float64)
    y, info = normalise(y, args.target_dbfs, args.peak_ceil)
    sf.write(args.dst, y.astype(np.float32), SR, subtype="PCM_16")
    print(args.dst, "n=", len(y), info)


if __name__ == "__main__":
    main()
