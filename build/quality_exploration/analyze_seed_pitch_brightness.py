"""Measure whether the perceived pitch change is F0 or spectral brightness."""
from __future__ import annotations

import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate, resample_poly, stft


def load_mono(path: Path, start_s: float, seconds: float = 4.8) -> np.ndarray:
    rate, data = wavfile.read(path)
    signal = np.asarray(data)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)
    if np.issubdtype(signal.dtype, np.integer):
        signal = signal.astype(np.float64) / max(abs(np.iinfo(signal.dtype).min), np.iinfo(signal.dtype).max)
    else:
        signal = signal.astype(np.float64)
    if rate != 16000:
        divisor = np.gcd(rate, 16000)
        signal = resample_poly(signal, 16000 // divisor, rate // divisor)
    begin = round(start_s * 16000)
    signal = signal[begin:begin + round(seconds * 16000)]
    if len(signal) != round(seconds * 16000) or not np.all(np.isfinite(signal)):
        raise ValueError(f"Invalid analysis crop: {path}")
    return signal


def f0_track(signal: np.ndarray) -> np.ndarray:
    # A dependency-free normalized-autocorrelation tracker is sufficient for
    # the paired question here.  Both candidates have identical timing and are
    # measured with the same estimator; this is not a replacement for WORLD.
    size, hop = 640, 80
    minimum_lag, maximum_lag = 32, 267
    window = np.hanning(size)
    output = []
    for begin in range(0, len(signal) - size + 1, hop):
        frame = signal[begin:begin + size].copy()
        frame -= frame.mean()
        frame *= window
        corr = correlate(frame, frame, mode="full", method="fft")[size - 1:]
        if corr[0] <= 1e-10:
            output.append(0.0)
            continue
        corr /= corr[0]
        region = corr[minimum_lag:maximum_lag + 1]
        lag = minimum_lag + int(np.argmax(region))
        strength = corr[lag]
        if strength < 0.45:
            output.append(0.0)
            continue
        if minimum_lag < lag < maximum_lag:
            left, middle, right = corr[lag - 1:lag + 2]
            denominator = left - 2 * middle + right
            if abs(denominator) > 1e-12:
                lag += float(0.5 * (left - right) / denominator)
        output.append(16000.0 / lag)
    return np.asarray(output)


def spectral_metrics(signal: np.ndarray) -> dict[str, float]:
    frequencies, _, spectrum = stft(signal, fs=16000, window="hann", nperseg=512,
                                    noverlap=432, nfft=1024, boundary=None, padded=False)
    power = np.abs(spectrum) ** 2
    frame_energy = power.sum(axis=0)
    active = frame_energy > max(frame_energy.max() * 1e-4, 1e-15)
    power = power[:, active]
    centroid = (frequencies[:, None] * power).sum(axis=0) / np.maximum(power.sum(axis=0), 1e-15)
    low = power[(frequencies >= 300) & (frequencies < 2000)].sum(axis=0)
    high = power[(frequencies >= 2000) & (frequencies <= 7500)].sum(axis=0)
    ratio = 10 * np.log10(np.maximum(high, 1e-15) / np.maximum(low, 1e-15))
    return {
        "active_frame_count": int(active.sum()),
        "spectral_centroid_median_hz": float(np.median(centroid)),
        "spectral_centroid_mean_hz": float(np.mean(centroid)),
        "high_2k_7k5_to_low_300_2k_median_db": float(np.median(ratio)),
        "high_2k_7k5_to_low_300_2k_mean_db": float(np.mean(ratio)),
    }


def summarize(signal: np.ndarray) -> tuple[dict[str, float], np.ndarray]:
    f0 = f0_track(signal)
    voiced = f0 > 0
    result = {
        "f0_voiced_frames": int(voiced.sum()),
        "f0_median_hz": float(np.median(f0[voiced])),
        "f0_p10_hz": float(np.percentile(f0[voiced], 10)),
        "f0_p90_hz": float(np.percentile(f0[voiced], 90)),
        **spectral_metrics(signal),
    }
    return result, f0


def main() -> None:
    controlled = ROOT / "build/generated/quality_exploration_20261018/seed_registration_controlled_seed20261019"
    items = {
        "target_track9": (ROOT / "voice_src/src_1/Track 9(1).wav", 11.0),
        "seed_single_track8_cfg070": (
            ROOT / "build/generated/seed_reference_20261015/output_steps30/vc_source_target_1.0_30_0.7.wav", 1.0),
        "seed_multi_cfg070": (next((controlled / "cfg_0.70").glob("vc_*.wav")), 1.0),
        "seed_multi_cfg095": (next((controlled / "cfg_0.95").glob("vc_*.wav")), 1.0),
    }
    metrics: dict[str, dict[str, float]] = {}
    tracks: dict[str, np.ndarray] = {}
    for name, (path, start) in items.items():
        metrics[name], tracks[name] = summarize(load_mono(path, start))

    left = tracks["seed_multi_cfg070"]
    right = tracks["seed_multi_cfg095"]
    both = (left > 0) & (right > 0)
    cents = 1200 * np.log2(right[both] / left[both])
    comparison = {
        "both_voiced_frame_count": int(both.sum()),
        "cfg095_minus_cfg070_f0_median_cents": float(np.median(cents)),
        "cfg095_minus_cfg070_f0_mean_cents": float(np.mean(cents)),
        "cfg095_f0_more_than_20_cents_higher_fraction": float(np.mean(cents > 20)),
        "cfg095_f0_more_than_20_cents_lower_fraction": float(np.mean(cents < -20)),
        "cfg095_minus_cfg070_centroid_median_hz": (
            metrics["seed_multi_cfg095"]["spectral_centroid_median_hz"]
            - metrics["seed_multi_cfg070"]["spectral_centroid_median_hz"]),
        "cfg095_minus_cfg070_high_low_median_db": (
            metrics["seed_multi_cfg095"]["high_2k_7k5_to_low_300_2k_median_db"]
            - metrics["seed_multi_cfg070"]["high_2k_7k5_to_low_300_2k_median_db"]),
    }
    record = {
        "kind": "seed_registration_pitch_brightness_analysis",
        "date": "2026-10-18",
        "analysis_window_seconds": 4.8,
        "metrics": metrics,
        "aligned_cfg095_vs_cfg070": comparison,
        "interpretation_rule": (
            "A near-zero aligned F0 delta with positive centroid/high-low deltas supports "
            "spectral brightness rather than a global pitch raise."),
        "limitations": [
            "One utterance and one stochastic seed only.",
            "Spectral centroid can also move with phoneme timing and synthesis artifacts.",
            "This analysis does not establish target similarity or deployability.",
        ],
    }
    output = ROOT / "report/quality_exploration_pitch_brightness_20261018.json"
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
