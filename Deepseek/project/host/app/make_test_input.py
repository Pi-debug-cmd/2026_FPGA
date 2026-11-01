"""Build the stage-1 test signals.

Two artifacts:
  data/test_src_16k.wav    16 kHz mono PCM16, the Python reference input
  data/test_src_32k_s24.raw  S24_LE / 32000 Hz / 2 ch raw, what the board plays in
                            (left channel = speech, right = a -6 dB delayed copy so
                            the pair is not identical; exercises the left-only rule)

The board only accepts S24_LE/32k/2ch, so the 32 k file is built by an explicit
2x upsample + 24-bit left-aligned packing exactly like the hardware delivers it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent


def upsample2(x: np.ndarray, fc_hz: float = 7800.0, taps: int = 127) -> np.ndarray:
    """x(16 kHz) -> 2x(32 kHz) with a Hamming-windowed sinc, matching the C tool.

    y[m] = 2 * sum_k h[k] * xu[m - k], xu = zero-stuffed x, h designed at 32 kHz.
    Zero padding at both ends, so the output is delayed by (taps-1)/2 samples.
    """
    n = len(x)
    fs_high = 32000
    fc_n = fc_hz / fs_high
    c = (taps - 1) // 2
    k = np.arange(taps) - c
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(k == 0, 1.0, np.sin(2 * np.pi * fc_n * k) / (2 * np.pi * fc_n * k))
    w = 0.54 - 0.46 * np.cos(2 * np.pi * np.arange(taps) / (taps - 1))
    h = 2.0 * fc_n * s * w
    h /= h.sum()
    xu = np.zeros(2 * n, dtype=np.float64)
    xu[::2] = x
    full = np.convolve(xu, h)              # length 2n + taps - 1
    return 2.0 * full[c:c + 2 * n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=str(ROOT / "data" / "pair16k" / "male" / "male_04.wav"))
    ap.add_argument("--start", type=float, default=1.0)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--peak", type=float, default=0.35,
                    help="normalise the slice to this peak (0.35 FS keeps 24-bit headroom)")
    args = ap.parse_args()

    x, sr = sf.read(args.wav, dtype="float64", always_2d=False)
    if x.ndim == 2:
        x = x.mean(axis=1)
    assert sr == 16000, sr
    a = int(round(args.start * sr))
    x = x[a:a + int(round(args.seconds * sr))].copy()
    x *= args.peak / max(np.abs(x).max(), 1e-9)
    n = len(x)

    sf.write(str(HERE / "data" / "test_src_16k.wav"),
             x.astype(np.float32), 16000, subtype="PCM_16")

    # 2x upsample with an explicit 127-tap Hamming-windowed sinc (cutoff 7.8 kHz
    # at 32 kHz).  scipy's resample_poly default filter is only 41 taps at
    # up=2 and rolls the band off from ~4 kHz, which is not what a real 32 kHz
    # capture looks like and it biases the model's c0 badly.
    x32 = upsample2(x, fc_hz=7800.0, taps=127)
    assert len(x32) == 2 * n, (len(x32), 2 * n)
    # right channel: 1 ms delayed, -6 dB, so left/right differ
    d = 32
    right = np.concatenate([np.zeros(d), x32[:-d]]) * 0.5
    inter = np.stack([x32, right], axis=1)                     # (2n, 2)
    # The board's S24_LE is a 32-bit container with the 24 valid bits left
    # justified (bits 31..8) -- confirmed by bringup_tool's wav24 mode, which
    # wrote `(int32)(v * 8388607) << 8` and played correctly.
    q24 = np.clip(np.round(inter * 8388608.0), -8388608, 8388607).astype(np.int32)
    q32 = q24 << 8
    out = q32.astype("<i4").tobytes()
    (HERE / "data" / "test_src_32k_s24.raw").write_bytes(out)

    meta = {
        "source": str(Path(args.wav).name),
        "start_s": args.start, "seconds": args.seconds,
        "samples_16k": int(n), "samples_32k": int(2 * n),
        "wav_16k_bytes": (HERE / "data" / "test_src_16k.wav").stat().st_size,
        "raw_s24_bytes": len(out),
        "raw_s24_expected": 2 * n * 2 * 4,
        "s24_layout": "int32 LE container, 24 valid bits left justified (<<8)",
        "peak_fs": round(float(np.abs(x).max()), 6),
        "rms_fs": round(float(np.sqrt(np.mean(x ** 2))), 6),
    }
    (HERE / "data" / "test_input.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
