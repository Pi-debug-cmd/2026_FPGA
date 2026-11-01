# -*- coding: utf-8 -*-
"""Compare xsim dumps against numpy.

M2 : out.hex  -> 32-bit words, value = z * SCALE, where z is the filtered
     time frame in int16 units (i.e. the C program's float frame * 32768).
M1 : fwd_out.hex -> 1024 (re,im) 40-bit two's-complement pairs per frame,
                   compare with fft(xq)*8 (input is xq, unscaled).
"""
import sys, os, json
import numpy as np

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
NFFT = 1024


def s32(hexstr):
    v = int(hexstr, 16)
    return v - (1 << 32) if v >= (1 << 31) else v


def s40(hexstr):
    v = int(hexstr, 16)
    return v - (1 << 40) if v >= (1 << 39) else v


def s48(hexstr):
    v = int(hexstr, 16)
    return v - (1 << 48) if v >= (1 << 47) else v


def load_out(path, scale=256.0):
    vals = [int(l, 16) for l in open(path) if l.strip()]
    a = np.array([v - (1 << 32) if v >= (1 << 31) else v for v in vals], dtype=np.float64)
    return a / scale


def m2(path, scale=256.0):
    xq = np.load(os.path.join(D, "xq.npy"))
    g = np.load(os.path.join(D, "gain.npy"))
    got = load_out(path, scale)
    nfr = got.size // NFFT
    got = got[:nfr * NFFT].reshape(nfr, NFFT)
    ref = np.zeros_like(got)
    for t in range(nfr):
        X = np.fft.fft(xq[t].astype(np.float64))
        ref[t] = np.fft.ifft(X * g[t]).real
    err = got - ref
    # report per-sample error in int16 LSB (z is already in int16 units)
    print(f"M2 frames={nfr} samples={got.size}")
    print(f"  max|err|   = {np.abs(err).max():.3f} LSB")
    print(f"  rms err    = {np.sqrt((err**2).mean()):.4f} LSB")
    print(f"  corr       = {np.corrcoef(got.ravel(), ref.ravel())[0,1]:.8f}")
    ok = np.abs(err).max() <= 2.0
    print(f"  VERDICT    = {'PASS' if ok else 'FAIL'} (<=2 LSB)")
    return {"frames": nfr, "max_abs_lsb": float(np.abs(err).max()),
            "rms_lsb": float(np.sqrt((err ** 2).mean())),
            "corr": float(np.corrcoef(got.ravel(), ref.ravel())[0, 1]),
            "pass": bool(ok)}


def m1_fwd(path):
    xq = np.load(os.path.join(D, "xq.npy"))
    rows = [l.split() for l in open(path) if l.strip()]
    n = len(rows)
    nfr = n // NFFT
    re = np.array([s40(r[0]) for r in rows], dtype=np.float64)[:nfr * NFFT]
    im = np.array([s40(r[1]) for r in rows], dtype=np.float64)[:nfr * NFFT]
    got = (re + 1j * im).reshape(nfr, NFFT)
    res = []
    for t in range(nfr):
        A = np.fft.fft(xq[t].astype(np.float64))
        e = np.abs(got[t] - A)
        mag = np.abs(A)
        rel = e / np.maximum(mag, 1e-9)
        strong = mag > mag.max() * 1e-3
        res.append({"frame": t, "max_abs": float(e.max()),
                    "max_rel_strong": float(rel[strong].max()),
                    "snr_db": float(10 * np.log10((mag ** 2).sum() / max((e ** 2).sum(), 1e-30)))})
        print(f"M1 fwd frame {t}: max_abs={e.max():.3f} "
              f"max_rel(>-60dB bins)={rel[strong].max():.2e} snr={res[-1]['snr_db']:.1f} dB")
    return res


def m1_inv(path):
    rows = [l.split() for l in open(path) if l.strip()]
    nfr = len(rows) // NFFT
    Yq = np.load(os.path.join(D, "Yq.npy"))[:nfr]
    re = np.array([s48(r[0]) for r in rows], dtype=np.float64)[:nfr * NFFT].reshape(nfr, NFFT)
    res = []
    for t in range(nfr):
        ref = (NFFT * np.fft.ifft(Yq[t].astype(np.float64))).real
        e = np.abs(re[t] - ref)
        rel = e / np.maximum(np.abs(ref), 1.0)
        res.append({"frame": t, "max_abs": float(e.max()),
                    "max_rel": float(rel.max())})
        print(f"M1 inv frame {t}: max_abs={e.max():.3f} max_rel={rel.max():.2e} "
              f"(ref peak {np.abs(ref).max():.1f})")
    return res


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "m2"
    path = sys.argv[2] if len(sys.argv) > 2 else "out.hex"
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 256.0
    if what == "m2":
        r = m2(path, scale)
    elif what == "fwd":
        r = m1_fwd(path)
    else:
        r = m1_inv(path)
    print(json.dumps(r, indent=1))

