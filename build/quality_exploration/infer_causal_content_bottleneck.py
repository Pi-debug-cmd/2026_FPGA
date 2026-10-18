"""Render speaker-heldout full utterances through the causal bottleneck and FARGAN."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import wave

import numpy as np

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_causal_content_bottleneck import (
    CausalContentBottleneck,
    ROOT,
    causal_prosody,
    load_manifest,
    read_features,
    split_pairs,
)


EXE = ROOT / "交接" / "核心材料" / "board_support" / "native_llvc_20261005" / "fargan_probe_host.exe"
DEFAULT_CHECKPOINT = ROOT / "build" / "generated" / "quality_exploration_20261018" / "causal_content_bottleneck_v1.pt"
DEFAULT_OUTPUT = ROOT / "build" / "generated" / "quality_exploration_20261018" / "causal_bottleneck_heldout"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_verified_checkpoint(path: Path):
    before = sha256(path)
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if sha256(path) != before:
        raise RuntimeError("checkpoint changed while it was being loaded")
    document, manifest_path = load_manifest()
    manifest_hash = sha256(manifest_path)
    if checkpoint.get("manifest_sha256") != manifest_hash:
        raise ValueError("checkpoint manifest hash does not match the current manifest")
    train, validation = split_pairs(document)
    expected = checkpoint.get("split", {})
    actual = {
        "train_speakers": sorted({pair.speaker for pair in train}),
        "validation_speakers": sorted({pair.speaker for pair in validation}),
        "train_pairs": len(train), "validation_pairs": len(validation),
    }
    if expected != actual:
        raise ValueError(f"checkpoint split does not match current split: {expected!r} != {actual!r}")
    if set(actual["train_speakers"]) & set(actual["validation_speakers"]):
        raise ValueError("checkpoint split contains speaker leakage")
    normalization = checkpoint["normalization"]
    if normalization.get("estimated_from_train_speakers_only") is not True:
        raise ValueError("checkpoint normalization is not marked train-only")
    model = CausalContentBottleneck(
        np.asarray(normalization["content_mean"], dtype=np.float32),
        np.asarray(normalization["content_std"], dtype=np.float32),
        np.asarray(normalization["target_profile"], dtype=np.float32),
        speakers=len(checkpoint["speaker_ids"]),
        latent_dim=int(checkpoint["config"]["latent_dim"]),
    )
    model.load_state_dict(checkpoint["model"], strict=True)
    model.eval()
    return model, checkpoint, document, manifest_path, validation, before


def infer_features(model: CausalContentBottleneck, source: np.ndarray,
                   chunk_frames: int | None = None) -> np.ndarray:
    """Stateful chunks are numerically equivalent to an unbroken causal GRU pass."""
    spectrum = torch.as_tensor(source[:, 1:18][None], dtype=torch.float32)
    prosody = torch.as_tensor(causal_prosody(source)[None], dtype=torch.float32)
    if not chunk_frames or chunk_frames >= len(source):
        with torch.inference_mode():
            output, _ = model(spectrum, prosody)
        result = output[0].numpy()
    else:
        encoder_state = decoder_state = None
        outputs = []
        with torch.inference_mode():
            condition = torch.tanh(model.target_projection(model.target_profile)).view(1, 1, -1)
            for start in range(0, len(source), chunk_frames):
                stop = min(start + chunk_frames, len(source))
                x = (spectrum[:, start:stop] - model.content_mean) / model.content_std
                encoded, encoder_state = model.content_gru(torch.tanh(model.content_pre(x)), encoder_state)
                latent = torch.tanh(model.bottleneck(encoded))
                target = condition.expand(1, stop - start, -1)
                decoded, decoder_state = model.decoder_gru(
                    torch.cat((latent, prosody[:, start:stop], target), dim=-1), decoder_state)
                outputs.append(model.output(decoded))
        result = torch.cat(outputs, dim=1)[0].numpy()
    result = np.asarray(result, dtype=np.float32)
    if result.shape != source.shape:
        raise ValueError(f"unexpected output shape {result.shape}; expected {source.shape}")
    if not np.isfinite(result).all():
        raise ValueError("inference produced non-finite features")
    return result


def pcm_to_wav(pcm: Path, destination: Path) -> None:
    with wave.open(str(destination), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(pcm.read_bytes())


def render(checkpoint_path: Path, output_dir: Path, chunk_frames: int | None) -> dict:
    model, checkpoint, _, manifest_path, validation, checkpoint_hash = load_verified_checkpoint(checkpoint_path)
    if not EXE.is_file():
        raise FileNotFoundError(EXE)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for pair in validation:
        source = read_features(pair.source)
        converted = infer_features(model, source, chunk_frames)
        stem = pair.source.name.replace("_source.features.f32", "")
        feature = output_dir / f"{stem}.converted.f32"
        pcm = output_dir / f"{stem}.pcm"
        wav = output_dir / f"{stem}.wav"
        stats = output_dir / f"{stem}.synthesis.json"
        converted.tofile(feature)
        subprocess.run([str(EXE), "--synthesis", str(feature), str(pcm), str(stats)],
                       check=True, cwd=EXE.parent)
        samples = pcm.stat().st_size // 2
        expected_samples = len(source) * 160
        if samples != expected_samples:
            raise ValueError(f"FARGAN length mismatch for {stem}: {samples} != {expected_samples}")
        pcm_to_wav(pcm, wav)
        rows.append({
            "filename": stem,
            "speaker": pair.speaker,
            "source_feature": str(pair.source.relative_to(ROOT)),
            "source_frames": len(source),
            "converted_feature": str(feature.relative_to(ROOT)),
            "converted_feature_sha256": sha256(feature),
            "feature_finite": bool(np.isfinite(converted).all()),
            "pcm": str(pcm.relative_to(ROOT)),
            "pcm_samples": samples,
            "pcm_sha256": sha256(pcm),
            "wav": str(wav.relative_to(ROOT)),
            "wav_sha256": sha256(wav),
            "synthesis_stats": str(stats.relative_to(ROOT)),
        })
    report = {
        "kind": "causal_content_bottleneck_heldout_inference",
        "checkpoint": str(checkpoint_path.relative_to(ROOT)),
        "checkpoint_sha256": checkpoint_hash,
        "checkpoint_epoch": checkpoint["epoch"],
        "manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": checkpoint["manifest_sha256"],
        "validated_split": checkpoint["split"],
        "full_utterance_causal": True,
        "stateful_chunk_frames": chunk_frames,
        "fargan_executable": str(EXE.relative_to(ROOT)),
        "fargan_executable_sha256": sha256(EXE),
        "sample_rate": 16000,
        "frame_samples": 160,
        "outputs": rows,
        "board_touched": False,
        "audio_played": False,
        "speaker_or_quality_metrics_run": False,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    (output_dir / "manifest.json").write_text(rendered + "\n", encoding="utf-8")
    (output_dir / "report.json").write_text(rendered + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chunk-frames", type=int, default=0,
                        help="stateful inference chunk; 0 performs one unbroken full-utterance pass")
    args = parser.parse_args()
    report = render(args.checkpoint.resolve(), args.output.resolve(), args.chunk_frames or None)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
