"""Evaluate full heldout-source causal-bottleneck waveforms with current metrics."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(str(ROOT / "build/generated/llvc_cpu_deps/torch/lib"))
    os.add_dll_directory(r"D:\Anaconda\Library\bin")
for dependency in ("eval_deps_20261016", "world_deps", "llvc_cpu_deps",
                   "seed_audio_deps", "seed_cpu_deps"):
    sys.path.insert(0, str(ROOT / "build/generated" / dependency))
sys.path.insert(0, str(ROOT / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import audit_seed_reference_20261016 as audit  # noqa: E402
from evaluate_fargan_target_oracle import script_normalized_cer  # noqa: E402

INFERENCE = (ROOT / "build/generated/quality_exploration_20261018/"
             "causal_bottleneck_heldout/manifest.json")
SOURCE_AUDIO = ROOT / "交接/核心材料/board_budget_20261005/student_corpus/audio"


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right)))


def main() -> None:
    manifest = json.loads(INFERENCE.read_text(encoding="utf-8"))
    if manifest.get("speaker_or_quality_metrics_run"):
        raise ValueError("Inference manifest unexpectedly claims prior quality evaluation")
    evaluators = audit.Evaluators()
    target_vectors = []
    for number in range(5, 9):
        target = audit.load16(ROOT / f"voice_src/src_1/Track {number}(1).wav")
        target_vectors.append(evaluators.wespeaker(target)[0])
    target_centroid = np.mean(np.stack(target_vectors), axis=0)
    target_centroid /= np.linalg.norm(target_centroid)

    rows = []
    for output in manifest["outputs"]:
        source_path = SOURCE_AUDIO / f"{output['filename']}.wav"
        candidate_path = ROOT / output["wav"]
        source = audit.load16(source_path)
        candidate = audit.load16(candidate_path)
        source_vector = evaluators.wespeaker(source)[0]
        candidate_vector = evaluators.wespeaker(candidate)[0]
        source_text = evaluators.transcribe(source)
        candidate_text = evaluators.transcribe(candidate)
        rows.append({
            "filename": output["filename"],
            "speaker": output["speaker"],
            "seconds": len(candidate) / 16000,
            "identity_to_target_centroid": cosine(candidate_vector, target_centroid),
            "source_leakage_cosine": cosine(candidate_vector, source_vector),
            "utmos_predicted": evaluators.naturalness(candidate),
            "source_asr": source_text,
            "candidate_asr": candidate_text,
            "content_cer_raw": audit.cer(source_text, candidate_text),
            "content_cer_script_normalized": script_normalized_cer(source_text, candidate_text),
        })

    identity = np.asarray([row["identity_to_target_centroid"] for row in rows])
    leakage = np.asarray([row["source_leakage_cosine"] for row in rows])
    utmos = np.asarray([row["utmos_predicted"] for row in rows])
    cer = np.asarray([row["content_cer_script_normalized"]["cer"] for row in rows])
    summary = {
        "utterances": len(rows),
        "heldout_speakers": sorted({row["speaker"] for row in rows}),
        "identity_mean": float(identity.mean()),
        "identity_p10": float(np.percentile(identity, 10)),
        "identity_min": float(identity.min()),
        "source_leakage_mean": float(leakage.mean()),
        "source_leakage_p90": float(np.percentile(leakage, 90)),
        "source_leakage_max": float(leakage.max()),
        "utmos_mean": float(utmos.mean()),
        "utmos_min": float(utmos.min()),
        "cer_mean": float(cer.mean()),
        "cer_p90": float(np.percentile(cer, 90)),
        "cer_max": float(cer.max()),
    }
    gates = {
        "identity_mean_at_least_0_45": summary["identity_mean"] >= 0.45,
        "identity_p10_at_least_0_35": summary["identity_p10"] >= 0.35,
        "source_leakage_mean_at_most_0_10": summary["source_leakage_mean"] <= 0.10,
        "utmos_mean_at_least_2_3": summary["utmos_mean"] >= 2.3,
        "cer_mean_at_most_0_15": summary["cer_mean"] <= 0.15,
        "cer_degradation_at_most_0_05": summary["cer_mean"] <= 0.05,
    }
    record = {
        "kind": "causal_content_bottleneck_heldout_objective_evaluation",
        "date": "2026-10-18",
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "protocol": "current WeSpeaker centroid + UTMOS22 strong + offline whisper-small",
        "rows": rows,
        "summary": summary,
        "gates": gates,
        "all_objective_gates_pass": all(gates.values()),
        "board_touched": False,
        "audio_played": False,
        "limitations": [
            "The teacher and model are fixed-target; unseen-target registration is not tested.",
            "The heldout set has two source speakers and eight utterances.",
            "CER uses source ASR as its reference and explicit observed-character script normalization.",
            "Objective metrics do not replace a later blind listening gate.",
        ],
    }
    destination = ROOT / "report/quality_exploration_causal_bottleneck_metrics_20261018.json"
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "gates": gates,
                      "all_objective_gates_pass": record["all_objective_gates_pass"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
