"""Five-gate scoring on the fixed male->female pair.

Gates (see plan.md):
  identity  >= 0.45  mean, >= 0.35 P10   (WeSpeaker CN-Celeb ResNet34 vs female centroid)
  leakage   <= 0.10                       (cosine vs male centroid)
  utmos     >= 2.30                       (UTMOS22-Strong)
  cer       <= 0.15                       (whisper-small, vs the male source transcript)

P10 is computed over 4 s windows with a 2 s hop: windows quieter than -60 dBFS
are skipped. Whole-file embedding is reported separately as `identity_file`,
because a single utterance-level vector hides window-level failures.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluator import Evaluator, cer, load16  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SR = 16000
PUNCT = set("，。！？、；：""''（）《》…—·,.!?;:\"'()<>[]{}~`")

# --- calibrated baselines, measured 2026-10-24 (see reports/EVAL_FINDINGS_20261024.md)
# The raw cosine-to-male-centroid is dominated by recording/channel domain, so the
# absolute values are meaningless: the TARGET FEMALE HERSELF scores 0.186..0.230.
# Leakage is therefore reported relative to that reference (<=0 means "at least as
# female-sounding as the real target"). Same idea for CER, whose reference text is
# itself a whisper transcription of the male source.
FEMALE_LEAK_BASELINE = 0.2073   # mean strict leakage of the 5 target-female files
TEACHER_CER_BASELINE = 0.1875   # Seed-VC teacher CER on the locked utterance (male_04)
GATES = {"identity_mean": 0.45, "identity_p10": 0.35,
         "leakage_rel": 0.0, "utmos": 2.30, "cer_rel": 0.0}


def windows(x: np.ndarray, win_s: float = 4.0, hop_s: float = 2.0):
    win, hop = int(win_s * SR), int(hop_s * SR)
    for s in range(0, max(len(x) - win + 1, 1), hop):
        c = x[s:s + win]
        if len(c) < SR or float(np.sqrt(np.mean(c * c))) < 1e-3:
            continue
        yield c


def clean(t: str) -> str:
    return "".join(c for c in t if not c.isspace() and c not in PUNCT)


def score(ev: Evaluator, wav: Path, fcent, mcent, ref_text: str | None) -> dict:
    x = load16(wav)
    file_emb = ev.embed(x)
    vals = [float(ev.embed_clip(c) @ fcent) for c in windows(x)]
    rec = {
        "wav": wav.name,
        "seconds": round(len(x) / SR, 2),
        "identity_file": round(float(file_emb @ fcent), 4),
        "identity_mean": round(float(np.mean(vals)), 4) if vals else None,
        "identity_p10": round(float(np.percentile(vals, 10)), 4) if vals else None,
        "windows": len(vals),
        "leakage_file": round(float(file_emb @ mcent), 4),
        "utmos": round(float(ev.utmos_score(x)), 4),
    }
    leaks = [float(ev.embed_clip(c) @ mcent) for c in windows(x)]
    rec["leakage_mean"] = round(float(np.mean(leaks)), 4) if leaks else None
    # the strict rule the repo uses: take the larger of windowed mean and file value
    rec["leakage_strict"] = round(max(rec["leakage_mean"] or 0.0, rec["leakage_file"]), 4)
    if ref_text is not None:
        hyp = ev.transcribe(x)
        rec["cer"] = round(float(cer(ref_text, clean(hyp))), 4)
        rec["hyp"] = hyp
    return with_gates(rec)


def with_gates(rec: dict) -> dict:
    """Add the calibrated metrics and a pass/fail verdict per gate."""
    rec["leakage_rel"] = round(rec["leakage_strict"] - FEMALE_LEAK_BASELINE, 4)
    rec["margin"] = round((rec["identity_mean"] or 0.0) - rec["leakage_strict"], 4)
    if "cer" in rec:
        rec["cer_rel"] = round(rec["cer"] - TEACHER_CER_BASELINE, 4)
    gate = {}
    for k, limit in GATES.items():
        if k not in rec or rec[k] is None:
            gate[k] = "n/a"
        elif k == "leakage_rel" or k == "cer_rel":
            gate[k] = "pass" if rec[k] <= limit else "fail"
        else:
            gate[k] = "pass" if rec[k] >= limit else "fail"
    rec["gate"] = gate
    rec["all_pass"] = all(v == "pass" for v in gate.values() if v != "n/a")
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wav", nargs="+", type=Path)
    ap.add_argument("--label", nargs="*", default=None)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--cer-from", type=Path, default=None,
                    help="speech to transcribe once and use as CER reference "
                         "(usually the male source wav); omit to skip CER")
    args = ap.parse_args()

    man = json.loads((ROOT / "data" / "pair16k" / "manifest.json").read_text(encoding="utf-8"))
    fw = [ROOT / e["wav"] for e in man["files"] if e["speaker"] == "female" and e["split"] == "train"]
    mw = [ROOT / e["wav"] for e in man["files"] if e["speaker"] == "male" and e["split"] == "train"]

    ev = Evaluator()
    fcent = ev.centroid(fw)
    mcent = ev.centroid(mw)

    ref_text = None
    if args.cer_from is not None:
        ref_text = clean(ev.transcribe(load16(args.cer_from)))
        print(f"CER reference ({args.cer_from.name}): {ref_text}", flush=True)

    rows = []
    for i, w in enumerate(args.wav):
        label = args.label[i] if args.label and i < len(args.label) else w.stem
        rec = score(ev, w, fcent, mcent, ref_text)
        rec["label"] = label
        rows.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print("->", args.json, flush=True)


if __name__ == "__main__":
    main()
