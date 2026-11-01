"""Compare two raw float32 mono signals: correlation, SNR, max abs diff.

Usage: compare_f32.py A.f32 B.f32 [--json out.json]
SNR is computed on the common length after removing the mean (DC) of each,
which is the convention used in board_c_20261025.md 8.2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def stats(a: np.ndarray, b: np.ndarray) -> dict:
    n = min(len(a), len(b))
    a = a[:n].astype(np.float64)
    b = b[:n].astype(np.float64)
    a = a - a.mean()
    b = b - b.mean()
    err = a - b
    sig = float(np.sum(a * a))
    noise = float(np.sum(err * err))
    snr = 10.0 * np.log10(sig / noise) if noise > 0 else float("inf")
    corr = float(np.corrcoef(a, b)[0, 1]) if n > 1 else float("nan")
    return {
        "n": int(n),
        "corr": round(corr, 9),
        "snr_db": round(float(snr), 3),
        "max_abs_diff": float(np.max(np.abs(err))),
        "rms_a": float(np.sqrt(np.mean(a * a))),
        "rms_b": float(np.sqrt(np.mean(b * b))),
        "peak_a": float(np.max(np.abs(a))),
        "peak_b": float(np.max(np.abs(b))),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--label-a", default="a")
    ap.add_argument("--label-b", default="b")
    args = ap.parse_args()
    a = np.fromfile(args.a, dtype="<f4")
    b = np.fromfile(args.b, dtype="<f4")
    s = stats(a, b)
    s["label_a"] = args.label_a
    s["label_b"] = args.label_b
    print(json.dumps(s, indent=2))
    if args.json:
        args.json.write_text(json.dumps(s, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
