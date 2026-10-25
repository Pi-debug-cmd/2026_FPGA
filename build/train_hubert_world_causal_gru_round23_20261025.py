"""Train the Round-23 causal GRU HuBERT-to-WORLD teacher."""
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
import numpy as np  # noqa: E402
import torch  # noqa: E402
from torch import nn  # noqa: E402
from torch.nn import functional as F  # noqa: E402


SEED = 20261025
PCA_DIM = 96
HIDDEN = 192
LAYERS = 2
CROP = 400
BATCH = 8
STEPS = 3000
CHECK_EVERY = 100
PATIENCE = 8
VUV_INDEX = base.SP_DIM + 1
CONTINUOUS = tuple(index for index in range(base.OUTPUT_DIM) if index != VUV_INDEX)


def interpolate(features: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(features), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, features[:, column])
                     for column in range(features.shape[1])], axis=1).astype(np.float32)


class CausalWorldGRU(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.input = nn.Linear(PCA_DIM, HIDDEN)
        self.gru = nn.GRU(HIDDEN, HIDDEN, num_layers=LAYERS, batch_first=True)
        self.output = nn.Linear(HIDDEN, base.OUTPUT_DIM)

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        hidden, _ = self.gru(torch.tanh(self.input(value)))
        return self.output(hidden)


def loss_terms(prediction: torch.Tensor, target_z: torch.Tensor,
               target_vuv: torch.Tensor, positive_weight: torch.Tensor) -> tuple[torch.Tensor, dict]:
    continuous_prediction = prediction[..., CONTINUOUS]
    continuous_target = target_z[..., CONTINUOUS]
    reconstruction = F.smooth_l1_loss(continuous_prediction, continuous_target)
    vuv = F.binary_cross_entropy_with_logits(prediction[..., VUV_INDEX], target_vuv,
                                              pos_weight=positive_weight)
    delta = F.smooth_l1_loss(continuous_prediction[:, 1:] - continuous_prediction[:, :-1],
                             continuous_target[:, 1:] - continuous_target[:, :-1])
    total = reconstruction + 0.35 * vuv + 0.20 * delta
    return total, {"total": float(total.detach()),
                   "reconstruction": float(reconstruction.detach()),
                   "vuv_bce": float(vuv.detach()), "delta": float(delta.detach())}


def validate(model: CausalWorldGRU, rows: list[tuple[np.ndarray, np.ndarray]],
             positive_weight: torch.Tensor) -> dict:
    records = []
    model.eval()
    with torch.inference_mode():
        for x, y in rows:
            prediction = model(torch.from_numpy(x[None]))
            target_z = torch.from_numpy(y[None])
            target_vuv = torch.from_numpy(y[None, :, VUV_INDEX] > 0.0).float()
            _, metrics = loss_terms(prediction, target_z, target_vuv, positive_weight)
            records.append(metrics)
    return {key: float(np.mean([record[key] for record in records])) for key in records[0]}


def verify_causality(model: CausalWorldGRU, example: np.ndarray) -> float:
    boundary = min(199, len(example) // 2)
    original = torch.from_numpy(example[None].copy())
    changed = original.clone()
    changed[:, boundary + 1:] += 5.0
    model.eval()
    with torch.inference_mode():
        left = model(original)[:, :boundary + 1]
        right = model(changed)[:, :boundary + 1]
    difference = float(torch.max(torch.abs(left - right)))
    if difference > 1e-7:
        raise AssertionError(f"future input changed causal prefix: {difference}")
    return difference


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round23_20261025")
    args = parser.parse_args()
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)

    target_dir = args.asset_root / "人物音频资料/女声"
    hubert_dir = args.asset_root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    hubert = base.HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    for parameter in hubert.parameters():
        parameter.requires_grad_(False)
    rows = {}
    for number in (5, 6, 7, 8):
        signal = base.read_16k(target_dir / f"Track {number}.wav")
        content = base.extract_hubert(hubert, signal)
        world = base.analyze_world(signal)
        rows[number] = {"content": content, "world": world}
        print(json.dumps({"track": number, "content_frames": len(content),
                          "world_frames": len(world["output"])}, ensure_ascii=False), flush=True)

    # PCA and all normalizers use only the first 80% of Tracks 5-8.
    pca_training = [row["content"][:int(len(row["content"]) * 0.8)] for row in rows.values()]
    mean, projection = base.pca_fit(pca_training)
    prepared = {}
    x_training, y_training = [], []
    for number, row in rows.items():
        reduced = (row["content"] - mean) @ projection
        x = interpolate(reduced, len(row["world"]["output"]))
        y = row["world"]["output"].astype(np.float32)
        boundary = int(min(len(x), len(y)) * 0.8)
        prepared[number] = {"x": x, "y": y, "boundary": boundary}
        x_training.append(x[:boundary]); y_training.append(y[:boundary])
    pooled_x = np.concatenate(x_training)
    x_mean = pooled_x.mean(axis=0)
    x_std = np.maximum(pooled_x.std(axis=0), 0.05)
    pooled_y = np.concatenate(y_training)
    y_mean = pooled_y.mean(axis=0)
    y_std = np.maximum(pooled_y.std(axis=0), 0.05)
    for item in prepared.values():
        item["x"] = ((item["x"] - x_mean) / x_std).astype(np.float32)
        item["z"] = ((item["y"] - y_mean) / y_std).astype(np.float32)
        # The VUV target remains an unnormalized 0/1 label.
        item["z"][:, VUV_INDEX] = item["y"][:, VUV_INDEX]

    voiced_fraction = float(np.mean(pooled_y[:, VUV_INDEX] > 0.5))
    positive_weight = torch.tensor((1.0 - voiced_fraction) / max(voiced_fraction, 1e-4),
                                   dtype=torch.float32)
    train_ranges = [(number, 0, item["boundary"]) for number, item in prepared.items()
                    if item["boundary"] >= CROP]
    validation = [(item["x"][item["boundary"]:], item["z"][item["boundary"]:])
                  for item in prepared.values()]

    model = CausalWorldGRU()
    optimizer = torch.optim.AdamW(model.parameters(), lr=8e-4, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, STEPS)
    rng = np.random.default_rng(SEED)
    history = []
    best = None
    stale = 0
    for step in range(1, STEPS + 1):
        batch_x, batch_y = [], []
        for _ in range(BATCH):
            number, lower, upper = train_ranges[int(rng.integers(len(train_ranges)))]
            start = int(rng.integers(lower, upper - CROP + 1))
            batch_x.append(prepared[number]["x"][start:start + CROP])
            batch_y.append(prepared[number]["z"][start:start + CROP])
        x = torch.from_numpy(np.stack(batch_x))
        target = torch.from_numpy(np.stack(batch_y))
        prediction = model(x)
        loss, metrics = loss_terms(prediction, target, target[..., VUV_INDEX], positive_weight)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        if step == 1 or step % CHECK_EVERY == 0:
            valid = validate(model, validation, positive_weight)
            record = {"step": step, "train": metrics, "validation": valid,
                      "learning_rate": optimizer.param_groups[0]["lr"]}
            history.append(record)
            print(json.dumps(record), flush=True)
            if best is None or valid["total"] < best["validation_total"] - 1e-4:
                best = {"step": step, "validation_total": valid["total"],
                        "state": {key: value.detach().clone()
                                  for key, value in model.state_dict().items()}}
                stale = 0
            else:
                stale += 1
            if stale >= PATIENCE:
                break
    assert best is not None
    model.load_state_dict(best.pop("state"))
    causal_difference = verify_causality(model, validation[0][0])

    checkpoint = args.output / "causal_gru_teacher.pt"
    torch.save({"format": "hubert_world_causal_gru_round23_v1", "model": model.state_dict(),
                "pca_mean": mean, "pca_projection": projection,
                "x_mean": x_mean, "x_std": x_std, "y_mean": y_mean, "y_std": y_std,
                "best": best, "history": history}, checkpoint)

    # Track 9 is decoded only after all training and early stopping are frozen.
    signal9 = base.read_16k(target_dir / "Track 9.wav")
    content9 = base.extract_hubert(hubert, signal9)
    world9 = base.analyze_world(signal9)
    del hubert
    x9 = interpolate((content9 - mean) @ projection, len(world9["output"]))
    x9 = ((x9 - x_mean) / x_std).astype(np.float32)
    with torch.inference_mode():
        raw = model(torch.from_numpy(x9[None]))[0].numpy()
    prediction = raw * y_std + y_mean
    vuv_probability = 1.0 / (1.0 + np.exp(-np.clip(raw[:, VUV_INDEX], -20.0, 20.0)))
    clip_lo = np.percentile(pooled_y, 0.1, axis=0)
    clip_hi = np.percentile(pooled_y, 99.9, axis=0)
    prediction = np.clip(prediction, clip_lo, clip_hi)
    prediction[:, VUV_INDEX] = (vuv_probability - 0.5) * 8.0
    voiced = pooled_y[:, VUV_INDEX] > 0.5
    log_sp = np.log(np.maximum(np.concatenate(
        [rows[number]["world"]["spectrum"][:prepared[number]["boundary"]]
         for number in (5, 6, 7, 8)]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(pooled_y[voiced, base.SP_DIM], 0.5)),
             "log_f0_hi": float(np.percentile(pooled_y[voiced, base.SP_DIM], 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}
    reconstructed, synthesis = base.synthesize(prediction, stats)
    wav_path = args.output / "track9_hubert_world_causal_gru.wav"
    base.sf.write(wav_path, reconstructed, base.SAMPLE_RATE, subtype="PCM_16")
    truth = world9["output"]
    mae = np.mean(np.abs(prediction - truth), axis=0)
    summary = {"task": "PS-20261021-10", "round": 23,
               "kind": "hubert_world_causal_gru_teacher", "seed": SEED,
               "parameters": sum(parameter.numel() for parameter in model.parameters()),
               "best": best, "steps_completed": history[-1]["step"],
               "early_stopped": stale >= PATIENCE,
               "causal_prefix_max_abs": causal_difference,
               "train_tracks": [5, 6, 7, 8], "development_track": 9,
               "track9_already_exposed": True,
               "normalizers_train_prefix_only": True,
               "synthesis": synthesis,
               "mae": {"spectrum_dct_mean": float(mae[:base.SP_DIM].mean()),
                       "log_f0": float(mae[base.SP_DIM]),
                       "vuv_probability": float(np.mean(np.abs(
                           vuv_probability - truth[:, VUV_INDEX]))),
                       "energy": float(mae[base.SP_DIM + 2]),
                       "aperiodicity_dct_mean": float(mae[base.SP_DIM + 3:].mean())},
               "checkpoint_sha256": base.sha256(checkpoint),
               "reconstruction_sha256": base.sha256(wav_path),
               "elapsed_seconds": time.monotonic() - started,
               "source_audio_used": False, "source_spectrum_skip": False,
               "played": False, "board_touched": False}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"inputs": [{"role": "source", "path": "人物音频资料/女声/Track 9.wav"}],
                "outputs": [{"candidate": "track9_hubert_world_causal_gru",
                             "path": "build/generated/hubert_world_round23_20261025/track9_hubert_world_causal_gru.wav"}]}
    (args.output / "strict_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
