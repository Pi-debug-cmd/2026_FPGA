"""Path-level HuBERT retrieval of target WORLD frames (Round 22)."""
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


CANDIDATES = 32
PENALTIES = (0.0, 0.10, 0.25, 0.50, 1.00)
DELTA_WEIGHT = 0.25


def resample_rows(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def build_library(rows: dict[int, dict], train_numbers: tuple[int, ...]) -> dict:
    mean, projection = base.pca_fit([rows[number]["content"] for number in train_numbers])
    projected = [(rows[number]["content"] - mean) @ projection for number in train_numbers]
    pooled = np.concatenate(projected).astype(np.float32)
    feature_mean = pooled.mean(axis=0)
    feature_std = np.maximum(pooled.std(axis=0), 0.05)
    features, values, tracks, frames = [], [], [], []
    for number, item in zip(train_numbers, projected):
        features.append((item - feature_mean) / feature_std)
        values.append(resample_rows(rows[number]["world"]["output"], len(item)))
        tracks.append(np.full(len(item), number, dtype=np.int16))
        frames.append(np.arange(len(item), dtype=np.int32))
    return {"mean": mean, "projection": projection, "feature_mean": feature_mean,
            "feature_std": feature_std, "features": np.concatenate(features),
            "values": np.concatenate(values), "tracks": np.concatenate(tracks),
            "frames": np.concatenate(frames)}


def nearest_candidates(query: np.ndarray, library: np.ndarray,
                       batch: int = 128) -> tuple[np.ndarray, np.ndarray]:
    all_indices, all_distances = [], []
    library_norm = np.sum(library * library, axis=1)
    for start in range(0, len(query), batch):
        part = query[start:start + batch]
        distance = (np.sum(part * part, axis=1, keepdims=True) + library_norm[None]
                    - 2.0 * part @ library.T)
        indices = np.argpartition(distance, CANDIDATES - 1, axis=1)[:, :CANDIDATES]
        selected = np.take_along_axis(distance, indices, axis=1)
        order = np.argsort(selected, axis=1)
        all_indices.append(np.take_along_axis(indices, order, axis=1))
        all_distances.append(np.take_along_axis(selected, order, axis=1))
    return np.concatenate(all_indices), np.concatenate(all_distances)


def decode_path(indices: np.ndarray, distances: np.ndarray, tracks: np.ndarray,
                frames: np.ndarray, jump_penalty: float) -> tuple[np.ndarray, dict]:
    scale = max(float(np.median(distances[:, 0])), 1e-4)
    emission = distances / scale
    costs = emission[0].copy()
    back = np.zeros(indices.shape, dtype=np.int16)
    for time_index in range(1, len(indices)):
        previous = indices[time_index - 1]
        current = indices[time_index]
        same_track = tracks[previous][:, None] == tracks[current][None, :]
        delta = frames[current][None, :] - frames[previous][:, None]
        sequential = same_track & (delta >= 0) & (delta <= 3)
        transition = np.where(sequential, 0.02 * np.abs(delta - 1), jump_penalty)
        total = costs[:, None] + transition
        choice = np.argmin(total, axis=0)
        back[time_index] = choice
        costs = emission[time_index] + total[choice, np.arange(CANDIDATES)]
    states = np.empty(len(indices), dtype=np.int16)
    states[-1] = int(np.argmin(costs))
    for time_index in range(len(indices) - 1, 0, -1):
        states[time_index - 1] = back[time_index, states[time_index]]
    path = indices[np.arange(len(indices)), states]
    same = tracks[path[1:]] == tracks[path[:-1]]
    delta = frames[path[1:]] - frames[path[:-1]]
    sequential = same & (delta >= 0) & (delta <= 3)
    return path, {"jump_rate": float(np.mean(~sequential)),
                  "exact_next_rate": float(np.mean(same & (delta == 1))),
                  "emission_mean": float(np.mean(
                      distances[np.arange(len(indices)), states] / scale))}


def retrieve(rows: dict[int, dict], train_numbers: tuple[int, ...],
             query_number: int, penalty: float) -> tuple[np.ndarray, dict]:
    library = build_library(rows, train_numbers)
    query_content = rows[query_number]["content"]
    query = ((query_content - library["mean"]) @ library["projection"]
             - library["feature_mean"]) / library["feature_std"]
    indices, distances = nearest_candidates(query.astype(np.float32), library["features"])
    path, diagnostics = decode_path(indices, distances, library["tracks"],
                                    library["frames"], penalty)
    result = library["values"][path].copy()
    # A single-frame blend only at forced jumps avoids hard parameter steps
    # without smoothing the interiors of consonants or vowels.
    path_track = library["tracks"][path]
    path_frame = library["frames"][path]
    sequential = ((path_track[1:] == path_track[:-1])
                  & (path_frame[1:] - path_frame[:-1] >= 0)
                  & (path_frame[1:] - path_frame[:-1] <= 3))
    jumps = np.flatnonzero(~sequential) + 1
    for index in jumps:
        result[index] = 0.5 * result[index - 1] + 0.5 * result[index]
    diagnostics.update({"penalty": penalty, "candidate_count": CANDIDATES,
                        "jump_blend_frames": 1, "path_frames": len(path)})
    return result, diagnostics


def cross_validation(rows: dict[int, dict]) -> tuple[float, list[dict]]:
    records = []
    for penalty in PENALTIES:
        folds = []
        for validation in sorted(rows):
            training = tuple(number for number in sorted(rows) if number != validation)
            prediction, diagnostic = retrieve(rows, training, validation, penalty)
            truth = resample_rows(rows[validation]["world"]["output"], len(prediction))
            pooled = np.concatenate([resample_rows(rows[number]["world"]["output"],
                                                   len(rows[number]["content"]))
                                     for number in training])
            scale = np.maximum(pooled.std(axis=0), 0.1)
            frame_mae = float(np.mean(np.abs(prediction - truth) / scale))
            delta_mae = float(np.mean(np.abs(np.diff(prediction, axis=0)
                                             - np.diff(truth, axis=0)) / scale))
            score = frame_mae + DELTA_WEIGHT * delta_mae
            folds.append({"validation_track": validation, "frame_mae": frame_mae,
                          "delta_mae": delta_mae, "score": score, **diagnostic})
        records.append({"penalty": penalty,
                        "mean_score": float(np.mean([fold["score"] for fold in folds])),
                        "mean_jump_rate": float(np.mean([fold["jump_rate"] for fold in folds])),
                        "folds": folds})
        print(json.dumps(records[-1], ensure_ascii=False), flush=True)
    selected = min(records, key=lambda item: (item["mean_score"], item["penalty"]))
    return float(selected["penalty"]), records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round22_20261025")
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
        signal = base.read_16k(target_dir / f"Track {number}.wav")
        rows[number] = {"content": base.extract_hubert(model, signal),
                        "world": base.analyze_world(signal)}
        print(json.dumps({"track": number, "content_frames": len(rows[number]["content"])},
                         ensure_ascii=False), flush=True)
    selected_penalty, validation = cross_validation(rows)

    signal = base.read_16k(target_dir / "Track 9.wav")
    rows[9] = {"content": base.extract_hubert(model, signal), "world": base.analyze_world(signal)}
    del model
    retrieved, path = retrieve(rows, (5, 6, 7, 8), 9, selected_penalty)
    prediction = resample_rows(retrieved, len(rows[9]["world"]["output"]))
    train_output = np.concatenate([rows[number]["world"]["output"] for number in (5, 6, 7, 8)])
    prediction = np.clip(prediction, np.percentile(train_output, 0.1, axis=0),
                         np.percentile(train_output, 99.9, axis=0))
    vuv_probability = prediction[:, base.SP_DIM + 1].copy()
    prediction[:, base.SP_DIM + 1] = (vuv_probability - 0.5) * 8.0
    voiced = train_output[:, base.SP_DIM + 1] > 0.5
    log_sp = np.log(np.maximum(np.concatenate(
        [rows[number]["world"]["spectrum"] for number in (5, 6, 7, 8)]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(train_output[voiced, base.SP_DIM], 0.5)),
             "log_f0_hi": float(np.percentile(train_output[voiced, base.SP_DIM], 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}
    reconstructed, synthesis = base.synthesize(prediction, stats)
    wav_path = args.output / "track9_hubert_world_path.wav"
    base.sf.write(wav_path, reconstructed, base.SAMPLE_RATE, subtype="PCM_16")
    summary = {"task": "PS-20261021-10", "round": 22,
               "kind": "hubert_world_viterbi_path_retrieval",
               "selection_data": "leave-one-track-out on Tracks 5-8 only",
               "development_track": 9, "track9_already_exposed": True,
               "selected_penalty": selected_penalty, "cross_validation": validation,
               "path": path, "synthesis": synthesis,
               "reconstruction_sha256": base.sha256(wav_path),
               "elapsed_seconds": time.monotonic() - started,
               "source_audio_used": False, "source_spectrum_skip": False,
               "played": False, "board_touched": False}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"inputs": [{"role": "source", "path": "人物音频资料/女声/Track 9.wav"}],
                "outputs": [{"candidate": "track9_hubert_world_path",
                             "path": "build/generated/hubert_world_round22_20261025/track9_hubert_world_path.wav"}]}
    (args.output / "strict_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
