"""Offline single-target/source F0 calibration; not a speaker identity model."""

import argparse
import json
from pathlib import Path

import numpy as np

from src.reference.audio_io import downsample_16k, file_sha256, read_pcm_wav
from src.reference.pitch_shift_fixed import ratio_to_q16


def estimate_f0(samples, rate=16000, f0_min=75, f0_max=400):
    """YIN difference and cumulative normalization, 40 ms frames / 10 ms hops."""
    samples = np.asarray(samples, dtype=np.float64)
    if rate != 16000 or samples.ndim != 1 or not np.all(np.isfinite(samples)):
        raise ValueError("Expected finite mono 16 kHz samples")
    size, hop = 640, 160
    min_lag, max_lag = int(np.ceil(rate / f0_max)), int(np.floor(rate / f0_min))
    if not 2 <= min_lag < max_lag < size // 2:
        raise ValueError("F0 range is incompatible with the frame size")
    values = []
    total_frames = max(0, 1 + (len(samples) - size) // hop)
    for index in range(total_frames):
        frame = samples[index * hop:index * hop + size]
        frame = frame - frame.mean()
        if np.sqrt(np.mean(frame * frame)) < 10 ** (-45 / 20):
            continue
        width = size // 2
        energy = np.concatenate(([0.0], np.cumsum(frame * frame)))
        correlation = np.correlate(frame, frame[:width], mode="valid")[:max_lag + 1]
        lag = np.arange(max_lag + 1)
        difference = np.maximum(energy[width] + energy[width + lag] - energy[lag]
                                - 2 * correlation, 0)
        cumulative = np.cumsum(difference[1:])
        normalized = np.ones(max_lag + 1)
        normalized[1:] = difference[1:] * np.arange(1, max_lag + 1) / np.maximum(cumulative, 1e-20)
        candidates = np.flatnonzero(normalized[min_lag:max_lag] < 0.15)
        if len(candidates) == 0:
            continue
        tau = min_lag + int(candidates[0])
        while tau < max_lag and normalized[tau + 1] < normalized[tau]:
            tau += 1
        refined = float(tau)
        if 0 < tau < max_lag:
            left, center, right = normalized[tau - 1:tau + 2]
            denominator = left - 2 * center + right
            if abs(denominator) > 1e-12:
                refined += float(np.clip(0.5 * (left - right) / denominator, -0.5, 0.5))
        f0 = rate / refined
        if f0_min <= f0 <= f0_max:
            values.append(f0)
    return np.asarray(values, dtype=np.float64), total_frames


def build_profile(samples):
    samples = np.asarray(samples, dtype=np.float64)
    if samples.ndim != 1 or len(samples) == 0 or not np.all(np.isfinite(samples)):
        raise ValueError("Empty or invalid recording")
    clipping = float(np.mean(abs(samples) >= 32760 / 32768))
    if clipping > 0.01:
        raise ValueError("More than 1% clipped samples; preserve the previous profile")
    f0, frames = estimate_f0(samples)
    if len(f0) < 300:
        raise ValueError("Less than 3 seconds of voiced-frame coverage; rerecord")
    return {
        "version": 1, "sample_rate": 16000, "kind": "f0_calibration_only",
        "duration_s": len(samples) / 16000,
        "voiced_frame_coverage_s": len(f0) * 0.01,
        "frames": frames, "voiced_frames": len(f0), "clip_fraction": clipping,
        "rms": float(np.sqrt(np.mean(samples * samples))),
        "f0_median_hz": float(np.median(f0)),
        "f0_p10_hz": float(np.percentile(f0, 10)),
        "f0_p90_hz": float(np.percentile(f0, 90)),
        "estimator": "yin_40ms_10ms_75_400hz_threshold_0.15",
    }


def calibration_ratio(source, target):
    ratio = target["f0_median_hz"] / source["f0_median_hz"]
    return ratio, ratio_to_q16(ratio)  # Reject rather than silently clamp beyond limits.


def register_wav(input_path, output_path, channel=0):
    # Validate before replacing an existing profile. Original audio stays untouched.
    input_path, output_path = Path(input_path), Path(output_path)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Profile output must differ from input audio")
    rate, samples = read_pcm_wav(input_path, channel)
    profile = build_profile(downsample_16k(rate, samples))
    profile.update({"input_sha256": file_sha256(input_path),
                    "input_sample_rate": rate, "input_channel": channel})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--channel", type=int, default=0)
    args = parser.parse_args()
    try:
        profile = register_wav(args.input, args.output, args.channel)
    except ValueError as error:
        parser.exit(2, f"Registration rejected: {error}\n")
    print(json.dumps(profile, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
