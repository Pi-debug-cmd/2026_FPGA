"""Prepare verified HuBERT-to-WORLD pairs from fixed-male training recordings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import audit_source_prosody_round32_20261025 as prosody_audit  # noqa: E402
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def interpolate(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def best_energy_lag(source: np.ndarray, teacher: np.ndarray) -> dict:
    rows = []
    for lag in range(-10, 11):
        if lag >= 0:
            left, right = source[:len(source) - lag or None], teacher[lag:]
        else:
            left, right = source[-lag:], teacher[:len(teacher) + lag]
        correlation = float(np.corrcoef(left, right)[0, 1])
        rows.append({"lag_frames_5ms": lag, "correlation": correlation})
    return max(rows, key=lambda row: row["correlation"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--generation", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    generation = json.loads(args.generation.read_text(encoding="utf-8"))
    if not generation["complete"] or generation["recording4_used"] or generation["recording5_used"]:
        raise ValueError("teacher generation is incomplete or used locked material")
    args.output.mkdir(parents=True, exist_ok=True)
    hubert_dir = root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    hubert = base.HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    torch.set_num_threads(4)
    rows = []
    for record in generation["rows"]:
        source_path = root / record["source_path"]
        teacher_path = Path(record["teacher_path"])
        if sha256(source_path) != record["source_sha256"] or sha256(teacher_path) != record["teacher_sha256"]:
            raise ValueError(f"asset SHA mismatch: {record['role']}")
        source = base.read_16k(source_path)
        teacher = base.read_16k(teacher_path)
        content = base.extract_hubert(hubert, source)
        source_world = base.analyze_world(source)
        teacher_world = base.analyze_world(teacher)
        target = interpolate(teacher_world["output"], len(content))
        prosody = prosody_audit.resample_rows(prosody_audit.source_prosody(source), len(content))
        if (not np.isfinite(content).all() or not np.isfinite(target).all()
                or not np.isfinite(prosody).all() or min(len(content), len(target), len(prosody)) < 128):
            raise ValueError(f"invalid fixed-male pair: {record['role']}")
        cache_path = args.output / f"{record['role']}.npz"
        np.savez(cache_path, content=content.astype(np.float32), target=target,
                 source_prosody=prosody.astype(np.float32))
        energy_index = base.SP_DIM + 2
        lag = best_energy_lag(source_world["output"][:, energy_index],
                              teacher_world["output"][:, energy_index])
        rows.append({"role": record["role"], "source_path": record["source_path"],
                     "source_sha256": record["source_sha256"],
                     "teacher_path": str(teacher_path), "teacher_sha256": record["teacher_sha256"],
                     "source_samples": len(source), "teacher_samples": len(teacher),
                     "content_frames_20ms": len(content), "target_frames_20ms": len(target),
                     "eligible_crop128": len(content) >= 128, "best_energy_lag": lag,
                     "cache_path": str(cache_path), "cache_sha256": sha256(cache_path)})
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    manifest = {"task": "PS-20261021-10", "round": 93,
                "kind": "fixed_male_teacher_pair_cache", "rows": rows,
                "generation_sha256": sha256(args.generation),
                "complete": len(rows) == 3 and all(row["eligible_crop128"] for row in rows),
                "recording4_used": False, "recording5_used": False,
                "target_track9_used": False, "played": False, "board_touched": False}
    path = args.output / "cache_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
