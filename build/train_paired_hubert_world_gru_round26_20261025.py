"""Long paired-data causal GRU training for Round 26."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import train_hubert_world_causal_gru_round23_20261025 as prior  # noqa: E402
import audit_source_prosody_round32_20261025 as prosody_audit  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


SEED = 20261025
CROP = 128
BATCH = 8
STEPS = 2000
CHECK_EVERY = 100
PATIENCE = 8
ANCHOR_PROBABILITY = 0.25
VUV_INDEX = prior.VUV_INDEX


class ProsodyCausalWorldGRU(prior.CausalWorldGRU):
    def __init__(self) -> None:
        super().__init__()
        self.input = torch.nn.Linear(prior.PCA_DIM + 3, prior.HIDDEN)


def interpolate(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def load_cache(cache: Path, record: dict) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(cache / record["cache"])
    content = data["content"].astype(np.float32)
    target = data["target"].astype(np.float32)
    if content.shape != (record["content_frames"], 768) or target.shape != (len(content), base.OUTPUT_DIM):
        raise ValueError(f"cache shape mismatch: {record['stem']}")
    if not np.isfinite(content).all() or not np.isfinite(target).all():
        raise ValueError(f"non-finite cache: {record['stem']}")
    return content, target


def loss_terms(prediction: torch.Tensor, target: torch.Tensor, target_vuv: torch.Tensor,
               positive_weight: torch.Tensor, multiscale: bool,
               group_balanced: bool = False,
               variance_matching: bool = False) -> tuple[torch.Tensor, dict]:
    if not multiscale:
        return prior.loss_terms(prediction, target, target_vuv, positive_weight)
    continuous_prediction = prediction[..., prior.CONTINUOUS]
    continuous_target = target[..., prior.CONTINUOUS]
    reconstruction = torch.nn.functional.smooth_l1_loss(continuous_prediction, continuous_target)
    vuv = torch.nn.functional.binary_cross_entropy_with_logits(
        prediction[..., VUV_INDEX], target_vuv, pos_weight=positive_weight)
    deltas = []
    group_deltas = []
    groups = (slice(0, base.SP_DIM), slice(base.SP_DIM, base.SP_DIM + 1),
              slice(base.SP_DIM + 1, base.SP_DIM + 2),
              slice(base.SP_DIM + 2, base.OUTPUT_DIM - 1))
    for lag in (1, 2, 4):
        prediction_delta = continuous_prediction[:, lag:] - continuous_prediction[:, :-lag]
        target_delta = continuous_target[:, lag:] - continuous_target[:, :-lag]
        per_group = [torch.nn.functional.smooth_l1_loss(prediction_delta[..., group],
                                                        target_delta[..., group])
                     for group in groups]
        group_deltas.append(per_group)
        deltas.append(torch.stack(per_group).mean() if group_balanced else
                      torch.nn.functional.smooth_l1_loss(prediction_delta, target_delta))
    multiscale_delta = torch.stack(deltas).mean()
    total = reconstruction + 0.35 * vuv + 0.75 * multiscale_delta
    metrics = {"total": float(total.detach()),
               "reconstruction": float(reconstruction.detach()),
               "vuv_bce": float(vuv.detach()),
               "multiscale_delta": float(multiscale_delta.detach()),
               "delta_lag1": float(deltas[0].detach()),
               "delta_lag2": float(deltas[1].detach()),
               "delta_lag4": float(deltas[2].detach())}
    if variance_matching:
        prediction_delta = continuous_prediction[:, 1:] - continuous_prediction[:, :-1]
        target_delta = continuous_target[:, 1:] - continuous_target[:, :-1]
        variance_terms = []
        for group in groups:
            prediction_rms = torch.sqrt(torch.mean(prediction_delta[..., group] ** 2) + 1e-6)
            target_rms = torch.sqrt(torch.mean(target_delta[..., group] ** 2) + 1e-6)
            variance_terms.append((torch.log(prediction_rms) - torch.log(target_rms)) ** 2)
        variance_match = torch.stack(variance_terms).mean()
        total = total + 0.05 * variance_match
        metrics["total"] = float(total.detach())
        metrics["variance_match"] = float(variance_match.detach())
    if group_balanced:
        for name, index in (("spectrum", 0), ("log_f0", 1), ("energy", 2), ("aperiodicity", 3)):
            metrics[f"delta_{name}"] = float(torch.stack(
                [per_lag[index] for per_lag in group_deltas]).mean().detach())
    return total, metrics


def validate(model: prior.CausalWorldGRU, rows: list[tuple[np.ndarray, np.ndarray]],
             positive_weight: torch.Tensor, multiscale: bool, group_balanced: bool,
             variance_matching: bool) -> dict:
    metrics = []
    model.eval()
    with torch.inference_mode():
        for x, target in rows:
            prediction = model(torch.from_numpy(x[None]))
            _, row = loss_terms(prediction, torch.from_numpy(target[None]),
                                torch.from_numpy(target[None, :, VUV_INDEX]), positive_weight,
                                multiscale, group_balanced, variance_matching)
            metrics.append(row)
    return {key: float(np.mean([row[key] for row in metrics])) for key in metrics[0]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round26_20261025")
    parser.add_argument("--multiscale-dynamics", action="store_true",
                        help="Round 28: use fixed 0.75 x mean(lag 1/2/4) dynamic loss")
    parser.add_argument("--group-balanced-dynamics", action="store_true",
                        help="Round 30: average spectrum/log-F0/energy/AP dynamic groups equally")
    parser.add_argument("--source-prosody", action="store_true",
                        help="Round 33: append normalized source log-F0/VUV/log-energy")
    parser.add_argument("--variance-matching", action="store_true",
                        help="Round 37: add fixed 0.05 x four-group lag-1 log-RMS loss")
    args = parser.parse_args()
    if args.group_balanced_dynamics and not args.multiscale_dynamics:
        raise ValueError("group-balanced dynamics requires --multiscale-dynamics")
    if args.source_prosody and (not args.multiscale_dynamics or args.group_balanced_dynamics):
        raise ValueError("source prosody requires Round-28 multiscale loss without group balancing")
    if args.variance_matching and not args.source_prosody:
        raise ValueError("variance matching requires --source-prosody")
    if args.multiscale_dynamics and args.output.name == "hubert_world_round26_20261025":
        raise ValueError("Round 28 requires a separate --output directory")
    args.output = args.output.resolve()
    experiment_round = (37 if args.variance_matching else
                        33 if args.source_prosody else
                        30 if args.group_balanced_dynamics else
                        28 if args.multiscale_dynamics else 26)
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    torch.manual_seed(SEED); np.random.seed(SEED); torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)

    round25 = ROOT / "build/generated/hubert_world_round25_20261025"
    manifest_path = round25 / "cache_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest["complete"] or manifest["target_track9_used"] or manifest["processed_pairs"] != 200:
        raise ValueError("Round 25 cache is not the complete frozen corpus")
    cache = round25 / "cache"
    train_records = [row for row in manifest["records"] if row["split"] == "train"]
    validation_records = [row for row in manifest["records"] if row["split"] == "validation"]
    train_raw = [load_cache(cache, row) for row in train_records]
    validation_raw = [load_cache(cache, row) for row in validation_records]

    source_prosody = None
    prosody_mean = prosody_std = None
    if args.source_prosody:
        corpus = args.asset_root / "交接/核心材料/board_budget_20261005/full_train_corpus_16k"
        declaration = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
        declared = {row["stem"]: row for split in ("train", "validation")
                    for row in declaration[split]}

        def extract(record: dict, frames: int) -> np.ndarray:
            row = declared[record["stem"]]
            path = prosody_audit.resolve(corpus, "src", row["src"])
            digest = base.sha256(path)
            if digest != row["src_sha"] or digest != record["source_sha256"]:
                raise ValueError(f"source SHA mismatch: {record['stem']}")
            signal = prosody_audit.read_raw(path)
            return prosody_audit.resample_rows(prosody_audit.source_prosody(signal), frames)

        train_source_prosody = [extract(record, len(raw[0]))
                                for record, raw in zip(train_records, train_raw)]
        validation_source_prosody = [extract(record, len(raw[0]))
                                     for record, raw in zip(validation_records, validation_raw)]
        pooled_prosody = np.concatenate(train_source_prosody)
        prosody_mean = pooled_prosody.mean(axis=0)
        prosody_std = np.maximum(pooled_prosody.std(axis=0), 0.05)
        source_prosody = (train_source_prosody, validation_source_prosody)

    # PCA and normalizers are fitted only from the 192 paired training rows.
    mean, projection = base.pca_fit([content for content, _ in train_raw])
    projected_train = [(content - mean) @ projection for content, _ in train_raw]
    pooled_x = np.concatenate(projected_train)
    x_mean = pooled_x.mean(axis=0); x_std = np.maximum(pooled_x.std(axis=0), 0.05)
    pooled_y = np.concatenate([target for _, target in train_raw])
    y_mean = pooled_y.mean(axis=0); y_std = np.maximum(pooled_y.std(axis=0), 0.05)

    def prepare(content: np.ndarray, target: np.ndarray,
                prosody: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        x = (((content - mean) @ projection - x_mean) / x_std).astype(np.float32)
        if args.source_prosody:
            if prosody is None or len(prosody) != len(x):
                raise ValueError("source prosody is missing or misaligned")
            x = np.concatenate((x, ((prosody - prosody_mean) / prosody_std).astype(np.float32)), axis=1)
        z = ((target - y_mean) / y_std).astype(np.float32)
        z[:, VUV_INDEX] = target[:, VUV_INDEX]
        return x, z

    train = [prepare(content, target, source_prosody[0][index] if source_prosody else None)
             for index, (content, target) in enumerate(train_raw)]
    validation = [prepare(content, target, source_prosody[1][index] if source_prosody else None)
                  for index, (content, target) in enumerate(validation_raw)]

    # Target self-reconstruction anchors influence optimization but never PCA,
    # normalization, validation, or early stopping.
    hubert_dir = args.asset_root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    hubert = base.HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    for parameter in hubert.parameters(): parameter.requires_grad_(False)
    anchors_raw = []
    for number in (5, 6, 7, 8):
        signal = base.read_16k(args.asset_root / f"人物音频资料/女声/Track {number}.wav")
        content = base.extract_hubert(hubert, signal)
        world = base.analyze_world(signal)
        target = interpolate(world["output"], len(content))
        prosody = (prosody_audit.resample_rows(prosody_audit.source_prosody(signal), len(content))
                   if args.source_prosody else None)
        anchors_raw.append((content, target, world, prosody))
    anchors = [prepare(content, target, prosody) for content, target, _, prosody in anchors_raw]
    eligible_train = [row for row in train if len(row[0]) >= CROP]
    eligible_anchors = [row for row in anchors if len(row[0]) >= CROP]
    if not eligible_train or len(eligible_anchors) != len(anchors):
        raise ValueError("eligible paired/anchor crop pool is incomplete")
    excluded_short_pairs = len(train) - len(eligible_train)

    voiced_fraction = float(np.mean(pooled_y[:, VUV_INDEX] > 0.5))
    positive_weight = torch.tensor((1.0 - voiced_fraction) / max(voiced_fraction, 1e-4))
    model = ProsodyCausalWorldGRU() if args.source_prosody else prior.CausalWorldGRU()
    optimizer = torch.optim.AdamW(model.parameters(), lr=6e-4, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, STEPS)
    rng = np.random.default_rng(SEED)
    history = []; best = None; stale = 0
    for step in range(1, STEPS + 1):
        batch_x, batch_y = [], []
        for _ in range(BATCH):
            pool = eligible_anchors if rng.random() < ANCHOR_PROBABILITY else eligible_train
            x, target = pool[int(rng.integers(len(pool)))]
            start = int(rng.integers(len(x) - CROP + 1))
            batch_x.append(x[start:start + CROP]); batch_y.append(target[start:start + CROP])
        x = torch.from_numpy(np.stack(batch_x)); target = torch.from_numpy(np.stack(batch_y))
        prediction = model(x)
        loss, metrics = loss_terms(prediction, target, target[..., VUV_INDEX], positive_weight,
                                   args.multiscale_dynamics, args.group_balanced_dynamics,
                                   args.variance_matching)
        optimizer.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step(); scheduler.step()
        if step == 1 or step % CHECK_EVERY == 0:
            valid = validate(model, validation, positive_weight, args.multiscale_dynamics,
                             args.group_balanced_dynamics, args.variance_matching)
            record = {"step": step, "train": metrics, "validation": valid,
                      "learning_rate": optimizer.param_groups[0]["lr"]}
            history.append(record); print(json.dumps(record), flush=True)
            if best is None or valid["total"] < best["validation_total"] - 1e-4:
                best = {"step": step, "validation_total": valid["total"],
                        "state": {key: value.detach().clone() for key, value in model.state_dict().items()}}
                stale = 0
            else:
                stale += 1
            if stale >= PATIENCE: break
    assert best is not None
    model.load_state_dict(best.pop("state"))
    causal_difference = prior.verify_causality(model, validation[0][0])
    checkpoint = args.output / "paired_causal_gru.pt"
    checkpoint_format = ("paired_hubert_world_causal_gru_round37_variance_matching_v1"
                         if args.variance_matching else
                         "paired_hubert_world_causal_gru_round33_source_prosody_v1"
                         if args.source_prosody else
                         "paired_hubert_world_causal_gru_round30_group_balanced_v1"
                         if args.group_balanced_dynamics else
                         "paired_hubert_world_causal_gru_round28_multiscale_v1"
                         if args.multiscale_dynamics else "paired_hubert_world_causal_gru_round26_v1")
    torch.save({"format": checkpoint_format,
                "model": model.state_dict(), "pca_mean": mean, "pca_projection": projection,
                "x_mean": x_mean, "x_std": x_std, "y_mean": y_mean, "y_std": y_std,
                "source_prosody": args.source_prosody,
                "prosody_mean": prosody_mean, "prosody_std": prosody_std,
                "best": best, "history": history,
                "round25_manifest_sha256": base.sha256(manifest_path)}, checkpoint)

    # Frozen target-speaker Track 9 development regression.
    signal9 = base.read_16k(args.asset_root / "人物音频资料/女声/Track 9.wav")
    content9 = base.extract_hubert(hubert, signal9); world9 = base.analyze_world(signal9); del hubert
    x9 = (((content9 - mean) @ projection - x_mean) / x_std).astype(np.float32)
    if args.source_prosody:
        prosody9 = prosody_audit.resample_rows(prosody_audit.source_prosody(signal9), len(content9))
        x9 = np.concatenate((x9, ((prosody9 - prosody_mean) / prosody_std).astype(np.float32)), axis=1)
    with torch.inference_mode(): raw20 = model(torch.from_numpy(x9[None]))[0].numpy()
    continuous20 = raw20 * y_std + y_mean
    probability20 = 1.0 / (1.0 + np.exp(-np.clip(raw20[:, VUV_INDEX], -20.0, 20.0)))
    prediction = interpolate(continuous20, len(world9["output"]))
    vuv_probability = interpolate(probability20[:, None], len(prediction))[:, 0]
    anchor_y = np.concatenate([target for _, target, _, _ in anchors_raw])
    prediction = np.clip(prediction, np.percentile(anchor_y, 0.1, axis=0),
                         np.percentile(anchor_y, 99.9, axis=0))
    prediction[:, VUV_INDEX] = (vuv_probability - 0.5) * 8.0
    voiced = anchor_y[:, VUV_INDEX] > 0.5
    log_sp = np.log(np.maximum(np.concatenate(
        [world["spectrum"] for _, _, world, _ in anchors_raw]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(anchor_y[voiced, base.SP_DIM], 0.5)),
             "log_f0_hi": float(np.percentile(anchor_y[voiced, base.SP_DIM], 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}
    reconstructed, synthesis = base.synthesize(prediction, stats)
    wav_path = args.output / ("track9_paired_causal_gru_variance_matching.wav"
                              if args.variance_matching else
                              "track9_paired_causal_gru_source_prosody.wav"
                              if args.source_prosody else
                              "track9_paired_causal_gru_group_balanced.wav"
                              if args.group_balanced_dynamics else
                              "track9_paired_causal_gru_multiscale.wav"
                              if args.multiscale_dynamics else "track9_paired_causal_gru.wav")
    base.sf.write(wav_path, reconstructed, base.SAMPLE_RATE, subtype="PCM_16")
    summary = {"task": "PS-20261021-10", "round": experiment_round,
               "kind": ("paired_hubert_world_causal_gru_variance_matching"
                        if args.variance_matching else
                        "paired_hubert_world_causal_gru_source_prosody"
                        if args.source_prosody else
                        "paired_hubert_world_causal_gru_group_balanced"
                        if args.group_balanced_dynamics else
                        "paired_hubert_world_causal_gru_multiscale"
                        if args.multiscale_dynamics else "paired_hubert_world_causal_gru"), "parameters":
               sum(parameter.numel() for parameter in model.parameters()),
               "best": best, "steps_completed": history[-1]["step"],
               "early_stopped": stale >= PATIENCE, "causal_prefix_max_abs": causal_difference,
               "paired_train": len(train), "paired_validation": len(validation),
               "excluded_short_train_pairs": excluded_short_pairs,
               "anchor_probability": ANCHOR_PROBABILITY, "target_track9_used_for_selection": False,
               "input_dimensions": 99 if args.source_prosody else 96,
               "source_prosody": args.source_prosody,
               "variance_matching": ({"weight": 0.05, "lag": 1,
                                      "groups": ["spectrum", "log_f0", "energy", "aperiodicity"]}
                                     if args.variance_matching else None),
               "dynamic_loss": ({"weight": 0.75, "lags": [1, 2, 4], "reduction": "mean"}
                                if args.multiscale_dynamics
                                else {"weight": 0.20, "lags": [1], "reduction": "mean"}),
               "synthesis": synthesis, "checkpoint_sha256": base.sha256(checkpoint),
               "reconstruction_sha256": base.sha256(wav_path),
               "elapsed_seconds": time.monotonic() - started,
               "played": False, "board_touched": False}
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
    if args.group_balanced_dynamics:
        summary["dynamic_loss"]["reduction"] = "equal_mean_of_spectrum_log_f0_energy_aperiodicity"
    candidate = ("track9_paired_causal_gru_variance_matching" if args.variance_matching else
                 "track9_paired_causal_gru_source_prosody" if args.source_prosody else
                 "track9_paired_causal_gru_group_balanced" if args.group_balanced_dynamics else
                 "track9_paired_causal_gru_multiscale" if args.multiscale_dynamics else
                 "track9_paired_causal_gru")
    manifest_out = {"inputs": [{"role": "source", "path": "人物音频资料/女声/Track 9.wav"}],
                    "outputs": [{"candidate": candidate,
                                 "path": str(wav_path.relative_to(ROOT)).replace("\\", "/")}]}
    (args.output / "strict_manifest.json").write_text(json.dumps(manifest_out, ensure_ascii=False, indent=2) + "\n",
                                                      encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__": main()
