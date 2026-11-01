# -*- coding: utf-8 -*-
"""Emit the full 401-frame board stimulus and the numpy reference for M2/M3."""
import os
import numpy as np

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main():
    xq = np.load(os.path.join(D, "xq.npy"))       # (401,1024) int16
    gq = np.load(os.path.join(D, "gq.npy"))       # (401,513) int64 Q4.19
    Yq = np.load(os.path.join(D, "Yq.npy"))       # (401,1024) complex, 6 frac bits
    T = xq.shape[0]
    print("frames", T)

    xq.astype("<i2").tofile(os.path.join(D, "stim_x.bin"))
    gq.astype("<i4").tofile(os.path.join(D, "stim_g.bin"))

    # RTL: y = sum Y e^{+i} = 1024*ifft(Y); out = (y + 128) >> 8
    y = (1024.0 * np.fft.ifft(Yq, axis=1)).real
    ref = np.floor_divide(np.rint(y).astype(np.int64) + 128, 256)
    ref.astype("<i4").tofile(os.path.join(D, "ref_z.bin"))
    print("stim_x", os.path.getsize(os.path.join(D, "stim_x.bin")),
          "stim_g", os.path.getsize(os.path.join(D, "stim_g.bin")),
          "ref_z", os.path.getsize(os.path.join(D, "ref_z.bin")))
    print("ref peak", int(np.abs(ref).max()), "2^%.2f" % np.log2(np.abs(ref).max()))


if __name__ == "__main__":
    main()
