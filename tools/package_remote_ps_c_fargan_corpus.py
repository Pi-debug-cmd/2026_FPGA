"""Build a portable, hash-verified paired corpus bundle for PS-20261025-20."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    budget = args.asset_root / "交接/核心材料/board_budget_20261005"
    full = budget / "full_train_corpus_16k"
    fargan = budget / "fargan_corpus_expanded"
    fargan_original = budget / "fargan_corpus"
    full_manifest = json.loads((full / "manifest.json").read_text(encoding="utf-8"))
    fargan_manifest = json.loads((fargan / "manifest.json").read_text(encoding="utf-8"))
    if not full_manifest["complete"] or not fargan_manifest["complete"]:
        raise ValueError("source manifests are incomplete")
    full_rows = full_manifest["train"] + full_manifest["validation"]
    if len(full_rows) != 200:
        raise ValueError(f"expected 200 full-corpus rows, got {len(full_rows)}")
    fargan_by_stem = {Path(row["filename"]).stem: row for row in fargan_manifest["files"]}

    staging = args.output / "paired_hubert_fargan_corpus_v1"
    if staging.exists():
        shutil.rmtree(staging)
    for relative in ("pcm/src", "pcm/tch", "features/source", "features/teacher"):
        (staging / relative).mkdir(parents=True, exist_ok=True)

    portable_rows = []
    for row in full_rows:
        stem = row["stem"]
        feature_row = fargan_by_stem.get(stem)
        if feature_row is None or feature_row["split"] != row["split"]:
            raise ValueError(f"missing or split-mismatched FARGAN row: {stem}")
        def feature_path(kind: str) -> Path:
            name = Path(feature_row[f"{kind}_features"]).name
            candidates = (fargan / name, fargan_original / name)
            matches = [path for path in candidates if path.is_file()]
            if len(matches) != 1:
                raise ValueError(f"expected one {kind} feature file for {stem}, got {matches}")
            return matches[0]

        sources = {
            "source_pcm": full / "src" / f"{stem}.f32",
            "teacher_pcm": full / "tch" / f"{stem}.f32",
            "source_features": feature_path("source"),
            "teacher_features": feature_path("teacher"),
        }
        if sha256(sources["source_pcm"]) != row["src_sha"]:
            raise ValueError(f"source PCM SHA mismatch: {stem}")
        if sha256(sources["teacher_pcm"]) != row["tch_sha"]:
            raise ValueError(f"teacher PCM SHA mismatch: {stem}")
        destinations = {
            "source_pcm": staging / "pcm/src" / f"{stem}.f32",
            "teacher_pcm": staging / "pcm/tch" / f"{stem}.f32",
            "source_features": staging / "features/source" / f"{stem}.f32",
            "teacher_features": staging / "features/teacher" / f"{stem}.f32",
        }
        assets = {}
        for name, source in sources.items():
            if not source.is_file():
                raise FileNotFoundError(source)
            destination = destinations[name]
            shutil.copy2(source, destination)
            size = destination.stat().st_size
            if name.endswith("features") and size % (20 * 4):
                raise ValueError(f"invalid 20-D feature size: {source}")
            if name.endswith("pcm") and size % 4:
                raise ValueError(f"invalid float32 PCM size: {source}")
            assets[name] = {
                "path": destination.relative_to(staging).as_posix(),
                "bytes": size,
                "sha256": sha256(destination),
                "samples_or_frames": size // (80 if name.endswith("features") else 4),
            }
        portable_rows.append({"stem": stem, "speaker": row["speaker"],
                              "split": row["split"], "text": row["text"],
                              "sample_rate": 16000, "assets": assets})

    manifest = {"task": "PS-20261025-20", "version": 1, "complete": True,
                "purpose": "HuBERT source content to target-style FARGAN 20-D feature training",
                "rows": portable_rows,
                "counts": {"train": sum(r["split"] == "train" for r in portable_rows),
                           "validation": sum(r["split"] == "validation" for r in portable_rows)},
                "target_track9_used": False,
                "teacher_origin": "existing project-approved CosyVoice3 source-VC paired corpus",
                "teacher_human_quality_accepted": False}
    manifest_path = staging / "portable_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    verifier = '''from pathlib import Path\nimport hashlib,json,sys\nroot=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent\nm=json.loads((root/"portable_manifest.json").read_text(encoding="utf-8"))\nassert m["complete"] and len(m["rows"])==200 and m["counts"]=={"train":192,"validation":8}\nfor row in m["rows"]:\n for item in row["assets"].values():\n  p=root/item["path"]; assert p.stat().st_size==item["bytes"]\n  assert hashlib.sha256(p.read_bytes()).hexdigest()==item["sha256"]\nprint("PASS",len(m["rows"]),sum(len(r["assets"]) for r in m["rows"]))\n'''
    (staging / "verify_bundle.py").write_text(verifier, encoding="utf-8")
    (staging / "README.md").write_text(
        "# PS-20261025-20 paired corpus v1\n\n"
        "Run `python verify_bundle.py .` after extraction. PCM files are mono 16 kHz "
        "float32; FARGAN feature files are frame-major float32 with 20 columns. "
        "Use only the manifest train rows for fitting and validation rows for checkpoint "
        "selection. Track 9 is absent. Paths are relative to this directory.\n", encoding="utf-8")
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / "PS-20261025-20_paired_hubert_fargan_corpus_v1.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as output:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                output.write(path, Path(staging.name) / path.relative_to(staging))
    summary = {"archive": archive.name, "bytes": archive.stat().st_size,
               "sha256": sha256(archive), "rows": len(portable_rows),
               "train": manifest["counts"]["train"],
               "validation": manifest["counts"]["validation"],
               "files_in_archive": sum(1 for path in staging.rglob("*") if path.is_file())}
    (args.output / "delivery_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
