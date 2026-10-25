"""HuBERT-content kNN retrieval of real target WORLD frames (Round 21)."""
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


K = 4
SEED = 20261025


def at_content_rate(world_output: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(world_output), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, world_output[:, column])
                     for column in range(world_output.shape[1])], axis=1).astype(np.float32)


def at_world_rate(content_output: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(content_output), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, content_output[:, column])
                     for column in range(content_output.shape[1])], axis=1).astype(np.float32)


def query_knn(query: np.ndarray, library: np.ndarray, values: np.ndarray,
              batch: int = 128) -> tuple[np.ndarray, dict]:
    outputs = []
    nearest = []
    library_norm = np.sum(library * library, axis=1)
    for start in range(0, len(query), batch):
        part = query[start:start + batch]
        distance = (np.sum(part * part, axis=1, keepdims=True) + library_norm[None]
                    - 2.0 * part @ library.T)
        indices = np.argpartition(distance, K - 1, axis=1)[:, :K]
        selected_distance = np.take_along_axis(distance, indices, axis=1)
        order = np.argsort(selected_distance, axis=1)
        indices = np.take_along_axis(indices, order, axis=1)
        selected_distance = np.take_along_axis(selected_distance, order, axis=1)
        scale = np.maximum(np.median(selected_distance, axis=1, keepdims=True), 1e-4)
        weights = np.exp(-selected_distance / scale)
        weights /= weights.sum(axis=1, keepdims=True)
        outputs.append(np.sum(values[indices] * weights[..., None], axis=1))
        nearest.append(selected_distance[:, 0])
    return np.concatenate(outputs).astype(np.float32), {
        "nearest_squared_distance_mean": float(np.mean(np.concatenate(nearest))),
        "nearest_squared_distance_p90": float(np.percentile(np.concatenate(nearest), 90)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round21_20261025")
    args = parser.parse_args()
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})

    target_dir = args.asset_root / "人物音频资料/女声"
    hubert_dir = args.asset_root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    model = base.HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    rows = {}
    for number in (5, 6, 7, 8):
        path = target_dir / f"Track {number}.wav"
        signal = base.read_16k(path)
        content = base.extract_hubert(model, signal)
        world = base.analyze_world(signal)
        rows[number] = {"content": content, "world": world}
        print(json.dumps({"track": number, "content_frames": len(content),
                          "world_frames": len(world["output"])}), flush=True)

    mean, projection = base.pca_fit([rows[number]["content"] for number in rows])
    projected = [(rows[number]["content"] - mean) @ projection for number in rows]
    library = np.concatenate(projected).astype(np.float32)
    feature_mean = library.mean(axis=0)
    feature_std = np.maximum(library.std(axis=0), 0.05)
    library = (library - feature_mean) / feature_std
    values = np.concatenate([at_content_rate(rows[number]["world"]["output"],
                                             len(rows[number]["content"]))
                             for number in rows])

    heldout_path = target_dir / "Track 9.wav"
    heldout_signal = base.read_16k(heldout_path)
    heldout_content = base.extract_hubert(model, heldout_signal)
    heldout_world = base.analyze_world(heldout_signal)
    query = ((heldout_content - mean) @ projection - feature_mean) / feature_std
    retrieved, distance = query_knn(query.astype(np.float32), library, values)
    prediction = at_world_rate(retrieved, len(heldout_world["output"]))

    train_output = np.concatenate([rows[number]["world"]["output"] for number in rows])
    clip_lo = np.percentile(train_output, 0.1, axis=0)
    clip_hi = np.percentile(train_output, 99.9, axis=0)
    prediction = np.clip(prediction, clip_lo, clip_hi)
    vuv_probability = prediction[:, base.SP_DIM + 1].copy()
    prediction[:, base.SP_DIM + 1] = (vuv_probability - 0.5) * 8.0
    voiced = train_output[:, base.SP_DIM + 1] > 0.5
    log_f0 = train_output[voiced, base.SP_DIM]
    log_sp = np.log(np.maximum(np.concatenate(
        [rows[number]["world"]["spectrum"] for number in rows]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(log_f0, 0.5)),
             "log_f0_hi": float(np.percentile(log_f0, 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}
    reconstructed, synthesis = base.synthesize(prediction, stats)
    wav_path = args.output / "track9_hubert_world_knn.wav"
    base.sf.write(wav_path, reconstructed, base.SAMPLE_RATE, subtype="PCM_16")
    truth = heldout_world["output"]
    mae = np.mean(np.abs(prediction - truth), axis=0)
    summary = {
        "task": "PS-20261021-10", "round": 21,
        "kind": "hubert_content_knn_target_world_retrieval", "k": K,
        "train_tracks": [5, 6, 7, 8], "development_track": 9,
        "track9_already_exposed_in_round20": True,
        "source_audio_used": False, "source_spectrum_skip": False,
        "hubert_checkpoint_sha256": base.sha256(hubert_dir / "pytorch_model.bin"),
        "library_frames": len(library), "query_frames": len(query),
        "distance": distance, "synthesis": synthesis,
        "mae": {"spectrum_dct_mean": float(mae[:base.SP_DIM].mean()),
                "log_f0": float(mae[base.SP_DIM]),
                "vuv_probability": float(np.mean(np.abs(
                    vuv_probability - truth[:, base.SP_DIM + 1]))),
                "energy": float(mae[base.SP_DIM + 2]),
                "aperiodicity_dct_mean": float(mae[base.SP_DIM + 3:].mean())},
        "reconstruction_sha256": base.sha256(wav_path),
        "elapsed_seconds": time.monotonic() - started,
        "board_touched": False, "played": False,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"inputs": [{"role": "source", "path": "人物音频资料/女声/Track 9.wav"}],
                "outputs": [{"candidate": "track9_hubert_world_knn",
                             "path": "build/generated/hubert_world_round21_20261025/track9_hubert_world_knn.wav"}]}
    (args.output / "strict_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
