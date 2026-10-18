"""Prepare a target profile and source/original-vs-pitch audio, without board access."""

import argparse
import json
from pathlib import Path

import numpy as np

from src.reference.audio_io import downsample_16k, file_sha256, read_pcm_wav, write_pcm16
from src.reference.pitch_shift_fixed import FixedPitchShifter
from src.reference.voice_profile import build_profile, calibration_ratio, register_wav


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materials", type=Path, default=Path("交接/核心材料"))
    parser.add_argument("--output", type=Path, default=Path("data/reference_demo"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    target_path = args.materials / "目标人物原始语音/Track 5.wav"
    target_profile = register_wav(target_path, args.output / "target_profile.json", channel=0)
    rate, target = read_pcm_wav(target_path, channel=0)
    write_pcm16(args.output / "target_reference.wav", downsample_16k(rate, target))

    corpus = args.materials / "board_budget_20261005/full_train_corpus_16k"
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8-sig"))
    # Already-used development speaker; do not claim an independent holdout test.
    selected = [row for row in manifest["validation"] if row["speaker"] == "SSB0434"]
    if len(selected) != 4:
        raise ValueError("Expected the four documented development clips")
    segments, provenance = [], []
    for row in selected:
        original = str(row["src"]).replace("\\", "/")
        suffix = original.split("/full_train_corpus_16k/", 1)[1]
        local = (corpus / suffix).resolve()
        if not local.is_relative_to(corpus.resolve()):
            raise ValueError("Source path escapes corpus")
        samples = np.fromfile(local, dtype="<f4").astype(np.float64)
        if len(samples) == 0 or not np.all(np.isfinite(samples)) or np.max(abs(samples)) > 1:
            raise ValueError("Invalid normalized source audio")
        segments.append(samples)
        segments.append(np.zeros(1600))
        provenance.append({"stem": row["stem"], "sha256": file_sha256(local),
                           "samples": len(samples)})
    source = np.concatenate(segments)
    source_profile = build_profile(source)
    (args.output / "source_profile.json").write_text(
        json.dumps(source_profile, indent=2) + "\n", encoding="utf-8")
    ratio, ratio_q16 = calibration_ratio(source_profile, target_profile)
    source_pcm = np.clip(np.rint(source * 32768), -32768, 32767).astype(np.int16)
    processed = FixedPitchShifter(ratio_q16).process(source_pcm)
    write_pcm16(args.output / "source_original.wav", source_pcm.astype(np.float64) / 32768)
    write_pcm16(args.output / "pitch_only.wav", processed.astype(np.float64) / 32768)
    report = {
        "version": 1, "kind": "offline_pitch_only_development_demo",
        "target_sha256": file_sha256(target_path), "target_channel": 0,
        "source_speaker": "SSB0434", "source_clips": provenance,
        "source_median_f0_hz": source_profile["f0_median_hz"],
        "target_median_f0_hz": target_profile["f0_median_hz"],
        "ratio": ratio, "ratio_q16": ratio_q16,
        "duration_s": len(source_pcm) / 16000,
        "output_samples": len(processed),
        "limitations": ["No target timbre transfer or human listening acceptance",
                        "Previously screened development clips, not an independent test",
                        "No board run or end-to-end delay measurement"],
    }
    for filename in ("target_reference.wav", "source_original.wav", "pitch_only.wav"):
        report[filename + "_sha256"] = file_sha256(args.output / filename)
    (args.output / "demo.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("source_median_f0_hz", "target_median_f0_hz",
                                                "ratio", "ratio_q16", "duration_s", "output_samples")}, indent=2))


if __name__ == "__main__":
    main()
