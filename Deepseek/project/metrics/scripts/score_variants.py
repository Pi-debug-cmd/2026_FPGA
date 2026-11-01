"""Score several vc_stream variants in one process (loads the Evaluator once).

The four-metric evaluator is expensive to spin up (WeSpeaker ONNX + UTMOS +
centroids), so this reuses one instance for all variants and reports the same
numbers score_full.py does (identity/leakage/utmos), without CER.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluator import Evaluator, load16  # noqa: E402

FEMALE_LEAK_BASELINE = 0.2073


def windows(x, win_s=4.0, hop_s=2.0):
    win, hop = int(win_s * 16000), int(hop_s * 16000)
    for s in range(0, max(len(x) - win + 1, 1), hop):
        c = x[s:s + win]
        if len(c) < 16000 or float(np.sqrt(np.mean(c * c))) < 1e-3:
            continue
        yield c


def main() -> None:
    files = [Path(p) for p in sys.argv[1:]]
    man = json.loads((ROOT / "data/pair16k/manifest.json").read_text(encoding="utf-8"))
    fw = [ROOT / e["wav"] for e in man["files"] if e["speaker"] == "female" and e["split"] == "train"]
    mw = [ROOT / e["wav"] for e in man["files"] if e["speaker"] == "male" and e["split"] == "train"]

    ev = Evaluator()
    fcent = ev.centroid(fw)
    mcent = ev.centroid(mw)

    rows = []
    for p in files:
        x = load16(p)
        emb = ev.embed(x)
        vals = [float(ev.embed_clip(c) @ fcent) for c in windows(x)]
        leaks = [float(ev.embed_clip(c) @ mcent) for c in windows(x)]
        rec = {
            "label": p.stem,
            "identity_file": round(float(emb @ fcent), 4),
            "identity_mean": round(float(np.mean(vals)), 4) if vals else None,
            "windows": len(vals),
            "leakage_file": round(float(emb @ mcent), 4),
            "leakage_strict": round(max(float(np.mean(leaks)) if leaks else 0.0,
                                        float(emb @ mcent)), 4),
            "utmos": round(float(ev.utmos_score(x)), 4),
        }
        rec["leakage_rel"] = round(rec["leakage_strict"] - FEMALE_LEAK_BASELINE, 4)
        rows.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
    Path("out/score/variants.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
