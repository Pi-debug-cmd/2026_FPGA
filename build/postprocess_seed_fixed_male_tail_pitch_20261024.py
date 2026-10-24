"""Create fixed tail-only pitch-shift candidates from one Seed-VC output."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--start-s", type=float, default=12.0)
    parser.add_argument("--crossfade-ms", type=float, default=100.0)
    parser.add_argument("--semitones", type=float, nargs="+", required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    asset_root = args.asset_root.resolve()
    for extra in (
        asset_root / "build" / "generated" / "seed_cpu_deps",
        asset_root / "build" / "generated" / "llvc_cpu_deps",
    ):
        sys.path.insert(0, str(extra))

    import librosa
    import numpy as np
    import soundfile as sf

    manifest_path = args.input_manifest.resolve()
    original = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = next(item for item in original["outputs"] if item["candidate"] == args.candidate)
    source_path = ROOT / source["path"]
    signal, rate = sf.read(str(source_path), dtype="float32", always_2d=False)
    if signal.ndim != 1:
        raise RuntimeError("Expected a mono Seed-VC output")

    start = round(args.start_s * rate)
    fade = round(args.crossfade_ms * rate / 1000.0)
    if not 0 <= start < len(signal):
        raise ValueError("Tail start lies outside the input")
    if not 0 < fade <= len(signal) - start:
        raise ValueError("Invalid crossfade length")

    output_root = ROOT / "build" / "generated" / "seed_fixed_male_20261024" / args.tag
    outputs = []
    for semitones in args.semitones:
        shifted_tail = librosa.effects.pitch_shift(
            signal[start:], sr=rate, n_steps=semitones, bins_per_octave=12, res_type="soxr_hq"
        ).astype("float32")
        shifted_tail = shifted_tail[: len(signal) - start]
        candidate = signal.copy()
        ramp = np.linspace(0.0, 1.0, fade, endpoint=True, dtype="float32")
        candidate[start : start + fade] = (
            signal[start : start + fade] * (1.0 - ramp) + shifted_tail[:fade] * ramp
        )
        candidate[start + fade :] = shifted_tail[fade:]

        label = f"tail_pitch_{semitones:+.1f}st".replace("+", "p").replace("-", "m").replace(".", "p")
        directory = output_root / label
        directory.mkdir(parents=True, exist_ok=True)
        output_path = directory / "candidate.wav"
        sf.write(str(output_path), candidate, rate, subtype="PCM_16")
        written, written_rate = sf.read(str(output_path), dtype="float32", always_2d=False)
        outputs.append(
            {
                "candidate": label,
                "source_candidate": args.candidate,
                "tail_pitch_semitones": semitones,
                "tail_start_s": args.start_s,
                "crossfade_ms": args.crossfade_ms,
                "path": output_path.relative_to(ROOT).as_posix(),
                "sha256": sha256(output_path),
                "rate": written_rate,
                "seconds": len(written) / written_rate,
                "peak": float(np.max(np.abs(written))),
                "clip_samples": int(np.count_nonzero(np.abs(written) >= 1.0)),
            }
        )

    result = {
        "kind": "strict_fixed_male_tail_pitch_outputs",
        "tag": args.tag,
        "inputs": original["inputs"],
        "source_output": source,
        "outputs": outputs,
        "postprocess": {
            "tail_start_s": args.start_s,
            "crossfade_ms": args.crossfade_ms,
            "pitch_shift": "librosa phase vocoder with soxr_hq resampling",
            "semitones": args.semitones,
        },
        "track9_used": False,
        "played": False,
        "board_touched": False,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    output_manifest = output_root / "manifest.json"
    output_manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MANIFEST {output_manifest}")


if __name__ == "__main__":
    main()
