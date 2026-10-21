"""Objective screen for the LLVC-content to FARGAN PS candidate."""
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

OUT = ROOT / "build/generated/quality_exploration_20261019/llvc_content_fargan_v1"
SOURCE = ROOT / "交接/核心材料/board_budget_20261005/student_corpus_expanded/audio"


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right)))


def main() -> None:
    training = json.loads((OUT / "training_report.json").read_text(encoding="utf-8"))
    evaluators = audit.Evaluators()
    target_vectors = []
    for number in range(5, 9):
        target = audit.load16(ROOT / f"voice_src/src_1/Track {number}(1).wav")
        target_vectors.append(evaluators.wespeaker(target)[0])
    centroid = np.mean(np.stack(target_vectors), axis=0)
    centroid /= np.linalg.norm(centroid)

    rows = []
    for output in training["outputs"]:
        source = audit.load16(SOURCE / output["file"])
        source_vector = evaluators.wespeaker(source)[0]
        source_text = evaluators.transcribe(source)
        row = {"file": output["file"], "speaker": output["speaker"],
               "source_asr": source_text}
        for kind in ("candidate", "teacher_oracle"):
            wave = audit.load16(ROOT / output[kind])
            vector = evaluators.wespeaker(wave)[0]
            text = evaluators.transcribe(wave)
            row[kind] = {
                "seconds": len(wave) / 16000,
                "identity_to_target_centroid": cosine(vector, centroid),
                "source_leakage_cosine": cosine(vector, source_vector),
                "utmos_predicted": evaluators.naturalness(wave),
                "asr": text,
                "content_cer_script_normalized": script_normalized_cer(source_text, text),
            }
        rows.append(row)

    summaries = {}
    for kind in ("candidate", "teacher_oracle"):
        identity = np.asarray([row[kind]["identity_to_target_centroid"] for row in rows])
        leakage = np.asarray([row[kind]["source_leakage_cosine"] for row in rows])
        utmos = np.asarray([row[kind]["utmos_predicted"] for row in rows])
        cer = np.asarray([row[kind]["content_cer_script_normalized"]["cer"] for row in rows])
        summaries[kind] = {
            "identity_mean": float(identity.mean()),
            "identity_p10": float(np.percentile(identity, 10)),
            "source_leakage_mean": float(leakage.mean()),
            "utmos_mean": float(utmos.mean()),
            "utmos_min": float(utmos.min()),
            "cer_mean": float(cer.mean()),
            "cer_max": float(cer.max()),
        }
    summary = summaries["candidate"]
    gates = {
        "identity_mean_at_least_0_45": summary["identity_mean"] >= 0.45,
        "identity_p10_at_least_0_35": summary["identity_p10"] >= 0.35,
        "source_leakage_mean_at_most_0_10": summary["source_leakage_mean"] <= 0.10,
        "utmos_mean_at_least_2_3": summary["utmos_mean"] >= 2.3,
        "cer_mean_at_most_0_15": summary["cer_mean"] <= 0.15,
    }
    record = {
        "kind": "llvc_content_to_fargan_ps_candidate_v1_objective_screen",
        "date": "2026-10-19",
        "protocol": "current WeSpeaker centroid + UTMOS22 strong + offline whisper-small",
        "rows": rows,
        "summaries": summaries,
        "gates": gates,
        "all_objective_gates_pass": all(gates.values()),
        "board_touched": False,
        "audio_played": False,
        "limitations": [
            "This preliminary screen has four utterances from one speaker-disjoint validation speaker.",
            "The fixed target is known during training; live target registration is not implemented.",
            "Objective scores do not replace a later blind listening gate.",
        ],
    }
    destination = ROOT / "report/quality_exploration_llvc_content_fargan_v1_20261019.json"
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summaries": summaries, "gates": gates,
                      "all_objective_gates_pass": record["all_objective_gates_pass"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
