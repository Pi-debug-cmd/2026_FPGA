# -*- coding: utf-8 -*-
"""Rebuild the exact STFT/gain/ISTFT reference chain from the C program's own
dumps (out/c32/xb16.f32, diff_db.f32, mask.f32).

Purpose:
  1. prove we understand the chain the PL has to replace (bit-comparable to the
     C program's y16.f32),
  2. emit per-frame integer stimulus (int16 windowed samples + Q19 gains) for the
     RTL testbench,
  3. emit the numpy floats for the M1 (per-bin spectrum) and M2 (per-sample
     waveform) comparisons.
"""
import os, sys, json
import numpy as np

NFFT, WIN, HOP, NBIN = 1024, 1024, 160, 513
# Input dumps come from the vc_o64 run that produced out/c32/*.f32 (`--dump`); they
# are NOT shipped (they are 4 MB of intermediates). Point these two at your own
# dump directory / work directory, or set FVC_DUMP_DIR / FVC_WORK_DIR.
SRC = os.environ.get("FVC_DUMP_DIR", r"out\c32")
OUT = os.environ.get("FVC_WORK_DIR", r"work\ref_chain")


def _need(p):
    if not os.path.isdir(p):
        sys.exit("ref_chain: dump dir not found: %s\n"
                 "  This tool needs the four float32 dumps produced by\n"
                 "  `vc_o64 ... --dump <dir>` (xb16/y16/diff_db/mask).\n"
                 "  Set FVC_DUMP_DIR to that directory (see fpga/stft/README.md §6)." % p)
    return p


def load(name, count=None):
    _need(SRC)
    a = np.fromfile(os.path.join(SRC, name), dtype=np.float32)
    if count is not None:
        assert a.size == count, (name, a.size, count)
    return a


def main():
    os.makedirs(OUT, exist_ok=True)
    xb = load("xb16.f32").astype(np.float64)
    y16 = load("y16.f32").astype(np.float64)
    diff = load("diff_db.f32").astype(np.float64)
    mask = load("mask.f32").astype(np.float64)
    T = diff.size // NBIN
    n = xb.size
    print(f"n={n} T={T} mask={mask.size}")

    win = 0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(NFFT) / NFFT)   # periodic hann
    frames = T
    assert frames == 1 + n // HOP, (frames, 1 + n // HOP)

    xin = np.zeros((frames, NFFT), dtype=np.float64)
    for t in range(frames):
        start = t * HOP - NFFT // 2
        for i in range(NFFT):
            j = start + i
            if 0 <= j < n:
                xin[t, i] = xb[j] * win[i]

    # gain = exp(diff_db * (1-mask) * ln10/20);  diff_db already clamped at +-20 dB
    gdb = diff.reshape(frames, NBIN) * (1.0 - mask)[:, None]
    gain = np.exp(gdb * (np.log(10.0) / 20.0))

    X = np.fft.rfft(xin, n=NFFT, axis=1)          # (frames, 513), unnormalised
    Y = X * gain

    # ISTFT: Hermitian expansion + inverse, OLA, wsum normalise
    y = np.fft.irfft(Y, n=NFFT, axis=1)           # numpy includes 1/N
    n_full = NFFT + HOP * (frames - 1)
    acc = np.zeros(n_full)
    wsum = np.zeros(n_full)
    for t in range(frames):
        s = t * HOP
        acc[s:s + NFFT] += win * y[t]
        wsum[s:s + NFFT] += win * win
    pad = NFFT // 2
    out = np.zeros(n)
    for i in range(n):
        j = i + pad
        d = wsum[j] if j < n_full else 0.0
        v = acc[j] if j < n_full else 0.0
        out[i] = v / d if d > 0 else 0.0

    err = np.abs(out - y16)
    print(f"recompute vs C y16: max={err.max():.3e} rms={np.sqrt((err**2).mean()):.3e} "
          f"corr={np.corrcoef(out, y16)[0,1]:.8f}")

    # ---- integer stimulus for RTL: int16 samples, Q19 gains
    xq = np.clip(np.round(xin * 32768.0), -32768, 32767).astype(np.int16)
    gq = np.round(gain * (1 << 19)).astype(np.int64)
    assert gq.min() >= -(1 << 23) and gq.max() < (1 << 23), (gq.min(), gq.max())
    print(f"gain: min={gain.min():.6f} max={gain.max():.6f}  q19 min={gq.min()} max={gq.max()}")

    # integer reference spectra: numpy fft of the int16 frame / 1024, in 24-bit
    Xq = np.fft.fft(xq.astype(np.float64), axis=1) / NFFT     # scaled-forward semantics

    np.save(os.path.join(OUT, "xb.npy"), xb)
    np.save(os.path.join(OUT, "gain.npy"), gain)
    np.save(os.path.join(OUT, "Xq.npy"), Xq)
    np.save(os.path.join(OUT, "xq.npy"), xq)
    np.save(os.path.join(OUT, "gq.npy"), gq)
    np.save(os.path.join(OUT, "y_ref.npy"), out)
    np.save(os.path.join(OUT, "y_c.npy"), y16)

    # hex stimulus, a few frames for xsim (full set is large but still fine)
    nsim = int(os.environ.get("NSIM", "4"))
    with open(os.path.join(OUT, "x_in.hex"), "w") as f:
        for t in range(nsim):
            for v in xq[t]:
                f.write(f"{int(v) & 0xFFFF:04x}\n")
    with open(os.path.join(OUT, "g_in.hex"), "w") as f:
        for t in range(nsim):
            for v in gq[t]:
                f.write(f"{int(v) & 0xFFFFFF:06x}\n")

    # ---- M1 reference: unscaled integer FFT of the int16 frame (x8 scaling) --
    # RTL feeds a[n] = xq[n]*8, so A[k] = 8*fft(xq)[k].
    A = np.fft.fft(xq.astype(np.float64), axis=1)
    # M2 reference: what the RTL multiplier must produce, Y = A*g_q >> 29
    gain_full = np.concatenate([gain, gain[:, 1:NBIN-1][:, ::-1]], axis=1)  # Hermitian mirror like the RTL
    assert gain_full.shape == A.shape, (gain_full.shape, A.shape)
    Yq = np.clip(np.round(A * gain_full * 64.0), -(1 << 31), (1 << 31) - 1)
    np.save(os.path.join(OUT, "A_ref.npy"), A)
    np.save(os.path.join(OUT, "Yq.npy"), Yq)
    # inverse reference: y = sum Y e^{+i} = N * ifft(Y)  (real)
    inv_ref = (NFFT * np.fft.ifft(Yq.astype(np.float64), axis=1)).real
    np.save(os.path.join(OUT, "inv_ref.npy"), inv_ref)

    with open(os.path.join(OUT, "Y_in.hex"), "w") as f:
        for t in range(nsim):
            for k in range(NFFT):
                re = int(Yq[t, k].real) & 0xFFFFFFFF
                im = int(Yq[t, k].imag) & 0xFFFFFFFF
                f.write(f"{im & 0xFFFFFFFF:08x}{re & 0xFFFFFFFF:08x}\n")

    meta = {"n": n, "frames": frames, "nsim": nsim,
            "gain_min": float(gain.min()), "gain_max": float(gain.max()),
            "recompute_max_err": float(err.max()),
            "recompute_corr": float(np.corrcoef(out, y16)[0, 1])}
    with open(os.path.join(OUT, "ref_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()




