"""Cache frozen HuBERT source content and target-teacher WORLD features."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round25_20261025/cache")
    parser.add_argument("--limit", type=int, default=0,
                        help="diagnostic limit; zero processes the complete declared corpus")
    args = parser.parse_args()
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    corpus = args.asset_root / "交接/核心材料/board_budget_20261005/full_train_corpus_16k"
    document = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    if not document.get("complete") or document.get("target_track9_used"):
        raise ValueError("paired corpus declaration is incomplete or uses Track 9")
    rows = [("train", row) for row in document["train"]]
    rows += [("validation", row) for row in document["validation"]]
    if args.limit:
        rows = rows[:args.limit]

    hubert_dir = args.asset_root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    model = base.HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    records = []
    speakers = {"train": set(), "validation": set()}
    total_seconds = {"train": 0.0, "validation": 0.0}
    for index, (split, row) in enumerate(rows, 1):
        source_path = resolve(corpus, "src", row["src"])
        teacher_path = resolve(corpus, "tch", row["tch"])
        if base.sha256(source_path) != row["src_sha"] or base.sha256(teacher_path) != row["tch_sha"]:
            raise ValueError(f"waveform SHA mismatch: {row['stem']}")
        source = read_raw(source_path)
        teacher = read_raw(teacher_path)
        content = base.extract_hubert(model, source)
        world = base.analyze_world(teacher)
        target = resample_rows(world["output"], len(content))
        destination = args.output / f"{row['stem']}.npz"
        np.savez_compressed(destination, content=content.astype(np.float16),
                            target=target.astype(np.float32))
        record = {"stem": row["stem"], "speaker": row["speaker"], "split": split,
                  "text": row["text"], "source_sha256": row["src_sha"],
                  "teacher_sha256": row["tch_sha"], "source_samples": len(source),
                  "teacher_samples": len(teacher), "content_frames": len(content),
                  "target_frames": len(target), "cache": destination.name,
                  "cache_sha256": base.sha256(destination)}
        records.append(record)
        speakers[split].add(row["speaker"])
        total_seconds[split] += len(source) / base.SAMPLE_RATE
        if index == 1 or index % 10 == 0 or index == len(rows):
            print(json.dumps({"processed": index, "total": len(rows), "stem": row["stem"],
                              "split": split, "frames": len(content)}, ensure_ascii=False), flush=True)

    overlap = speakers["train"] & speakers["validation"]
    if overlap:
        raise AssertionError(f"speaker leakage across split: {sorted(overlap)}")
    summary = {"task": "PS-20261021-10", "round": 25,
               "kind": "paired_hubert_world_feature_cache",
               "complete": not args.limit, "declared_pairs": len(document["train"]) + len(document["validation"]),
               "processed_pairs": len(records),
               "split": {name: {"pairs": sum(row["split"] == name for row in records),
                                   "speakers": sorted(speakers[name]),
                                   "seconds": total_seconds[name]}
                         for name in ("train", "validation")},
               "speaker_disjoint": True, "target_track9_used": False,
               "fixed_male_audio_used": False,
               "hubert_checkpoint_sha256": base.sha256(hubert_dir / "pytorch_model.bin"),
               "feature_dim": {"content": 768, "world": base.OUTPUT_DIM},
               "world_representation": {"sp_dct": base.SP_DIM, "ap_dct": base.AP_DIM,
                                        "frame_rate": "resampled to HuBERT frames"},
               "records": records, "elapsed_seconds": time.monotonic() - started,
               "board_touched": False, "played": False}
    (args.output.parent / "cache_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "records"},
                     ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
