"""Render the v23 WORLD control and one registered-F0 candidate for Round 19."""
from __future__ import annotations

import argparse
import hashlib
import json
from math import gcd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RATE = 16000
FIXED_RATIO = 108722 / 65536
OLD_PROFILE = {"formant_warp": 1.15, "log_power_delta": [0.0] * 513}
pyworld = None
sf = None
resample_poly = None
np = None
fit_pitch_mapping = None
map_pitch = None
apply_envelope = None
analyze = None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load16(path: Path) -> np.ndarray:
    audio, rate = sf.read(str(path), dtype="float64", always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if rate != RATE:
        common = gcd(int(rate), RATE)
        audio = resample_poly(audio, RATE // common, int(rate) // common)
    return np.ascontiguousarray(audio, dtype=np.float64)


def profile_f0(paths: list[Path]) -> np.ndarray:
    values = []
    for path in paths:
        f0, _, _ = analyze(load16(path))
        values.append(f0)
    return np.concatenate(values)


def render(source: np.ndarray, mapped_f0: np.ndarray, spectrum: np.ndarray,
           ap: np.ndarray) -> np.ndarray:
    output = pyworld.synthesize(
        np.ascontiguousarray(mapped_f0),
        np.ascontiguousarray(spectrum),
        np.ascontiguousarray(ap),
        RATE,
        frame_period=10,
    )[: len(source)]
    if len(output) != len(source) or not np.isfinite(output).all():
        raise RuntimeError("WORLD returned invalid output")
    peak = float(np.max(np.abs(output)))
    if peak > 0.98:
        output *= 0.98 / peak
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--asset-root",
        type=Path,
        required=True,
        help="Project root containing ignored WORLD dependencies and the authorized capture",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Defaults to the authorized Round 18 capture under this repository",
    )
    parser.add_argument("--crop-start", type=float, default=3.37)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build/generated/world_v23_f0_round19_20261024",
    )
    args = parser.parse_args()
    asset_root = args.asset_root.resolve()
    generated = asset_root / "build/generated"
    for dependency in (
        generated / "eval_deps_20261016",
        generated / "world_deps",
        generated / "seed_audio_deps",
        generated / "seed_cpu_deps",
    ):
        sys.path.insert(0, str(dependency))
    global np, pyworld, sf, resample_poly, fit_pitch_mapping, map_pitch, apply_envelope, analyze
    import numpy as numpy_module
    import pyworld as pyworld_module
    import soundfile as soundfile_module
    from scipy.signal import resample_poly as resample_poly_function
    from src.reference.source_target_mapping import fit_pitch_mapping as fit_pitch_mapping_function
    from src.reference.source_target_mapping import map_pitch as map_pitch_function
    from src.reference.timbre_envelope import apply_envelope as apply_envelope_function
    from src.reference.world_registration import analyze as analyze_function

    np = numpy_module
    pyworld = pyworld_module
    sf = soundfile_module
    resample_poly = resample_poly_function
    fit_pitch_mapping = fit_pitch_mapping_function
    map_pitch = map_pitch_function
    apply_envelope = apply_envelope_function
    analyze = analyze_function
    source_path = (
        args.input.resolve()
        if args.input
        else ROOT / "build/generated/seed_fixed_male_20261024/round18_capture.wav"
    )
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    original = load16(source_path)
    crop_sample = round(args.crop_start * RATE)
    source = np.ascontiguousarray(original[crop_sample:])
    if len(source) < RATE * 10:
        raise RuntimeError("Round 19 source crop is too short")

    source_profile_paths = [
        ROOT / "人物音频资料/男声" / f"标准录音 {number}.wav" for number in range(1, 4)
    ]
    target_profile_paths = [
        ROOT / "人物音频资料/女声" / f"Track {number}.wav" for number in range(5, 9)
    ]
    pitch_profile = fit_pitch_mapping(
        profile_f0(source_profile_paths), profile_f0(target_profile_paths)
    )

    f0, times, spectrum = analyze(source)
    ap = pyworld.d4c(source, f0, times, RATE, fft_size=1024)
    mapped_spectrum = apply_envelope(spectrum, f0 > 0, OLD_PROFILE, 0.65)
    variants = {
        "v23_fixed_ratio": f0 * FIXED_RATIO,
        "v23_registered_log_f0": map_pitch(f0, pitch_profile),
    }
    outputs = []
    for name, mapped_f0 in variants.items():
        audio = render(source, mapped_f0, mapped_spectrum, ap)
        path = output_dir / f"{name}.wav"
        sf.write(str(path), audio.astype(np.float32), RATE, subtype="PCM_16")
        voiced = mapped_f0[mapped_f0 > 0]
        outputs.append(
            {
                "candidate": name,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(path),
                "rate": RATE,
                "seconds": len(audio) / RATE,
                "peak": float(np.max(np.abs(audio))),
                "clip_samples": int(np.sum(np.abs(audio) >= 1.0)),
                "parameter_f0_p10_median_p90_hz": [
                    float(value) for value in np.percentile(voiced, [10, 50, 90])
                ],
            }
        )

    manifest = {
        "kind": "world_v23_registered_f0_round19",
        "task": "PS-20261021-10",
        "inputs": [
            {
                "role": "source",
                "path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(source_path),
                "original_seconds": len(original) / RATE,
                "crop_start_s": args.crop_start,
                "seconds": len(source) / RATE,
            }
        ],
        "profile": {
            "source_files": [str(path.relative_to(ROOT)).replace("\\", "/") for path in source_profile_paths],
            "target_files": [str(path.relative_to(ROOT)).replace("\\", "/") for path in target_profile_paths],
            "target_track9_used": False,
            "pitch": pitch_profile,
            "spectrum": {
                "formant_warp_profile": 1.15,
                "strength": 0.65,
                "effective_formant_warp": 1.0975,
                "mean_spectrum_correction": False,
            },
            "aperiodicity": "source retained",
        },
        "outputs": outputs,
        "played": False,
        "board_touched": False,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
