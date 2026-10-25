"""Attribute Round-26 quality loss to teacher quality or prediction smoothing."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import train_hubert_world_causal_gru_round23_20261025 as prior  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


VUV_INDEX = prior.VUV_INDEX
GROUPS = {"spectrum": slice(0, base.SP_DIM), "log_f0": slice(base.SP_DIM, base.SP_DIM + 1),
          "energy": slice(base.SP_DIM + 2, base.SP_DIM + 3),
          "aperiodicity": slice(base.SP_DIM + 3, base.OUTPUT_DIM)}


def interpolate(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def dynamics(values: np.ndarray) -> dict:
    result = {}
    for name, region in GROUPS.items():
        block = values[:, region]
        result[name] = {"std_mean": float(np.mean(np.std(block, axis=0))),
                        "delta_rms": float(np.sqrt(np.mean(np.diff(block, axis=0) ** 2)))}
    vuv = values[:, VUV_INDEX]
    result["vuv"] = {"mean": float(np.mean(vuv)),
                     "transition_rate": float(np.mean((vuv[1:] >= 0.5) != (vuv[:-1] >= 0.5)))}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round27_20261025")
    parser.add_argument("--checkpoint", type=Path,
                        default=ROOT / "build/generated/hubert_world_round26_20261025/paired_causal_gru.pt")
    parser.add_argument("--experiment-round", type=int, default=27)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.checkpoint = args.checkpoint.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    # Load the established evaluator from the asset root so its model paths are valid.
    spec = importlib.util.spec_from_file_location(
        "round27_audit_runtime", args.asset_root / "build/audit_seed_reference_20261016.py")
    audit = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(audit)
    evaluator = audit.Evaluators()

    round25 = ROOT / "build/generated/hubert_world_round25_20261025"
    manifest = json.loads((round25 / "cache_manifest.json").read_text(encoding="utf-8"))
    cache = round25 / "cache"
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = prior.CausalWorldGRU(); model.load_state_dict(checkpoint["model"]); model.eval()
    mean = checkpoint["pca_mean"]; projection = checkpoint["pca_projection"]
    x_mean = checkpoint["x_mean"]; x_std = checkpoint["x_std"]
    y_mean = checkpoint["y_mean"]; y_std = checkpoint["y_std"]

    train_targets = []
    for record in manifest["records"]:
        if record["split"] == "train":
            train_targets.append(np.load(cache / record["cache"])["target"].astype(np.float32))
    pooled_y = np.concatenate(train_targets)
    clip_lo = np.percentile(pooled_y, 0.1, axis=0)
    clip_hi = np.percentile(pooled_y, 99.9, axis=0)
    voiced = pooled_y[:, VUV_INDEX] > 0.5

    anchor_world = []
    for number in (5, 6, 7, 8):
        signal = base.read_16k(args.asset_root / f"人物音频资料/女声/Track {number}.wav")
        anchor_world.append(base.analyze_world(signal))
    log_sp = np.log(np.maximum(np.concatenate([row["spectrum"] for row in anchor_world]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(pooled_y[voiced, base.SP_DIM], 0.5)),
             "log_f0_hi": float(np.percentile(pooled_y[voiced, base.SP_DIM], 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}

    rows = []
    for record in [row for row in manifest["records"] if row["split"] == "validation"]:
        data = np.load(cache / record["cache"])
        content = data["content"].astype(np.float32)
        teacher20 = data["target"].astype(np.float32)
        x = (((content - mean) @ projection - x_mean) / x_std).astype(np.float32)
        with torch.inference_mode(): raw = model(torch.from_numpy(x[None]))[0].numpy()
        prediction20 = raw * y_std + y_mean
        prediction_probability = 1.0 / (1.0 + np.exp(-np.clip(raw[:, VUV_INDEX], -20.0, 20.0)))
        prediction20 = np.clip(prediction20, clip_lo, clip_hi)
        prediction20[:, VUV_INDEX] = prediction_probability

        frames5 = int(round(record["teacher_samples"] / (base.SAMPLE_RATE * base.FRAME_PERIOD_MS / 1000))) + 1
        audio = {}
        for kind, features20 in (("teacher", teacher20), ("prediction", prediction20)):
            features5 = interpolate(features20, frames5)
            features5[:, VUV_INDEX] = (features5[:, VUV_INDEX] - 0.5) * 8.0
            waveform, synthesis = base.synthesize(features5, stats)
            path = args.output / f"{record['stem']}_{kind}.wav"
            base.sf.write(path, waveform, base.SAMPLE_RATE, subtype="PCM_16")
            audio[kind] = {"utmos": evaluator.naturalness(waveform.astype(np.float64)),
                           "sha256": base.sha256(path), "synthesis": synthesis,
                           "dynamics": dynamics(features20)}
        ratios = {}
        for group in GROUPS:
            ratios[group] = {
                metric + "_prediction_over_teacher":
                audio["prediction"]["dynamics"][group][metric]
                / max(audio["teacher"]["dynamics"][group][metric], 1e-8)
                for metric in ("std_mean", "delta_rms")}
        rows.append({"stem": record["stem"], "speaker": record["speaker"],
                     "seconds": record["teacher_samples"] / base.SAMPLE_RATE,
                     "teacher": audio["teacher"], "prediction": audio["prediction"],
                     "ratios": ratios})
        print(json.dumps({"stem": record["stem"],
                          "teacher_utmos": audio["teacher"]["utmos"],
                          "prediction_utmos": audio["prediction"]["utmos"]}), flush=True)

    aggregate_ratios = {}
    for group in GROUPS:
        aggregate_ratios[group] = {
            metric: float(np.mean([row["ratios"][group][metric] for row in rows]))
            for metric in rows[0]["ratios"][group]}
    summary = {"task": "PS-20261021-10", "round": args.experiment_round,
               "kind": "paired_teacher_prediction_dynamics_audit",
               "checkpoint_sha256": base.sha256(args.checkpoint),
               "validation_rows": len(rows),
               "teacher_utmos_mean": float(np.mean([row["teacher"]["utmos"] for row in rows])),
               "prediction_utmos_mean": float(np.mean([row["prediction"]["utmos"] for row in rows])),
               "utmos_drop_mean": float(np.mean([row["teacher"]["utmos"]
                                                  - row["prediction"]["utmos"] for row in rows])),
               "aggregate_dynamic_ratios": aggregate_ratios,
               "rows": rows, "training_started": False, "track9_used": False,
               "fixed_male_used": False, "played": False, "board_touched": False}
    (args.output / "audit.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"},
                     ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__": main()
