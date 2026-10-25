"""Measure fixed prediction-to-teacher lag for the Round-33 prosody model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import train_hubert_world_causal_gru_round23_20261025 as prior  # noqa: E402
import train_paired_hubert_world_gru_round26_20261025 as paired  # noqa: E402
import audit_source_prosody_round32_20261025 as prosody_audit  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


LAGS = tuple(range(-4, 5))
GROUPS = {"spectrum": slice(0, base.SP_DIM),
          "log_f0": slice(base.SP_DIM, base.SP_DIM + 1),
          "energy": slice(base.SP_DIM + 2, base.SP_DIM + 3),
          "aperiodicity": slice(base.SP_DIM + 3, base.OUTPUT_DIM)}


def smooth_l1(left: np.ndarray, right: np.ndarray) -> float:
    absolute = np.abs(left - right)
    return float(np.mean(np.where(absolute < 1.0, 0.5 * absolute * absolute, absolute - 0.5)))


def aligned(left: np.ndarray, right: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    if lag > 0:
        return left[:-lag], right[lag:]
    if lag < 0:
        return left[-lag:], right[:lag]
    return left, right


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--checkpoint", type=Path,
                        default=ROOT / "build/generated/hubert_world_round33_20261025/paired_causal_gru.pt")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round35_20261025")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if not checkpoint.get("source_prosody"):
        raise ValueError("Round 35 requires a source-prosody checkpoint")
    model = paired.ProsodyCausalWorldGRU()
    model.load_state_dict(checkpoint["model"]); model.eval()

    round25 = ROOT / "build/generated/hubert_world_round25_20261025"
    manifest = json.loads((round25 / "cache_manifest.json").read_text(encoding="utf-8"))
    records = [row for row in manifest["records"] if row["split"] == "validation"]
    corpus = args.asset_root / "交接/核心材料/board_budget_20261005/full_train_corpus_16k"
    declaration = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    declared = {row["stem"]: row for split in ("train", "validation")
                for row in declaration[split]}
    mean = checkpoint["pca_mean"]; projection = checkpoint["pca_projection"]
    x_mean = checkpoint["x_mean"]; x_std = checkpoint["x_std"]
    y_mean = checkpoint["y_mean"]; y_std = checkpoint["y_std"]
    prosody_mean = checkpoint["prosody_mean"]; prosody_std = checkpoint["prosody_std"]

    rows = []
    for record in records:
        data = np.load(round25 / "cache" / record["cache"])
        content = data["content"].astype(np.float32)
        target = data["target"].astype(np.float32)
        declaration_row = declared[record["stem"]]
        source_path = prosody_audit.resolve(corpus, "src", declaration_row["src"])
        digest = base.sha256(source_path)
        if digest != declaration_row["src_sha"] or digest != record["source_sha256"]:
            raise ValueError(f"source SHA mismatch: {record['stem']}")
        source = prosody_audit.read_raw(source_path)
        source_prosody = prosody_audit.resample_rows(
            prosody_audit.source_prosody(source), len(content))
        x = (((content - mean) @ projection - x_mean) / x_std).astype(np.float32)
        x = np.concatenate((x, ((source_prosody - prosody_mean) / prosody_std).astype(np.float32)),
                           axis=1)
        target_z = ((target - y_mean) / y_std).astype(np.float32)
        with torch.inference_mode():
            prediction = model(torch.from_numpy(x[None]))[0].numpy()

        losses = {}
        for lag in LAGS:
            prediction_aligned, target_aligned = aligned(prediction, target_z, lag)
            row = {name: smooth_l1(prediction_aligned[:, region], target_aligned[:, region])
                   for name, region in GROUPS.items()}
            row["overall"] = smooth_l1(prediction_aligned[:, prior.CONTINUOUS],
                                       target_aligned[:, prior.CONTINUOUS])
            losses[str(lag)] = row
        best_lag = min(LAGS, key=lambda value: losses[str(value)]["overall"])
        rows.append({"stem": record["stem"], "speaker": record["speaker"],
                     "frames": len(content), "best_lag": best_lag,
                     "best_lag_ms": best_lag * 20, "losses": losses})

    aggregate = {str(lag): {name: float(np.mean([row["losses"][str(lag)][name]
                                                  for row in rows]))
                            for name in (*GROUPS, "overall")}
                 for lag in LAGS}
    best_lag = min(LAGS, key=lambda value: aggregate[str(value)]["overall"])
    baseline = aggregate["0"]["overall"]
    best = aggregate[str(best_lag)]["overall"]
    improvement = 100.0 * (baseline - best) / baseline
    signs = {"negative": sum(row["best_lag"] < 0 for row in rows),
             "zero": sum(row["best_lag"] == 0 for row in rows),
             "positive": sum(row["best_lag"] > 0 for row in rows)}
    consistent = signs["negative"] >= 5 if best_lag < 0 else signs["positive"] >= 5 if best_lag > 0 else False
    go = best_lag != 0 and improvement >= 1.0 and consistent
    summary = {"task": "PS-20261021-10", "round": 35,
               "kind": "prediction_teacher_lag_audit", "validation_rows": len(rows),
               "lag_definition": "prediction[t] compared with teacher[t+lag]",
               "aggregate_losses": aggregate, "aggregate_best_lag": best_lag,
               "aggregate_best_lag_ms": best_lag * 20,
               "aggregate_improvement_percent": improvement,
               "per_row_best_lag_signs": signs,
               "decision_gate": {"minimum_improvement_percent": 1.0,
                                 "minimum_consistent_rows": 5},
               "limited_lookahead_go": go,
               "checkpoint_sha256": base.sha256(args.checkpoint),
               "rows": rows, "training_started": False, "track9_used": False,
               "fixed_male_used": False, "played": False, "board_touched": False}
    (args.output / "lag_audit.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
