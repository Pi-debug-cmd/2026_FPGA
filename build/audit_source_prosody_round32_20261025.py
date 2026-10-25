"""Preflight explicit source prosody for the paired HuBERT-to-WORLD route."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import numpy as np  # noqa: E402


def resolve(root: Path, subdirectory: str, raw: str) -> Path:
    path = root / subdirectory / PureWindowsPath(raw).name
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def read_raw(path: Path) -> np.ndarray:
    signal = np.fromfile(path, dtype="<f4").astype(np.float64)
    if not len(signal) or not np.isfinite(signal).all() or float(np.max(np.abs(signal))) == 0.0:
        raise ValueError(f"invalid raw waveform: {path}")
    return signal


def resample_rows(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def source_prosody(signal: np.ndarray) -> np.ndarray:
    f0, times = base.pyworld.harvest(signal, base.SAMPLE_RATE,
                                     frame_period=base.FRAME_PERIOD_MS,
                                     f0_floor=55.0, f0_ceil=500.0)
    f0 = base.pyworld.stonemask(signal, f0, times, base.SAMPLE_RATE)
    spectrum = base.pyworld.cheaptrick(signal, f0, times, base.SAMPLE_RATE, fft_size=1024)
    log_f0, voiced = base.continuous_log_f0(f0)
    energy = np.log(np.maximum(spectrum, 1e-8)).mean(axis=1)
    result = np.stack((log_f0, voiced, energy), axis=1)
    if not np.isfinite(result).all():
        raise ValueError("non-finite source prosody")
    return result.astype(np.float32)


def correlation(left: np.ndarray, right: np.ndarray) -> float | None:
    if len(left) < 3 or float(np.std(left)) < 1e-8 or float(np.std(right)) < 1e-8:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round32_20261025")
    args = parser.parse_args()
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    corpus = args.asset_root / "交接/核心材料/board_budget_20261005/full_train_corpus_16k"
    declaration = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    cache_root = ROOT / "build/generated/hubert_world_round25_20261025"
    cache_manifest_path = cache_root / "cache_manifest.json"
    cache_manifest = json.loads(cache_manifest_path.read_text(encoding="utf-8"))
    declared = {row["stem"]: (split, row) for split in ("train", "validation")
                for row in declaration[split]}
    if set(declared) != {row["stem"] for row in cache_manifest["records"]}:
        raise ValueError("Round 25 cache and paired declaration differ")

    rows = []
    pooled = {"source_f0": [], "target_f0": [], "source_df0": [], "target_df0": [],
              "source_energy": [], "target_energy": []}
    vuv_true_positive = vuv_false_positive = vuv_false_negative = vuv_equal = vuv_total = 0
    for index, record in enumerate(cache_manifest["records"], 1):
        split, declaration_row = declared[record["stem"]]
        if split != record["split"]:
            raise ValueError(f"split mismatch: {record['stem']}")
        source_path = resolve(corpus, "src", declaration_row["src"])
        source_sha = base.sha256(source_path)
        if source_sha != declaration_row["src_sha"] or source_sha != record["source_sha256"]:
            raise ValueError(f"source SHA mismatch: {record['stem']}")
        source = read_raw(source_path)
        target = np.load(cache_root / "cache" / record["cache"])["target"].astype(np.float32)
        prosody = resample_rows(source_prosody(source), len(target))
        source_voiced = prosody[:, 1] >= 0.5
        target_voiced = target[:, base.SP_DIM + 1] >= 0.5
        joint = source_voiced & target_voiced
        if not source_voiced.any() or not target_voiced.any() or int(joint.sum()) < 3:
            raise ValueError(f"insufficient voiced overlap: {record['stem']}")

        source_f0 = prosody[:, 0] - np.median(prosody[source_voiced, 0])
        target_f0 = target[:, base.SP_DIM] - np.median(target[target_voiced, base.SP_DIM])
        pooled["source_f0"].append(source_f0[joint]); pooled["target_f0"].append(target_f0[joint])
        adjacent = joint[1:] & joint[:-1]
        pooled["source_df0"].append(np.diff(source_f0)[adjacent])
        pooled["target_df0"].append(np.diff(target_f0)[adjacent])

        source_energy = (prosody[:, 2] - prosody[:, 2].mean()) / max(prosody[:, 2].std(), 1e-6)
        target_energy_raw = target[:, base.SP_DIM + 2]
        target_energy = (target_energy_raw - target_energy_raw.mean()) / max(target_energy_raw.std(), 1e-6)
        pooled["source_energy"].append(source_energy)
        pooled["target_energy"].append(target_energy)

        vuv_true_positive += int(np.sum(source_voiced & target_voiced))
        vuv_false_positive += int(np.sum(source_voiced & ~target_voiced))
        vuv_false_negative += int(np.sum(~source_voiced & target_voiced))
        vuv_equal += int(np.sum(source_voiced == target_voiced)); vuv_total += len(target)
        rows.append({"stem": record["stem"], "split": split, "speaker": record["speaker"],
                     "frames": len(target), "source_voiced_fraction": float(source_voiced.mean()),
                     "target_voiced_fraction": float(target_voiced.mean()),
                     "joint_voiced_frames": int(joint.sum()),
                     "centered_log_f0_correlation": correlation(source_f0[joint], target_f0[joint]),
                     "delta_log_f0_correlation": correlation(np.diff(source_f0)[adjacent],
                                                               np.diff(target_f0)[adjacent]),
                     "normalized_energy_correlation": correlation(source_energy, target_energy)})
        if index == 1 or index % 20 == 0 or index == len(cache_manifest["records"]):
            print(json.dumps({"processed": index, "total": len(cache_manifest["records"]),
                              "stem": record["stem"]}), flush=True)

    pooled_values = {key: np.concatenate(value) for key, value in pooled.items()}
    f1_denominator = 2 * vuv_true_positive + vuv_false_positive + vuv_false_negative
    current_parameters = 477771
    added_parameters = 3 * 192
    current_macs_per_frame = 96 * 192 + 2 * 3 * (192 * 192 + 192 * 192) + 192 * 75
    summary = {"task": "PS-20261021-10", "round": 32,
               "kind": "explicit_source_prosody_preflight", "records": len(rows),
               "assets": {"source_sha_verified": len(rows), "finite": True,
                          "cache_manifest_sha256": base.sha256(cache_manifest_path),
                          "track9_used": False, "fixed_male_used": False},
               "aggregate": {
                   "centered_log_f0_correlation": correlation(pooled_values["source_f0"],
                                                                pooled_values["target_f0"]),
                   "delta_log_f0_correlation": correlation(pooled_values["source_df0"],
                                                             pooled_values["target_df0"]),
                   "normalized_energy_correlation": correlation(pooled_values["source_energy"],
                                                                  pooled_values["target_energy"]),
                   "vuv_accuracy": vuv_equal / vuv_total,
                   "vuv_f1": 2 * vuv_true_positive / max(f1_denominator, 1),
                   "joint_voiced_frames": len(pooled_values["source_f0"])},
               "budget": {"input_dimensions_before": 96, "input_dimensions_after": 99,
                          "parameters_before": current_parameters,
                          "parameters_after": current_parameters + added_parameters,
                          "added_parameters": added_parameters,
                          "parameter_increase_percent": 100.0 * added_parameters / current_parameters,
                          "macs_per_frame_before": current_macs_per_frame,
                          "added_macs_per_frame": added_parameters,
                          "mac_increase_percent": 100.0 * added_parameters / current_macs_per_frame,
                          "added_macs_per_second_at_50hz": added_parameters * 50},
               "deployment_boundary": {
                   "offline_extractor": "WORLD Harvest+StoneMask+CheapTrick; non-causal evidence only",
                   "intended_runtime": "reuse existing source F0/energy analysis; causal parity not yet tested",
                   "board_measurement": False, "pl_measurement": False},
               "rows": rows, "elapsed_seconds": time.monotonic() - started,
               "training_started": False, "played": False, "board_touched": False}
    (args.output / "preflight.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"},
                     ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
