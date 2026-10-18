"""Evaluate mapper-free Track5-8 FARGAN reconstructions with the current protocol."""
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
import audit_seed_reference_20261016 as audit  # noqa: E402
import numpy as np  # noqa: E402

OUTPUT = ROOT / "build/generated/quality_exploration_20261018/fargan_target_oracle"

# Whisper can emit one utterance in Traditional Chinese and the reconstruction
# in Simplified Chinese.  CER must not count script conversion as audio damage.
# This explicit table covers the characters observed in Track5-8 transcripts.
SCRIPT_MAP = str.maketrans({
    "來": "来", "樹": "树", "換": "换", "黃": "黄", "風": "风", "葉": "叶",
    "飛": "飞", "裡": "里", "蘋": "苹", "臉": "脸", "掛": "挂", "齊": "齐",
    "燈": "灯", "籠": "笼", "彎": "弯", "處": "处", "豐": "丰", "氣": "气",
    "週": "周", "學": "学", "騎": "骑", "車": "车", "開": "开", "總": "总",
    "搖": "摇", "幾": "几", "點": "点", "棄": "弃", "勵": "励", "訴": "诉",
    "調": "调", "勢": "势", "斷": "断", "練": "练", "習": "习", "終": "终",
    "於": "于", "獨": "独", "這": "这", "讓": "让", "堅": "坚", "會": "会",
    "難": "难", "輕": "轻", "認": "认", "輸": "输", "貓": "猫", "長": "长",
    "著": "着", "對": "对", "圓": "圆", "鏡": "镜", "兩": "两", "顆": "颗",
    "別": "别", "歡": "欢", "線": "线", "飯": "饭", "時": "时", "覺": "觉",
    "團": "团", "軟": "软", "當": "当", "過": "过", "愛": "爱", "夥": "伙",
})


def script_normalized_cer(reference: str, hypothesis: str) -> dict:
    return audit.cer(reference.translate(SCRIPT_MAP), hypothesis.translate(SCRIPT_MAP))


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right)))


def main() -> None:
    evaluators = audit.Evaluators()
    originals = {}
    original_vectors = {}
    for index in range(5, 9):
        audio = audit.load16(ROOT / f"voice_src/src_1/Track {index}(1).wav")
        originals[index] = audio
        original_vectors[index] = evaluators.wespeaker(audio)[0]
    centroid = np.mean(np.stack(list(original_vectors.values())), axis=0)
    centroid /= np.linalg.norm(centroid)

    rows = []
    for index in range(5, 9):
        original = originals[index]
        reconstructed = audit.load16(OUTPUT / f"target_track{index}_fargan_oracle.wav")
        vector = evaluators.wespeaker(reconstructed)[0]
        original_text = evaluators.transcribe(original)
        reconstructed_text = evaluators.transcribe(reconstructed)
        content = audit.cer(original_text, reconstructed_text)
        normalized_content = script_normalized_cer(original_text, reconstructed_text)
        rows.append({
            "track": index,
            "seconds_original": len(original) / 16000,
            "seconds_reconstructed": len(reconstructed) / 16000,
            "identity_to_target_centroid_original": cosine(original_vectors[index], centroid),
            "identity_to_target_centroid_reconstructed": cosine(vector, centroid),
            "identity_to_same_track_original": cosine(vector, original_vectors[index]),
            "utmos_original": evaluators.naturalness(original),
            "utmos_reconstructed": evaluators.naturalness(reconstructed),
            "asr_original": original_text,
            "asr_reconstructed": reconstructed_text,
            "reconstruction_cer_relative_to_original_asr": content,
            "reconstruction_cer_script_normalized": normalized_content,
        })

    identity = [row["identity_to_target_centroid_reconstructed"] for row in rows]
    self_identity = [row["identity_to_same_track_original"] for row in rows]
    utmos = [row["utmos_reconstructed"] for row in rows]
    utmos_drop = [row["utmos_original"] - row["utmos_reconstructed"] for row in rows]
    raw_cer = [row["reconstruction_cer_relative_to_original_asr"]["cer"] for row in rows]
    cer = [row["reconstruction_cer_script_normalized"]["cer"] for row in rows]
    summary = {
        "identity_to_target_centroid_mean": float(np.mean(identity)),
        "identity_to_target_centroid_min": float(np.min(identity)),
        "identity_to_same_track_mean": float(np.mean(self_identity)),
        "identity_to_same_track_min": float(np.min(self_identity)),
        "utmos_reconstructed_mean": float(np.mean(utmos)),
        "utmos_reconstructed_min": float(np.min(utmos)),
        "utmos_drop_from_original_mean": float(np.mean(utmos_drop)),
        "cer_relative_to_original_asr_raw_mean": float(np.mean(raw_cer)),
        "cer_script_normalized_mean": float(np.mean(cer)),
        "cer_script_normalized_max": float(np.max(cer)),
    }
    gates = {
        "identity_mean_at_least_0_75": summary["identity_to_target_centroid_mean"] >= 0.75,
        "utmos_mean_at_least_2_6": summary["utmos_reconstructed_mean"] >= 2.6,
        "cer_mean_at_most_0_05": summary["cer_script_normalized_mean"] <= 0.05,
    }
    record = {
        "kind": "mapper_independent_fargan_target_oracle_evaluation",
        "date": "2026-10-18",
        "protocol": "current WeSpeaker centroid + UTMOS22 strong + offline whisper-small",
        "rows": rows,
        "summary": summary,
        "gates": gates,
        "oracle_pass": all(gates.values()),
        "board_touched": False,
        "audio_played": False,
        "limitations": [
            "ASR preservation is measured against the original recording's ASR transcript, not a human transcript.",
            "CER applies an explicit Traditional-to-Simplified map covering observed Track5-8 characters; raw CER is retained.",
            "The four recordings belong to one target speaker and do not test target registration or source conversion.",
            "Objective scores do not replace a later listening gate.",
        ],
    }
    destination = ROOT / "report/quality_exploration_fargan_target_oracle_metrics_20261018.json"
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
