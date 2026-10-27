# -*- coding: utf-8 -*-
"""End-to-end comparison of the all-ARM binary against the PL-STFT binary.

Both write S24_LE stereo 32 kHz (or raw float32 with --out-f32-16k); this script
decodes the left channel to int16 and reports correlation, max/rms difference in
int16 LSBs and the sample count that differs by more than 1 or 2 LSB.
"""
import sys
import numpy as np


def load_s24(path, ch=2):
    raw = np.fromfile(path, dtype=np.uint8)
    n = raw.size // (4 * ch)
    a = raw[:n * 4 * ch].reshape(n, ch, 4)
    out = []
    for c in range(ch):
        w = (a[:, c, 0].astype(np.int64) |
             (a[:, c, 1].astype(np.int64) << 8) |
             (a[:, c, 2].astype(np.int64) << 16))
        v = (w ^ 0x800000) - 0x800000          # sign-extend 24 bit
        out.append(np.round(v / 256.0))         # int16 units
    return np.array(out)


def main(a_path, b_path):
    A = load_s24(a_path)
    B = load_s24(b_path)
    if A.shape != B.shape:
        print(f"shape mismatch {A.shape} vs {B.shape}")
        return
    print(f"samples {A.shape[1]} channels {A.shape[0]}")
    for c in range(A.shape[0]):
        a, b = A[c], B[c]
        d = b - a
        corr = np.corrcoef(a, b)[0, 1]
        print(f"ch{c}: corr={corr:.8f} max|d|={np.abs(d).max():.0f} "
              f"rms={np.sqrt((d**2).mean()):.3f} >1LSB={int((np.abs(d) > 1).sum())} "
              f">2LSB={int((np.abs(d) > 2).sum())}")
    a, b = A.ravel(), B.ravel()
    print(f"overall corr={np.corrcoef(a, b)[0,1]:.8f} "
          f"max|d|={np.abs(b-a).max():.0f} rms={np.sqrt(((b-a)**2).mean()):.3f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
