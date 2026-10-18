"""Dry-run harness for a causal, fixed-target FARGAN content bottleneck.

This file intentionally does not implement a long training command yet.  The
dry run validates the data split, the absence of an acoustic residual path,
causality, one backward pass, and deterministic replay on CPU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Iterable

import numpy as np

# The checked-in Anaconda environment loads a second Intel OpenMP runtime when
# numpy precedes torch.  This setting is local to this diagnostic process.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import torch
from torch import nn
from torch.nn import functional as F


ROOT = Path(__file__).resolve().parents[2]
BUDGET = ROOT / "交接" / "核心材料" / "board_budget_20261005"
EXPANDED = BUDGET / "fargan_corpus_expanded" / "manifest.json"
FALLBACK = BUDGET / "fargan_corpus" / "manifest.json"
FEATURE_DIM = 20


@dataclass(frozen=True)
class Pair:
    speaker: str
    source: Path
    teacher: Path


class GradientReverse(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value: torch.Tensor, scale: float) -> torch.Tensor:
        ctx.scale = scale
        return value.view_as(value)

    @staticmethod
    def backward(ctx, gradient: torch.Tensor):
        return -ctx.scale * gradient, None


class CausalContentBottleneck(nn.Module):
    """No source-spectrum residual or source-to-output skip is present."""

    def __init__(self, content_mean: np.ndarray, content_std: np.ndarray,
                 target_profile: np.ndarray, speakers: int, latent_dim: int = 32):
        super().__init__()
        if latent_dim not in (24, 32):
            raise ValueError("latent_dim must be 24 or 32")
        self.register_buffer("content_mean", torch.as_tensor(content_mean, dtype=torch.float32))
        self.register_buffer("content_std", torch.as_tensor(content_std, dtype=torch.float32))
        self.register_buffer("target_profile", torch.as_tensor(target_profile, dtype=torch.float32))
        self.content_pre = nn.Linear(17, 64)
        self.content_gru = nn.GRU(64, 64, batch_first=True)
        self.bottleneck = nn.Linear(64, latent_dim)
        self.target_projection = nn.Linear(40, 16)
        self.decoder_gru = nn.GRU(latent_dim + 4 + 16, 64, batch_first=True)
        self.output = nn.Linear(64, FEATURE_DIM)
        self.speaker_head = nn.Sequential(nn.Linear(latent_dim, 32), nn.Tanh(), nn.Linear(32, speakers))

    def encode(self, spectrum: torch.Tensor) -> torch.Tensor:
        normalized = (spectrum - self.content_mean) / self.content_std
        hidden, _ = self.content_gru(torch.tanh(self.content_pre(normalized)))
        return torch.tanh(self.bottleneck(hidden))

    def decode(self, latent: torch.Tensor, prosody: torch.Tensor) -> torch.Tensor:
        condition = torch.tanh(self.target_projection(self.target_profile))
        condition = condition.view(1, 1, -1).expand(latent.shape[0], latent.shape[1], -1)
        hidden, _ = self.decoder_gru(torch.cat((latent, prosody, condition), dim=-1))
        # Complete 20-D prediction.  There is deliberately no addition of the
        # source spectrum, pitch, energy, or full input frame here.
        return self.output(hidden)

    def forward(self, spectrum: torch.Tensor, prosody: torch.Tensor):
        latent = self.encode(spectrum)
        return self.decode(latent, prosody), latent

    def classify_speaker(self, latent: torch.Tensor, scale: float = 1.0) -> torch.Tensor:
        active_summary = latent.mean(dim=1)
        return self.speaker_head(GradientReverse.apply(active_summary, scale))


def resolve_feature(raw_path: str) -> Path:
    name = PureWindowsPath(raw_path).name
    preferred = "fargan_corpus_expanded" if "fargan_corpus_expanded" in raw_path else "fargan_corpus"
    candidates = [BUDGET / preferred / name, BUDGET / "fargan_corpus_expanded" / name,
                  BUDGET / "fargan_corpus" / name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"cannot resolve feature file {raw_path!r}")


def load_manifest() -> tuple[dict, Path]:
    path = EXPANDED if EXPANDED.is_file() else FALLBACK
    document = json.loads(path.read_text(encoding="utf-8"))
    if not document.get("complete"):
        raise ValueError(f"incomplete manifest: {path}")
    return document, path


def split_pairs(document: dict) -> tuple[list[Pair], list[Pair]]:
    rows = document["files"]
    declared_validation = {row["speaker"] for row in rows if row["split"] == "validation"}
    train_speakers = {row["speaker"] for row in rows if row["split"] == "train"}
    if declared_validation and declared_validation.isdisjoint(train_speakers):
        heldout = declared_validation
    else:
        all_speakers = sorted({row["speaker"] for row in rows})
        heldout = set(all_speakers[-max(1, len(all_speakers) // 10):])
    pairs = [Pair(row["speaker"], resolve_feature(row["source_features"]),
                  resolve_feature(row["teacher_features"])) for row in rows]
    train = [pair for pair in pairs if pair.speaker not in heldout]
    validation = [pair for pair in pairs if pair.speaker in heldout]
    if not train or not validation:
        raise ValueError("speaker-disjoint split is empty")
    if {p.speaker for p in train} & {p.speaker for p in validation}:
        raise AssertionError("speaker leakage across train and validation")
    return train, validation


def read_features(path: Path) -> np.ndarray:
    flat = np.fromfile(path, dtype=np.float32)
    if flat.size % FEATURE_DIM:
        raise ValueError(f"invalid feature length: {path}")
    frames = flat.reshape(-1, FEATURE_DIM)
    if not np.isfinite(frames).all():
        raise ValueError(f"non-finite features: {path}")
    return frames


def causal_prosody(frames: np.ndarray, window: int = 151) -> np.ndarray:
    """Relative energy/F0 and their causal deltas; no raw source periodicity."""
    result = np.zeros((len(frames), 4), dtype=np.float32)
    energy_history: list[float] = []
    pitch_history: list[float] = []
    for index, row in enumerate(frames):
        energy_history.append(float(row[0]))
        del energy_history[:-window]
        voiced = bool(row[19] > 0.05 and row[0] > -7.0)
        if voiced:
            pitch_history.append(float(row[18]))
            del pitch_history[:-window]
        energy_center = float(np.mean(energy_history))
        pitch_center = float(np.median(pitch_history)) if pitch_history else float(row[18])
        energy_delta = float(row[0] - frames[index - 1, 0]) if index else 0.0
        result[index] = (np.clip(row[0] - energy_center, -4.0, 4.0),
                         np.clip(row[18] - pitch_center, -1.5, 1.5) if voiced else 0.0,
                         float(voiced), float(np.clip(energy_delta, -2.0, 2.0)))
    return result


def target_profile(document: dict) -> np.ndarray:
    frames = [read_features(resolve_feature(row["features"])) for row in document["target_training"]]
    pooled = np.concatenate(frames)
    return np.concatenate((pooled.mean(axis=0), np.maximum(pooled.std(axis=0), 1e-3))).astype(np.float32)


def sample_batch(pairs: list[Pair], frames: int = 64, batch_size: int = 4):
    chosen: list[Pair] = []
    for speaker in sorted({pair.speaker for pair in pairs}):
        chosen.append(next(pair for pair in pairs if pair.speaker == speaker))
        if len(chosen) == batch_size:
            break
    if len(chosen) < 2:
        raise ValueError("dry run requires at least two training speakers")
    while len(chosen) < batch_size:
        chosen.append(pairs[len(chosen) % len(pairs)])
    source_batch, teacher_batch, prosody_batch, labels = [], [], [], []
    speaker_ids = {name: index for index, name in enumerate(sorted({p.speaker for p in pairs}))}
    for pair in chosen:
        source, teacher = read_features(pair.source), read_features(pair.teacher)
        length = min(len(source), len(teacher), frames)
        if length < frames:
            raise ValueError(f"dry-run utterance is shorter than {frames} frames: {pair.source}")
        source_batch.append(source[:frames])
        teacher_batch.append(teacher[:frames])
        prosody_batch.append(causal_prosody(source[:frames]))
        labels.append(speaker_ids[pair.speaker])
    tensors = tuple(torch.as_tensor(np.stack(values), dtype=torch.float32)
                    for values in (source_batch, teacher_batch, prosody_batch))
    return (*tensors, torch.tensor(labels, dtype=torch.long), speaker_ids)


def estimate_content_stats(pairs: Iterable[Pair], limit: int = 32) -> tuple[np.ndarray, np.ndarray]:
    spectra = [read_features(pair.source)[:, 1:18] for pair in list(pairs)[:limit]]
    pooled = np.concatenate(spectra)
    return pooled.mean(axis=0).astype(np.float32), np.maximum(pooled.std(axis=0), 0.1).astype(np.float32)


def train_only_statistics(pairs: Iterable[Pair]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Streaming normalization statistics from the training speakers only."""
    content_sum = np.zeros(17, dtype=np.float64)
    content_square = np.zeros(17, dtype=np.float64)
    output_sum = np.zeros(FEATURE_DIM, dtype=np.float64)
    output_square = np.zeros(FEATURE_DIM, dtype=np.float64)
    content_count = output_count = 0
    for pair in pairs:
        source = read_features(pair.source)[:, 1:18].astype(np.float64)
        teacher = read_features(pair.teacher).astype(np.float64)
        content_sum += source.sum(axis=0)
        content_square += np.square(source).sum(axis=0)
        output_sum += teacher.sum(axis=0)
        output_square += np.square(teacher).sum(axis=0)
        content_count += len(source)
        output_count += len(teacher)
    content_mean = content_sum / content_count
    content_std = np.sqrt(np.maximum(content_square / content_count - np.square(content_mean), 0.0))
    output_mean = output_sum / output_count
    output_std = np.sqrt(np.maximum(output_square / output_count - np.square(output_mean), 0.0))
    return (content_mean.astype(np.float32), np.maximum(content_std, 0.1).astype(np.float32),
            np.maximum(output_std, 0.1).astype(np.float32))


def crop_pair(pair: Pair, frames: int, rng: np.random.Generator,
              center: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    source, teacher = read_features(pair.source), read_features(pair.teacher)
    usable = min(len(source), len(teacher))
    if usable < frames:
        raise ValueError(f"pair has {usable} frames, shorter than fixed crop {frames}: {pair.source}")
    start = (usable - frames) // 2 if center else int(rng.integers(usable - frames + 1))
    source_crop = source[start:start + frames]
    teacher_crop = teacher[start:start + frames]
    return source_crop, teacher_crop, causal_prosody(source_crop)


class SpeakerBalancedCropper:
    """Deterministic speaker rotation with random utterance and crop selection."""

    def __init__(self, pairs: list[Pair], frames: int, seed: int):
        eligible = [pair for pair in pairs
                    if min(read_features(pair.source).shape[0], read_features(pair.teacher).shape[0]) >= frames]
        self.by_speaker = {speaker: [pair for pair in eligible if pair.speaker == speaker]
                           for speaker in sorted({pair.speaker for pair in eligible})}
        if len(self.by_speaker) < 2:
            raise ValueError("training requires at least two speakers with a full fixed crop")
        self.frames = frames
        self.rng = np.random.default_rng(seed)
        self.queue: list[str] = []

    def _speaker(self) -> str:
        if not self.queue:
            names = np.asarray(sorted(self.by_speaker), dtype=object)
            self.queue = self.rng.permutation(names).tolist()
        return self.queue.pop()

    def batch(self, size: int):
        source, teacher, prosody, speakers = [], [], [], []
        for _ in range(size):
            speaker = self._speaker()
            rows = self.by_speaker[speaker]
            pair = rows[int(self.rng.integers(len(rows)))]
            x, y, rhythm = crop_pair(pair, self.frames, self.rng)
            source.append(x); teacher.append(y); prosody.append(rhythm); speakers.append(speaker)
        tensors = tuple(torch.as_tensor(np.stack(values), dtype=torch.float32)
                        for values in (source, teacher, prosody))
        return (*tensors, speakers)


def loss_terms(model: CausalContentBottleneck, source: torch.Tensor, teacher: torch.Tensor,
               prosody: torch.Tensor, output_std: torch.Tensor,
               labels: torch.Tensor | None = None) -> tuple[torch.Tensor, dict[str, float]]:
    prediction, source_latent = model(source[..., 1:18], prosody)
    teacher_latent = model.encode(teacher[..., 1:18])
    reconstruction = F.smooth_l1_loss((prediction - teacher) / output_std, torch.zeros_like(teacher))
    latent_consistency = F.smooth_l1_loss(source_latent, teacher_latent.detach())
    delta = F.l1_loss((prediction[:, 1:] - prediction[:, :-1]) / output_std,
                      (teacher[:, 1:] - teacher[:, :-1]) / output_std)
    speaker = prediction.sum() * 0.0
    if labels is not None:
        speaker = F.cross_entropy(model.classify_speaker(source_latent), labels)
    total = reconstruction + 0.5 * latent_consistency + 0.1 * delta + 0.1 * speaker
    metrics = {"total": float(total.detach()), "reconstruction": float(reconstruction.detach()),
               "latent_consistency": float(latent_consistency.detach()), "delta": float(delta.detach()),
               "speaker_adversary": float(speaker.detach())}
    return total, metrics


def one_pass(seed: int, content_mean: np.ndarray, content_std: np.ndarray,
             profile: np.ndarray, source: torch.Tensor, teacher: torch.Tensor,
             prosody: torch.Tensor, labels: torch.Tensor, speaker_count: int,
             latent_dim: int):
    torch.manual_seed(seed)
    model = CausalContentBottleneck(content_mean, content_std, profile, speaker_count, latent_dim)
    output_std = torch.ones(FEATURE_DIM)
    loss, metrics = loss_terms(model, source, teacher, prosody, output_std, labels)
    loss.backward()
    gradients = torch.cat([parameter.grad.flatten() for parameter in model.parameters()
                           if parameter.grad is not None])
    with torch.inference_mode():
        prediction, _ = model(source[..., 1:18], prosody)
    return model, prediction.detach(), gradients.detach(), metrics


def verify_causality(model: CausalContentBottleneck, source: torch.Tensor,
                     prosody: torch.Tensor, boundary: int = 31) -> float:
    altered_source, altered_prosody = source.clone(), prosody.clone()
    altered_source[:, boundary + 1:] += 7.0
    altered_prosody[:, boundary + 1:] -= 3.0
    with torch.inference_mode():
        before, _ = model(source[..., 1:18], prosody)
        after, _ = model(altered_source[..., 1:18], altered_prosody)
    return float((before[:, :boundary + 1] - after[:, :boundary + 1]).abs().max())


def validation_loss(model: CausalContentBottleneck, pairs: list[Pair], frames: int,
                    output_std: torch.Tensor, device: torch.device) -> dict[str, float]:
    rows: list[dict[str, float]] = []
    rng = np.random.default_rng(0)
    model.eval()
    with torch.inference_mode():
        for pair in pairs:
            source, teacher, prosody = crop_pair(pair, frames, rng, center=True)
            tensors = [torch.as_tensor(value[None], dtype=torch.float32, device=device)
                       for value in (source, teacher, prosody)]
            _, metrics = loss_terms(model, *tensors, output_std, labels=None)
            rows.append(metrics)
    return {name: float(np.mean([row[name] for row in rows])) for name in rows[0]}


def checkpoint_payload(model: CausalContentBottleneck, optimizer: torch.optim.Optimizer,
                       manifest_path: Path, train: list[Pair], validation: list[Pair],
                       config: dict, history: list[dict], epoch: int,
                       normalization: dict, speaker_ids: dict[str, int]) -> dict:
    return {
        "format": "causal_content_bottleneck_v1",
        "epoch": epoch,
        "manifest": str(manifest_path),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "split": {
            "train_speakers": sorted({pair.speaker for pair in train}),
            "validation_speakers": sorted({pair.speaker for pair in validation}),
            "train_pairs": len(train), "validation_pairs": len(validation),
        },
        "config": config,
        "normalization": normalization,
        "speaker_ids": speaker_ids,
        "history": history,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
    }


def run_training(args: argparse.Namespace) -> dict:
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if device.type == "cpu":
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
    document, manifest_path = load_manifest()
    train, validation = split_pairs(document)
    mean, std, output_scale = train_only_statistics(train)
    profile = target_profile(document)
    speaker_ids = {name: index for index, name in enumerate(sorted({p.speaker for p in train}))}
    model = CausalContentBottleneck(mean, std, profile, len(speaker_ids), args.latent_dim).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    cropper = SpeakerBalancedCropper(train, args.crop_frames, args.seed)
    output_std = torch.as_tensor(output_scale, dtype=torch.float32, device=device)
    config = {"seed": args.seed, "latent_dim": args.latent_dim, "crop_frames": args.crop_frames,
              "batch_size": args.batch_size, "epochs": args.epochs,
              "steps_per_epoch": args.steps_per_epoch, "learning_rate": args.learning_rate,
              "patience": args.patience, "min_delta": args.min_delta, "device": args.device,
              "speaker_balanced": True, "fixed_crop_no_padding": True}
    normalization = {"content_mean": mean.tolist(), "content_std": std.tolist(),
                     "output_std": output_scale.tolist(), "target_profile": profile.tolist(),
                     "estimated_from_train_speakers_only": True}
    history: list[dict] = []
    best = float("inf")
    stale = 0
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, args.epochs + 1):
        model.train()
        train_rows = []
        for _ in range(args.steps_per_epoch):
            source, teacher, prosody, names = cropper.batch(args.batch_size)
            source, teacher, prosody = (value.to(device) for value in (source, teacher, prosody))
            labels = torch.tensor([speaker_ids[name] for name in names], dtype=torch.long, device=device)
            loss, metrics = loss_terms(model, source, teacher, prosody, output_std, labels)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_rows.append(metrics)
        train_metrics = {name: float(np.mean([row[name] for row in train_rows]))
                         for name in train_rows[0]}
        valid_metrics = validation_loss(model, validation, args.crop_frames, output_std, device)
        row = {"epoch": epoch, "train": train_metrics, "validation": valid_metrics}
        history.append(row)
        if valid_metrics["total"] < best - args.min_delta:
            best = valid_metrics["total"]
            stale = 0
            torch.save(checkpoint_payload(model, optimizer, manifest_path, train, validation,
                                          config, history, epoch, normalization, speaker_ids), output)
        else:
            stale += 1
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if stale >= args.patience:
            break
    return {"training": True, "epochs_completed": len(history),
            "steps_completed": len(history) * args.steps_per_epoch,
            "best_validation_total": best, "checkpoint": str(output),
            "checkpoint_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "early_stopped": stale >= args.patience}


def dry_run(latent_dim: int) -> dict:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    document, manifest_path = load_manifest()
    train, validation = split_pairs(document)
    mean, std = estimate_content_stats(train)
    profile = target_profile(document)
    source, teacher, prosody, labels, speaker_ids = sample_batch(train)
    first = one_pass(20261018, mean, std, profile, source, teacher, prosody,
                     labels, len(speaker_ids), latent_dim)
    second = one_pass(20261018, mean, std, profile, source, teacher, prosody,
                      labels, len(speaker_ids), latent_dim)
    output_difference = float((first[1] - second[1]).abs().max())
    gradient_difference = float((first[2] - second[2]).abs().max())
    causal_difference = verify_causality(first[0], source, prosody)
    if output_difference != 0.0 or gradient_difference != 0.0:
        raise AssertionError("fixed-seed forward/backward replay is not deterministic")
    if causal_difference > 1e-7:
        raise AssertionError(f"future frames affected the prefix: {causal_difference}")
    return {
        "dry_run": True,
        "manifest": str(manifest_path),
        "train_pairs": len(train),
        "validation_pairs": len(validation),
        "train_speakers": sorted({pair.speaker for pair in train}),
        "heldout_speakers": sorted({pair.speaker for pair in validation}),
        "batch_shapes": {"source": list(source.shape), "teacher": list(teacher.shape),
                         "prosody": list(prosody.shape)},
        "latent_dim": latent_dim,
        "parameters": sum(parameter.numel() for parameter in first[0].parameters()),
        "loss": first[3],
        "causal_prefix_max_abs": causal_difference,
        "deterministic_output_max_abs": output_difference,
        "deterministic_gradient_max_abs": gradient_difference,
        "long_training_started": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="validate one deterministic CPU step")
    parser.add_argument("--train", action="store_true", help="run the explicit bounded training loop")
    parser.add_argument("--latent-dim", type=int, choices=(24, 32), default=32)
    parser.add_argument("--json", type=Path, help="optional run-summary JSON path")
    parser.add_argument("--seed", type=int, default=20261018)
    parser.add_argument("--crop-frames", type=int, default=160)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--steps-per-epoch", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--min-delta", type=float, default=1e-4)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--output", default=str(ROOT / "build" / "generated" /
                                                  "quality_exploration_20261018" /
                                                  "causal_content_bottleneck_best.pt"))
    args = parser.parse_args()
    if args.dry_run == args.train:
        parser.error("select exactly one of --dry-run or --train")
    result = dry_run(args.latent_dim) if args.dry_run else run_training(args)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
