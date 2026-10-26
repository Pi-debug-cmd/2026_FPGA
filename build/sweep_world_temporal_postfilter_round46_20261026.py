"""Sweep one shared non-F0 temporal-contrast gain on frozen Round-37 validation rows."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import audit_source_prosody_round32_20261025 as prosody_audit  # noqa: E402
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import train_hubert_world_causal_gru_round23_20261025 as prior  # noqa: E402
import train_paired_hubert_world_gru_round26_20261025 as paired  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


GAINS = (1.0, 1.1, 1.2, 1.3, 1.4)
VUV_INDEX = prior.VUV_INDEX
NON_F0 = (slice(0, base.SP_DIM),
          slice(base.SP_DIM + 2, base.SP_DIM + 3),
          slice(base.SP_DIM + 3, base.OUTPUT_DIM))


def interpolate(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--generated-root", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)

    spec = importlib.util.spec_from_file_location(
        "round46_evaluator", args.asset_root / "build/audit_seed_reference_20261016.py")
    audit = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(audit)
    evaluator = audit.Evaluators()

    round25 = args.generated_root / "hubert_world_round25_20261025"
    manifest = json.loads((round25 / "cache_manifest.json").read_text(encoding="utf-8"))
    cache = round25 / "cache"
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if checkpoint["format"] != "paired_hubert_world_causal_gru_round37_variance_matching_v1":
        raise ValueError("Round46 requires the frozen Round37 checkpoint")
    model = paired.ProsodyCausalWorldGRU().eval()
    model.load_state_dict(checkpoint["model"])

    train_targets = [np.load(cache / row["cache"])["target"].astype(np.float32)
                     for row in manifest["records"] if row["split"] == "train"]
    pooled_y = np.concatenate(train_targets)
    clip_lo = np.percentile(pooled_y, 0.1, axis=0)
    clip_hi = np.percentile(pooled_y, 99.9, axis=0)
    voiced = pooled_y[:, VUV_INDEX] > 0.5
    anchor_world = [base.analyze_world(base.read_16k(
        args.asset_root / f"人物音频资料/女声/Track {number}.wav")) for number in (5, 6, 7, 8)]
    log_sp = np.log(np.maximum(np.concatenate([row["spectrum"] for row in anchor_world]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(pooled_y[voiced, base.SP_DIM], 0.5)),
             "log_f0_hi": float(np.percentile(pooled_y[voiced, base.SP_DIM], 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}

    corpus = args.asset_root / "交接/核心材料/board_budget_20261005/full_train_corpus_16k"
    declaration = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    declared = {row["stem"]: row for split in ("train", "validation")
                for row in declaration[split]}
    candidates = {gain: [] for gain in GAINS}
    for record in [row for row in manifest["records"] if row["split"] == "validation"]:
        data = np.load(cache / record["cache"])
        content = data["content"].astype(np.float32)
        x = (((content - checkpoint["pca_mean"]) @ checkpoint["pca_projection"]
              - checkpoint["x_mean"]) / checkpoint["x_std"]).astype(np.float32)
        declaration_row = declared[record["stem"]]
        source_path = prosody_audit.resolve(corpus, "src", declaration_row["src"])
        if base.sha256(source_path) != declaration_row["src_sha"]:
            raise ValueError(f"source SHA mismatch: {record['stem']}")
        source = prosody_audit.read_raw(source_path)
        source_prosody = prosody_audit.resample_rows(prosody_audit.source_prosody(source), len(x))
        x = np.concatenate((x, ((source_prosody - checkpoint["prosody_mean"])
                                / checkpoint["prosody_std"]).astype(np.float32)), axis=1)
        with torch.inference_mode():
            raw = model(torch.from_numpy(x[None]))[0].numpy()
        prediction = raw * checkpoint["y_std"] + checkpoint["y_mean"]
        probability = 1.0 / (1.0 + np.exp(-np.clip(raw[:, VUV_INDEX], -20.0, 20.0)))
        prediction = np.clip(prediction, clip_lo, clip_hi)
        prediction[:, VUV_INDEX] = probability
        frames5 = int(round(record["teacher_samples"] /
                            (base.SAMPLE_RATE * base.FRAME_PERIOD_MS / 1000))) + 1
        for gain in GAINS:
            filtered = prediction.copy()
            for group in NON_F0:
                center = np.mean(filtered[:, group], axis=0, keepdims=True)
                filtered[:, group] = center + gain * (filtered[:, group] - center)
            filtered = np.clip(filtered, clip_lo, clip_hi)
            filtered[:, VUV_INDEX] = probability
            features5 = interpolate(filtered, frames5)
            features5[:, VUV_INDEX] = (features5[:, VUV_INDEX] - 0.5) * 8.0
            waveform, synthesis = base.synthesize(features5, stats)
            path = args.output / f"{record['stem']}_gain{gain:.1f}.wav"
            base.sf.write(path, waveform, base.SAMPLE_RATE, subtype="PCM_16")
            candidates[gain].append({"stem": record["stem"], "speaker": record["speaker"],
                                     "utmos": evaluator.naturalness(waveform.astype(np.float64)),
                                     "sha256": base.sha256(path), "synthesis": synthesis})

    results = []
    speakers = sorted({row["speaker"] for rows in candidates.values() for row in rows})
    baseline = candidates[1.0]
    baseline_speaker = {speaker: float(np.mean([row["utmos"] for row in baseline
                                                if row["speaker"] == speaker]))
                        for speaker in speakers}
    for gain, rows in candidates.items():
        speaker_mean = {speaker: float(np.mean([row["utmos"] for row in rows
                                                if row["speaker"] == speaker]))
                        for speaker in speakers}
        results.append({"gain": gain, "utmos_mean": float(np.mean([row["utmos"] for row in rows])),
                        "speaker_utmos_mean": speaker_mean,
                        "speaker_delta_from_baseline": {
                            speaker: speaker_mean[speaker] - baseline_speaker[speaker]
                            for speaker in speakers}, "rows": rows})
    eligible = [row for row in results if row["gain"] > 1.0
                and row["utmos_mean"] > results[0]["utmos_mean"]
                and all(delta >= 0.0 for delta in row["speaker_delta_from_baseline"].values())]
    selected = max(eligible, key=lambda row: row["utmos_mean"])["gain"] if eligible else None
    summary = {"task": "PS-20261021-10", "round": 46,
               "kind": "non_f0_temporal_contrast_validation_sweep",
               "checkpoint_sha256": base.sha256(args.checkpoint), "gains": list(GAINS),
               "validation_rows": len(baseline), "results": results,
               "selection_gate": "mean improves and neither validation speaker regresses",
               "selected_gain": selected, "track9_used": False, "fixed_male_used": False,
               "played": False, "board_touched": False, "board_powered": False}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected_gain": selected,
                      "results": [{key: value for key, value in row.items() if key != "rows"}
                                  for row in results]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
