"""Run deterministic Seed-VC candidates for the strict Fixed-Male split.

This is an offline quality-ceiling experiment.  It never records, plays audio,
or touches the board.  Model assets stay under an explicitly supplied asset
root and generated WAVs stay under build/generated/.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
TARGET_NAMES = [f"Track {number}.wav" for number in range(5, 9)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--cfg", type=float, nargs="+", required=True)
    parser.add_argument("--seed", type=int, nargs="+", required=True)
    parser.add_argument("--steps", type=int, default=30)
    return parser.parse_args()


def select_speech_window(signal, rate: int, seconds: float):
    import numpy as np

    count = round(seconds * rate)
    if len(signal) < count:
        raise ValueError("Target registration track is too short")
    frame = round(0.02 * rate)
    hop = round(0.01 * rate)
    squares = np.convolve(
        np.asarray(signal, dtype=np.float64) ** 2,
        np.ones(frame, dtype=np.float64) / frame,
        mode="valid",
    )[::hop]
    active = squares > 10 ** (-45 / 10)
    frames = max(1, int(np.ceil((count - frame) / hop)) + 1)
    activity = np.convolve(active.astype(np.float64), np.ones(frames), mode="valid")
    energy = np.convolve(squares, np.ones(frames), mode="valid")
    start_frame = int(np.argmax(activity + 0.01 * np.log(np.maximum(energy, 1e-20))))
    start = min(start_frame * hop, len(signal) - count)
    return start, np.asarray(signal[start : start + count], dtype=np.float64).copy()


def prepare_inputs(base: Path, source_original: Path):
    import numpy as np
    from src.reference.audio_io import downsample_16k, file_sha256, read_pcm_wav, write_pcm16

    inputs = base / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    rate, source = read_pcm_wav(source_original)
    source = downsample_16k(rate, source)
    source_gain = min(
        0.04 / max(float(np.sqrt(np.mean(source**2))), 1e-12),
        0.9 / max(float(np.max(np.abs(source))), 1e-12),
    )
    source_path = inputs / "source.wav"
    write_pcm16(source_path, source * source_gain)
    records = [
        {
            "role": "source",
            "path": str(source_original.relative_to(ROOT)).replace("\\", "/"),
            "sha256": file_sha256(source_original),
            "seconds": len(source) / 16000,
            "offline_gain": source_gain,
        }
    ]

    parts = []
    fade = np.linspace(0.0, 1.0, round(0.01 * 16000), endpoint=False)
    for name in TARGET_NAMES:
        original = ROOT / "人物音频资料" / "女声" / name
        rate, signal = read_pcm_wav(original)
        signal = downsample_16k(rate, signal)
        start, part = select_speech_window(signal, 16000, 2.0)
        part[: len(fade)] *= fade
        part[-len(fade) :] *= fade[::-1]
        parts.append(part)
        records.append(
            {
                "role": "target_registration_segment",
                "path": str(original.relative_to(ROOT)).replace("\\", "/"),
                "sha256": file_sha256(original),
                "crop_start_s": start / 16000,
                "seconds": len(part) / 16000,
            }
        )
    target = np.concatenate(parts)
    target_gain = min(
        0.04 / max(float(np.sqrt(np.mean(target**2))), 1e-12),
        0.9 / max(float(np.max(np.abs(target))), 1e-12),
    )
    target_path = inputs / "target_registered.wav"
    write_pcm16(target_path, target * target_gain)
    records.append(
        {
            "role": "target_registration_prompt",
            "construction": "Track 5-8, deterministic 2 s high-activity window each",
            "seconds": len(target) / 16000,
            "offline_gain": target_gain,
            "sha256": file_sha256(target_path),
            "track9_used": False,
        }
    )
    return records, source_path, target_path


def main() -> None:
    args = parse_args()
    if args.steps < 1 or any(value < 0 or value > 2 for value in args.cfg):
        raise SystemExit("Invalid steps/cfg")
    if not args.tag.replace("_", "").replace("-", "").isalnum():
        raise SystemExit("Tag must contain only letters, numbers, underscores or hyphens")

    asset_root = args.asset_root.resolve()
    source_original = args.source.resolve()
    try:
        source_original.relative_to(ROOT)
    except ValueError as error:
        raise SystemExit("Source must be a tracked canonical file under this checkout") from error

    generated = ROOT / "build" / "generated"
    external_generated = asset_root / "build" / "generated"
    for directory in ("llvc_cpu_deps", "seed_audio_deps", "seed_cpu_deps"):
        sys.path.insert(0, str(external_generated / directory))
    sys.path.insert(0, str(ROOT))

    import numpy as np
    import torch
    import yaml
    from src.reference.audio_io import file_sha256

    base = generated / "seed_fixed_male_20261024" / args.tag
    base.mkdir(parents=True, exist_ok=True)
    input_records, source_path, target_path = prepare_inputs(base, source_original)

    seed_base = external_generated / "seed_reference_20261015"
    upstream = next((seed_base / "source").glob("seed-vc-*"))
    runtime = base / "cpu_runtime"
    if not runtime.exists():
        shutil.copytree(upstream, runtime)
    modified = {}
    for relative in ("inference.py", "modules/length_regulator.py"):
        text = (upstream / relative).read_text(encoding="utf-8")
        if relative == "inference.py":
            text = text.replace(".half()", ".float()")
        else:
            text = text.replace("from dac.nn.quantize import VectorQuantize\n", "")
            text = text.replace(
                "            if vector_quantize:\n",
                "            if vector_quantize:\n                from dac.nn.quantize import VectorQuantize\n",
            )
        destination = runtime / relative
        destination.write_text(text, encoding="utf-8")
        modified[relative] = {
            "upstream_sha256": file_sha256(upstream / relative),
            "runtime_sha256": file_sha256(destination),
        }

    manifest_path = asset_root / "report" / "seed_reference_assets_20261015.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest["complete"]:
        raise RuntimeError("Seed asset manifest is incomplete")
    assets = {}
    for item in manifest["files"]:
        path = Path(item["path"])
        if not path.is_absolute():
            path = asset_root / path
        if file_sha256(path) != item["actual_sha256"]:
            raise RuntimeError(f"Seed asset SHA changed: {path}")
        assets[(item["repository"], item["name"])] = str(path)

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["NUMBA_CACHE_DIR"] = str(base / "numba_cache")
    os.environ["HF_HOME"] = str(base / "hf_cache")
    os.chdir(runtime)
    sys.path.insert(0, str(runtime))
    torch.set_num_threads(4)

    import hf_utils

    def pinned_load(repo_id, model_filename="pytorch_model.bin", config_filename=None):
        path = assets[(repo_id, model_filename)]
        return (path, assets[(repo_id, config_filename)]) if config_filename else path

    hf_utils.load_custom_model_from_hf = pinned_load
    import modules.commons as commons

    original_loader = commons.load_checkpoint
    loading_audit = []

    def checked_load(model, optimizer, path, *values, **options):
        state = torch.load(path, map_location="cpu", weights_only=True)["net"]
        for name, network in model.items():
            supplied = {key.removeprefix("module."): value for key, value in state[name].items()}
            for key, parameter in network.named_parameters():
                if key not in supplied or supplied[key].shape != parameter.shape:
                    raise RuntimeError(f"Learned parameter missing/mismatched: {name}/{key}")
        loading_audit.append({"checkpoint": file_sha256(path), "all_parameters_present": True})
        return original_loader(model, optimizer, path, *values, **options)

    commons.load_checkpoint = checked_load
    config = yaml.safe_load(
        (runtime / "configs/presets/config_dit_mel_seed_uvit_xlsr_tiny.yml").read_text(encoding="utf-8")
    )
    config["model_params"]["speech_tokenizer"]["name"] = str(
        seed_base / "assets" / "facebook__wav2vec2-xls-r-300m"
    )
    config_path = base / "cpu_tiny_config.yml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    import inference
    import soundfile as sf

    if inference.device.type != "cpu":
        raise RuntimeError("Strict sweep is pinned to CPU")
    outputs = []
    for seed in args.seed:
        for cfg in args.cfg:
            torch.manual_seed(seed)
            candidate = f"cfg_{cfg:.2f}_seed_{seed}"
            output_dir = base / candidate
            settings = SimpleNamespace(
                source=str(source_path),
                target=str(target_path),
                output=str(output_dir),
                diffusion_steps=args.steps,
                length_adjust=1.0,
                inference_cfg_rate=cfg,
                f0_condition=False,
                auto_f0_adjust=False,
                semi_tone_shift=0,
                checkpoint=assets[("Plachta/Seed-VC", "DiT_uvit_tat_xlsr_ema.pth")],
                config=str(config_path),
                fp16=False,
            )
            started = time.perf_counter()
            inference.main(settings)
            elapsed = time.perf_counter() - started
            generated_wav = next(output_dir.glob("vc_*.wav"))
            signal, rate = sf.read(generated_wav, dtype="float32")
            if not np.isfinite(signal).all() or float(np.sqrt(np.mean(signal**2))) < 1e-6:
                raise RuntimeError(f"Invalid output: {candidate}")
            outputs.append(
                {
                    "candidate": candidate,
                    "cfg": cfg,
                    "seed": seed,
                    "steps": args.steps,
                    "path": str(generated_wav.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": file_sha256(generated_wav),
                    "elapsed_s": elapsed,
                    "rate": rate,
                    "seconds": len(signal) / rate,
                    "peak": float(np.max(np.abs(signal))),
                    "clip_samples": int(np.sum(np.abs(signal) >= 1)),
                }
            )
            print(f"COMPLETE {candidate} elapsed={elapsed:.2f}s", flush=True)

    record = {
        "kind": "strict_fixed_male_seed_vc_outputs",
        "tag": args.tag,
        "device": "cpu",
        "inputs": input_records,
        "outputs": outputs,
        "runtime_changes": modified,
        "checkpoint_loading": loading_audit,
        "track9_used": False,
        "played": False,
        "board_touched": False,
    }
    output_manifest = base / "manifest.json"
    output_manifest.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MANIFEST {output_manifest}")


if __name__ == "__main__":
    main()
