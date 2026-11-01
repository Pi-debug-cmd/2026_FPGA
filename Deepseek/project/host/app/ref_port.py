"""Python oracle for the board C port: run the exact reference chain and dump
every intermediate stage as float32 so the C implementation can be compared
stage by stage.

Fidelity policy: the feature / statistics / model code is *imported* from the
real training scripts (no re-implementation), and `analyse` is copied verbatim
from scripts/synth_eval.py.  The STFT/ISTFT transplant block (frame_rms,
smooth_mask, to_stft_grid, transplant) is copied verbatim out of
scripts/stft_env_20261024.py -- importing that module would drag in
scripts/evaluator.py (and its UTMOS dependencies) for no benefit.

Usage
-----
    ref_port.py --wav data/pair16k/male/male_04.wav --out-dir out/ref_male04
    ref_port.py --in-f32 dump/x16.f32 --out-dir out/ref_x16 --nopitch

`--in-f32` accepts the float32 mono 16 kHz signal dumped by vc_stream --dump-dir,
which is how the C/Python comparison is made free of any resampler difference.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from train_student import frame_features, stack_context  # noqa: E402
from train_v5 import EnvNet5, utterance_stats  # noqa: E402

import pyworld as pw  # noqa: E402
import librosa  # noqa: E402

SR = 16000
NFFT = 1024
WIN = 1024
HOP = 160
SILENCE_DB = -45.0
NBINS = 513


# ---------------------------------------------------------------- analysis
def analyse(x: np.ndarray, frame: float = 10.0, fft: int = 1024):
    """Verbatim copy of scripts/synth_eval.py:analyse."""
    x = np.ascontiguousarray(x, dtype=np.float64)
    f0, t = pw.dio(x, 16000, f0_floor=75.0, f0_ceil=400.0, frame_period=frame, speed=4)
    f0 = pw.stonemask(x, f0, t, 16000)
    sp = pw.cheaptrick(x, f0, t, 16000, fft_size=fft, f0_floor=75.0)
    ap = pw.d4c(x, f0, t, 16000, fft_size=fft)
    return f0, np.log(np.maximum(sp, 1e-16)), ap


# ---------------------------------------------------------------- grid utils
def to_stft_grid(A: np.ndarray, n_frames: int) -> np.ndarray:
    """Verbatim copy of scripts/stft_env_20261024.py:to_stft_grid."""
    n = A.shape[0]
    if n == n_frames:
        return A.astype(np.float64)
    pos = np.linspace(0.0, n - 1.0, n_frames)
    lo = np.floor(pos).astype(int)
    hi = np.minimum(lo + 1, n - 1)
    w = (pos - lo)[:, None]
    return A[lo] * (1.0 - w) + A[hi] * w


def frame_rms(x: np.ndarray, n_frames: int) -> np.ndarray:
    """Verbatim copy of scripts/stft_env_20261024.py:frame_rms."""
    pad = WIN // 2
    xp = np.pad(x, (pad, pad), mode="constant")
    c = np.concatenate([[0.0], np.cumsum(xp * xp)])
    lo = np.arange(n_frames) * HOP
    hi = lo + WIN
    hi[-1] = min(hi[-1], len(xp))
    return np.sqrt(np.maximum((c[hi] - c[lo]) / WIN, 0.0))


def smooth_mask(m: np.ndarray) -> np.ndarray:
    """Verbatim copy of scripts/stft_env_20261024.py:smooth_mask."""
    w = np.convolve(m.astype(np.float64), np.array([0.25, 0.5, 0.25]), mode="same")
    return np.clip(w, 0.0, 1.0)


# ---------------------------------------------------------------- prediction
def predict(ck, x):
    f0, logsp, ap = analyse(x)
    d = {"logsp": logsp.astype(np.float32), "f0": f0.astype(np.float32),
         "ap": ap.astype(np.float32)}
    feats, _ceps, aux = frame_features(d)
    st = utterance_stats(d, ck["dct_in"])
    X = np.concatenate([stack_context(feats, ck["context"]),
                        np.tile(st[None, :], (len(feats), 1))], axis=1)
    Xn = ((X - ck["mu"]) / ck["sd"]).astype(np.float32)
    model = EnvNet5(ck["in_dim"], ck["hidden"], ck["layers"], out_dim=ck["nceps_out"])
    model.load_state_dict(ck["state"])
    model.eval()
    with torch.no_grad():
        res = model(torch.from_numpy(Xn)).numpy()
    ceps = (logsp.astype(np.float64) @ ck["dct_out"].T) + res
    logsp_pred = ceps @ np.linalg.pinv(ck["dct_out"]).T
    return {"f0": f0, "logsp": logsp, "ap": ap, "feats": feats, "aux": aux,
            "stats": st, "X": X, "Xn": Xn, "res": res, "ceps": ceps,
            "logsp_pred": logsp_pred}


def transplant(x, logsp_pred, logsp_src, gain_limit_db=20.0, gain_exponent=0.5):
    """Verbatim copy of scripts/stft_env_20261024.py:transplant (stats trimmed)."""
    X = librosa.stft(x, n_fft=NFFT, hop_length=HOP, win_length=WIN,
                     window="hann", center=True, pad_mode="constant")
    n_frames = X.shape[1]
    src = to_stft_grid(logsp_src, n_frames)
    prd = to_stft_grid(logsp_pred, n_frames)
    diff_db = gain_exponent * (prd - src) * (20.0 / np.log(10.0))
    rms = frame_rms(x, n_frames)
    ref = float(np.percentile(rms, 95))
    silent = rms < max(1e-4, ref * 10.0 ** (SILENCE_DB / 20.0))
    w = smooth_mask(silent)
    clip_mask = np.abs(diff_db) > gain_limit_db
    diff_db = np.clip(diff_db, -gain_limit_db, gain_limit_db)
    log_gain = diff_db * (np.log(10.0) / 20.0)
    log_gain *= (1.0 - w)[:, None]
    p = (X.real ** 2 + X.imag ** 2)
    stats = {
        "frames": int(n_frames),
        "silent_frames_frac": round(float(silent.mean()), 4),
        "gain_clipped_frac": round(float(clip_mask.mean()), 4),
        "median_gain_db": round(float(np.median(diff_db[~silent])), 3) if (~silent).any() else 0.0,
        "peak_out": float(np.max(np.abs(librosa.istft(X * np.exp(log_gain.T), hop_length=HOP,
                                                      win_length=WIN, window="hann",
                                                      center=True, length=len(x))))),
    }
    Y = X * np.exp(log_gain.T)
    y = librosa.istft(Y, hop_length=HOP, win_length=WIN, window="hann",
                      center=True, length=len(x))
    recon = librosa.istft(X, hop_length=HOP, win_length=WIN, window="hann",
                          center=True, length=len(x))
    stats["istft_roundtrip_maxerr"] = float(np.max(np.abs(recon - x)))
    return y, dict(stats=stats, log_gain=log_gain, rms=rms, silent=silent,
                   mask=w, diff_db=diff_db, X=X)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=str(ROOT / "models" / "student_v5.pt"))
    ap.add_argument("--wav", default=None)
    ap.add_argument("--in-f32", default=None, help="raw float32 mono 16 kHz (C dump)")
    ap.add_argument("--xB-f32", default=None,
                    help="use this raw float32 16 kHz signal as the pitch-shifted source "
                         "(the C build's SoundTouch output); the prediction is still made "
                         "from --in-f32/--wav, exactly like the B path")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pitch", type=float, default=1.4)
    ap.add_argument("--nopitch", action="store_true")
    ap.add_argument("--pitch-impl", default="librosa", choices=["librosa"],
                    help="the board uses SoundTouch WSOLA; librosa's phase vocoder is "
                         "the only Python-side reference available")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if args.in_f32:
        x = np.fromfile(args.in_f32, dtype="<f4").astype(np.float64)
        src_name = args.in_f32
    else:
        x, sr = __import__("soundfile").read(args.wav, dtype="float64", always_2d=False)
        if x.ndim == 2:
            x = x.mean(axis=1)
        assert sr == SR, f"expected 16 kHz, got {sr}"
        src_name = args.wav
    x = np.ascontiguousarray(x, dtype=np.float64)
    n = len(x)

    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    P = predict(ck, x)

    if args.xB_f32:
        # SoundTouch output from the C build: keeps the pitch algorithm out of the
        # comparison, everything else is still the reference code.
        xB = np.fromfile(args.xB_f32, dtype="<f4").astype(np.float64)
        if len(xB) < n:
            xB = np.pad(xB, (0, n - len(xB)))
        xB = xB[:n]
        f0b, logsp_b, apb = analyse(xB)
        n_steps = 12.0 * np.log2(args.pitch)
        pitch_impl = "soundtouch-from-c"
    elif args.nopitch:
        xB = x.copy()
        f0b, logsp_b, apb = P["f0"], P["logsp"], P["ap"]
        n_steps = 0.0
        pitch_impl = None
    else:
        n_steps = 12.0 * np.log2(args.pitch)
        xB = librosa.effects.pitch_shift(x, sr=SR, n_steps=n_steps, res_type="soxr_hq")
        if len(xB) != n:
            xB = np.pad(xB, (0, max(0, n - len(xB))))[:n]
        f0b, logsp_b, apb = analyse(xB)
        pitch_impl = "librosa"

    y, T = transplant(xB, P["logsp_pred"], logsp_b)
    y = np.pad(y, (0, max(0, n - len(y))))[:n]

    np.savez_compressed(
        out / "stages.npz",
        x=x.astype(np.float32), xB=xB.astype(np.float32), y=y.astype(np.float32),
        f0=P["f0"].astype(np.float32), logsp=P["logsp"].astype(np.float32),
        ap=P["ap"].astype(np.float32), feats=P["feats"].astype(np.float32),
        stats=P["stats"].astype(np.float32), X=P["X"].astype(np.float32),
        Xn=P["Xn"].astype(np.float32), res=P["res"].astype(np.float32),
        ceps=P["ceps"].astype(np.float32), logsp_pred=P["logsp_pred"].astype(np.float32),
        f0b=f0b.astype(np.float32), logsp_b=logsp_b.astype(np.float32),
        diff_db=T["diff_db"].astype(np.float32), mask=T["mask"].astype(np.float32),
        rms=T["rms"].astype(np.float32), silent=T["silent"],
        Xstft=np.abs(T["X"]).astype(np.float32),
    )
    y.astype("<f4").tofile(out / "y16.f32")

    vu = P["f0"] > 0
    summary = {
        "input": src_name,
        "samples": int(n),
        "seconds": round(n / SR, 4),
        "world_frames": int(len(P["f0"])),
        "voiced_frac": round(float(vu.mean()), 4),
        "median_f0_hz": round(float(np.median(P["f0"][vu])), 3) if vu.any() else 0.0,
        "pitch": None if args.nopitch else args.pitch,
        "pitch_impl": pitch_impl,
        "semitone": round(float(n_steps), 4),
        "median_f0_after_shift_hz": round(float(np.median(f0b[f0b > 0])), 3) if (f0b > 0).any() else 0.0,
        "transplant": T["stats"],
        "peak_y": float(np.max(np.abs(y))),
        "rms_y": float(np.sqrt(np.mean(y ** 2))),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
