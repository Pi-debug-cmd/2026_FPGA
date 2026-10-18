"""Synthesize cached target Track5-8 features with the mapper-free FARGAN vocoder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "交接/核心材料"
CORPUS = LEGACY / "board_budget_20261005/fargan_corpus"
MANIFEST = CORPUS / "manifest.json"
EXE = LEGACY / "board_support/native_llvc_20261005/fargan_probe_host.exe"
OUTPUT = ROOT / "build/generated/quality_exploration_20261018/fargan_target_oracle"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pcm_to_wav(raw: Path, wav: Path) -> None:
    payload = raw.read_bytes()
    with wave.open(str(wav), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(payload)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("feature_dim") != 20 or manifest.get("frame_samples") != 160:
        raise ValueError("Unexpected cached FARGAN feature format")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, item in enumerate(manifest["target_training"], start=5):
        feature = CORPUS / Path(item["features"]).name
        frames, remainder = divmod(feature.stat().st_size, 20 * 4)
        if remainder:
            raise ValueError(f"Malformed feature file: {feature}")
        stem = f"target_track{index}_fargan_oracle"
        raw = OUTPUT / f"{stem}.pcm"
        wav = OUTPUT / f"{stem}.wav"
        stats = OUTPUT / f"{stem}.stats.json"
        subprocess.run([str(EXE), "--synthesis", str(feature), str(raw), str(stats)],
                       check=True, cwd=EXE.parent)
        pcm_samples = raw.stat().st_size // 2
        if pcm_samples != frames * 160:
            raise ValueError(f"Unexpected output length for {stem}: {pcm_samples}")
        pcm_to_wav(raw, wav)
        rows.append({
            "track": index,
            "feature_path": str(feature.relative_to(ROOT)),
            "feature_sha256": sha256(feature),
            "feature_frames": frames,
            "recorded_input_samples_in_legacy_manifest": item["samples"],
            "output_pcm_samples": pcm_samples,
            "duration_seconds": pcm_samples / 16000,
            "wav_path": str(wav.relative_to(ROOT)),
            "wav_sha256": sha256(wav),
            "synthesis_stats_path": str(stats.relative_to(ROOT)),
        })
    report = {
        "kind": "mapper_independent_fargan_target_oracle",
        "date": "2026-10-18",
        "official_pretrained_vocoder": True,
        "mapper_used": False,
        "board_touched": False,
        "audio_played": False,
        "outputs": rows,
        "limitations": [
            "Cached features were extracted from target Track5-8 by the legacy official encoder.",
            "This establishes only the vocoder reconstruction ceiling.",
            "No target registration, unseen-source conversion, subjective acceptance, or board runtime is claimed.",
        ],
    }
    destination = ROOT / "report/quality_exploration_fargan_target_oracle_20261018.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
