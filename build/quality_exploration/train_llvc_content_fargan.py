"""Train a small causal mapper from LLVC content features to target FARGAN features.

This is an offline PS-candidate screen.  It reuses frozen content features and
does not touch the board, Vivado, or the DSH realtime path.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "build/generated/a3_neural"))
import a3_bootstrap  # noqa: E402,F401  # adds the isolated local dependencies

import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from torch import nn  # noqa: E402

SEED = 20261019
PAST = 8
PCA_DIM = 64
HIDDEN = 192
STEPS = 2400
BATCH = 2048
VAL_SPEAKERS = {"SSB0043", "SSB0394"}

A3 = ROOT / "build/generated/a3_neural"
CORPUS = ROOT / "交接/核心材料/board_budget_20261005/fargan_corpus_expanded"
NATIVE = ROOT / "交接/核心材料/board_support/native_llvc_20261005"
OUT = ROOT / "build/generated/quality_exploration_20261019/llvc_content_fargan_v1"


def causal_context(x: np.ndarray) -> np.ndarray:
    padded = np.pad(x, ((PAST, 0), (0, 0)), mode="edge")
    return np.concatenate([padded[i:i + len(x)] for i in range(PAST + 1)], axis=1)


class Mapper(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(PCA_DIM * (PAST + 1), HIDDEN), nn.ReLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.ReLU(),
            nn.Linear(HIDDEN, 20),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def load_rows() -> list[dict]:
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    return [row for row in manifest["files"]
            if (A3 / "dataset_content" / (row["filename"] + ".npz")).is_file()]


def build_row(row: dict, mean: np.ndarray, projection: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    content = np.load(A3 / "dataset_content" / (row["filename"] + ".npz"))["content"].astype(np.float32)
    content = (content - mean) @ projection
    target = np.fromfile(CORPUS / f'{Path(row["filename"]).stem}_teacher.features.f32',
                         dtype=np.float32).reshape(-1, 20)
    count = min(len(content), len(target))
    return causal_context(content[:count]).astype(np.float32), target[:count].astype(np.float32)


def synthesize(name: str, features: np.ndarray) -> Path:
    feature_path = OUT / f"{name}.features.f32"
    pcm_path = OUT / f"{name}.pcm"
    json_path = OUT / f"{name}.synthesis.json"
    wav_path = OUT / f"{name}.wav"
    features.astype(np.float32).tofile(feature_path)
    subprocess.run([str(NATIVE / "fargan_probe_host.exe"), "--synthesis",
                    str(feature_path), str(pcm_path), str(json_path)], check=True)
    pcm = np.fromfile(pcm_path, dtype="<i2").astype(np.float32) / 32768.0
    sf.write(wav_path, pcm, 16000, subtype="PCM_16")
    return wav_path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)

    pca = np.load(A3 / "content_pca.npz")
    mean = pca["mean"].astype(np.float32)
    projection = pca["proj"][:, :PCA_DIM].astype(np.float32)
    rows = load_rows()
    train_rows = [row for row in rows if row["speaker"] not in VAL_SPEAKERS]
    valid_rows = [row for row in rows if row["speaker"] in VAL_SPEAKERS]
    if not train_rows or not valid_rows:
        raise RuntimeError("speaker-disjoint train/validation split is empty")

    train_pairs = [build_row(row, mean, projection) for row in train_rows]
    valid_pairs = [build_row(row, mean, projection) for row in valid_rows]
    train_x = np.concatenate([pair[0] for pair in train_pairs])
    train_y = np.concatenate([pair[1] for pair in train_pairs])
    valid_x = np.concatenate([pair[0] for pair in valid_pairs])
    valid_y = np.concatenate([pair[1] for pair in valid_pairs])

    y_mean = train_y.mean(axis=0)
    y_std = np.maximum(train_y.std(axis=0), 0.05)
    train_z = (train_y - y_mean) / y_std
    valid_z = (valid_y - y_mean) / y_std
    clip_lo = np.percentile(train_y, 0.25, axis=0).astype(np.float32)
    clip_hi = np.percentile(train_y, 99.75, axis=0).astype(np.float32)

    model = Mapper()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.2e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, STEPS)
    history = []
    best = None
    for step in range(1, STEPS + 1):
        index = rng.integers(0, len(train_x), size=BATCH)
        x = torch.from_numpy(train_x[index])
        target = torch.from_numpy(train_z[index])
        prediction = model(x)
        loss = torch.nn.functional.smooth_l1_loss(prediction, target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        scheduler.step()
        if step == 1 or step % 200 == 0:
            with torch.inference_mode():
                predicted = model(torch.from_numpy(valid_x))
                val_loss = torch.nn.functional.smooth_l1_loss(
                    predicted, torch.from_numpy(valid_z)).item()
            record = {"step": step, "train_loss": float(loss.item()), "val_loss": val_loss}
            history.append(record)
            print(json.dumps(record), flush=True)
            if best is None or val_loss < best["val_loss"]:
                best = record | {"state": {key: value.detach().clone()
                                            for key, value in model.state_dict().items()}}

    assert best is not None
    model.load_state_dict(best.pop("state"))
    with torch.inference_mode():
        val_prediction = model(torch.from_numpy(valid_x)).numpy() * y_std + y_mean
    val_prediction = np.clip(val_prediction, clip_lo, clip_hi)
    mae = np.mean(np.abs(val_prediction - valid_y), axis=0)
    baseline_mae = np.mean(np.abs(valid_y - y_mean), axis=0)

    outputs = []
    for row, (x, target) in list(zip(valid_rows, valid_pairs))[:4]:
        with torch.inference_mode():
            prediction = model(torch.from_numpy(x)).numpy() * y_std + y_mean
        prediction = np.clip(prediction, clip_lo, clip_hi)
        stem = Path(row["filename"]).stem
        candidate = synthesize(stem + "_candidate", prediction)
        teacher = synthesize(stem + "_teacher_oracle", target)
        outputs.append({"file": row["filename"], "speaker": row["speaker"],
                        "candidate": str(candidate.relative_to(ROOT)).replace("\\", "/"),
                        "teacher_oracle": str(teacher.relative_to(ROOT)).replace("\\", "/")})

    checkpoint = OUT / "mapper.pt"
    torch.save({"state_dict": model.state_dict(), "past_frames": PAST,
                "pca_mean": mean, "pca_projection": projection,
                "target_mean": y_mean, "target_std": y_std,
                "clip_lo": clip_lo, "clip_hi": clip_hi}, checkpoint)
    report = {
        "kind": "llvc_content_to_fargan_ps_candidate_v1",
        "seed": SEED,
        "causal": True,
        "lookback_frames": PAST,
        "algorithmic_lookback_ms": PAST * 10,
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "train_speakers": len({row["speaker"] for row in train_rows}),
        "validation_speakers": sorted(VAL_SPEAKERS),
        "train_frames": len(train_x),
        "validation_frames": len(valid_x),
        "best": best,
        "mean_absolute_error_by_feature": mae.tolist(),
        "constant_baseline_mae_by_feature": baseline_mae.tolist(),
        "mean_mae_ratio_to_constant": float(np.mean(mae / np.maximum(baseline_mae, 1e-6))),
        "outputs": outputs,
        "quality_accepted": False,
        "board_deployed": False,
        "pl_work_started": False,
        "history": history,
    }
    (OUT / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("parameters", "train_frames", "validation_frames",
                       "mean_mae_ratio_to_constant")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
