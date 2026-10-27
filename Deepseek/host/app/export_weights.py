"""Export models/student_v5.pt to the flat little-endian blob read by vc_stream.

The blob deliberately contains everything the board needs, including the two DCT
matrices and the inverse-DCT synthesis matrix, so the runtime never has to
recompute a pinv (no LAPACK on the board).

Layout (all little-endian)
--------------------------
    char    magic[4]              "VCB1"
    int32   version               1
    int32   in_dim                646
    int32   hidden                512
    int32   layers                4
    int32   out_dim               48 (student_v5/T4) or 64 (O64); from the ckpt
    int32   context               4
    int32   nceps_in              32
    int32   nceps_out             = out_dim
    int32   n_bins                513
    int32   fft_size              1024
    int32   frame_period_x10      100      (10.0 ms)
    int32   sample_rate           16000
    float32 pitch_ratio           1.4
    float32 mu[in_dim]
    float32 sd[in_dim]
    float32 dct_in[nceps_in][n_bins]
    float32 dct_out[nceps_out][n_bins]
    float32 synth[nceps_out][n_bins]       (= pinv(dct_out).T, i.e. pred = ceps @ synth)
    float32 pitch_shift_ratio     1.4      (runtime duplicate, keeps the header self-describing)
    per layer l in 0..layers-1:
        float32 W_l[hidden][in_l]  (row j = weights of output neuron j)
        float32 b_l[hidden]
    float32 W_out[out_dim][hidden]
    float32 b_out[out_dim]

Run:  python export_weights.py [--ckpt ...] [--out ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
NBINS = 513
PITCH_RATIO = 1.4


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=str(ROOT / "models" / "student_v5.pt"))
    ap.add_argument("--out", default=str(HERE / "data" / "student_v5.blob"))
    args = ap.parse_args()

    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    state = ck["state"]
    in_dim = int(ck["in_dim"])
    hidden = int(ck["hidden"])
    layers = int(ck["layers"])
    out_dim = int(ck["nceps_out"])
    nceps_out = out_dim
    context = int(ck["context"])
    nceps_in = int(ck["nceps_in"])
    dct_in = np.asarray(ck["dct_in"], dtype=np.float32)
    dct_out = np.asarray(ck["dct_out"], dtype=np.float32)
    assert dct_in.shape == (nceps_in, NBINS), dct_in.shape
    assert dct_out.shape == (out_dim, NBINS), dct_out.shape

    # Exactly the matrix used by the Python reference:
    #   logsp_pred = ceps @ np.linalg.pinv(dct_out).T
    synth = np.linalg.pinv(dct_out.astype(np.float64)).T.astype(np.float32)
    assert synth.shape == (out_dim, NBINS)

    # Linear layers live at body.0 / body.3 / body.6 / body.9 (Linear, GELU, Dropout)
    ws, bs = [], []
    for l in range(layers):
        ws.append(state[f"body.{3 * l}.weight"].detach().cpu().numpy().astype(np.float32))
        bs.append(state[f"body.{3 * l}.bias"].detach().cpu().numpy().astype(np.float32))
    assert ws[0].shape == (hidden, in_dim), ws[0].shape
    for l in range(1, layers):
        assert ws[l].shape == (hidden, hidden), ws[l].shape
    w_out = state["out.weight"].detach().cpu().numpy().astype(np.float32)
    b_out = state["out.bias"].detach().cpu().numpy().astype(np.float32)
    assert w_out.shape == (out_dim, hidden), w_out.shape

    mu = np.asarray(ck["mu"], dtype=np.float32)
    sd = np.asarray(ck["sd"], dtype=np.float32)
    assert mu.shape == (in_dim,) and sd.shape == (in_dim,)

    chunks = []
    chunks.append(b"VCB1")
    chunks.append(struct.pack("<12i", 1, in_dim, hidden, layers, out_dim, context,
                              nceps_in, nceps_out, NBINS, 1024, 100, 16000))
    chunks.append(struct.pack("<f", float(PITCH_RATIO)))
    for a in (mu, sd, dct_in, dct_out, synth):
        chunks.append(a.astype("<f4").tobytes())
    chunks.append(struct.pack("<f", float(PITCH_RATIO)))
    for l in range(layers):
        chunks.append(ws[l].astype("<f4").tobytes())
        chunks.append(bs[l].astype("<f4").tobytes())
    chunks.append(w_out.astype("<f4").tobytes())
    chunks.append(b_out.astype("<f4").tobytes())

    blob = b"".join(chunks)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)

    expected = (4 + 48 + 4 + 4 * (in_dim * 2 + nceps_in * NBINS + out_dim * NBINS * 2 + 1)
                + 4 * (sum(w.size + b.size for w, b in zip(ws, bs)) + w_out.size + b_out.size))
    assert len(blob) == expected, (len(blob), expected)

    meta = {
        "ckpt": str(Path(args.ckpt).relative_to(ROOT).as_posix()),
        "blob": out.name,
        "bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "in_dim": in_dim, "hidden": hidden, "layers": layers,
        "out_dim": out_dim, "context": context,
        "nceps_in": nceps_in, "n_bins": NBINS, "pitch_ratio": PITCH_RATIO,
        "params": int(sum(w.size + b.size for w, b in zip(ws, bs)) + w_out.size + b_out.size),
        "synth_is_pinv_transpose": True,
        "note": "synth rows are orthonormal (dct_out @ dct_out.T == I), so synth ~= dct_out; "
                "the exact pinv is stored anyway to remove any doubt about the inverse DCT.",
        "dct_out_orthonormality_maxerr": float(np.abs(dct_out @ dct_out.T - np.eye(out_dim)).max()),
        "synth_vs_dct_out_maxerr": float(np.abs(synth - dct_out).max()),
    }
    (out.with_suffix(".json")).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
