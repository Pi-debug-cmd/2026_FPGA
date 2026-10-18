"""Offline bounded low-frequency suppression in unvoiced candidate frames only."""
import numpy as np


def suppress_low_events(signal, f0):
    signal, f0 = np.asarray(signal, dtype=np.float64), np.asarray(f0, dtype=np.float64)
    if signal.ndim != 1 or len(signal) < 1024 or not np.all(np.isfinite(signal)):
        raise ValueError('Need finite mono samples, at least 1024')
    size, hop = 1024, 160
    centers = np.arange(len(signal) // hop + 1) * hop
    if f0.shape != centers.shape or not np.all(np.isfinite(f0)) or np.any(f0 < 0):
        raise ValueError('Need aligned finite nonnegative F0 at 10ms/16kHz')
    window = np.hanning(size)
    padded = np.pad(signal, (size // 2, size), mode='reflect')
    frames = np.stack([padded[start:start + size] for start in centers])
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    # Keep original frame DC for reconstruction; only center detector frames.
    analysis = np.fft.rfft((frames - frames.mean(axis=1, keepdims=True)) * window, axis=1)
    frequency = np.fft.rfftfreq(size, 1 / 16000)
    power = np.abs(analysis) ** 2
    low_ratio = power[:, frequency < 90].sum(axis=1) / np.maximum(power.sum(axis=1), 1e-30)
    strength = np.clip((low_ratio - .65) / .25, 0, 1)
    strength[(rms <= .003) | (f0 > 0)] = 0
    strength = np.convolve(strength, [.25, .5, .25], mode='same')
    strength[(f0 > 0) | (rms <= .003)] = 0
    # Smooth frequency taper; no intended attenuation at/above 100 Hz.
    taper = np.clip((100 - frequency) / 40, 0, 1)
    gains = 1 - (1 - 10 ** (-6 / 20)) * strength[:, None] * taper[None, :]
    spectrum = np.fft.rfft(frames * window, axis=1)
    processed = np.fft.irfft(spectrum * gains, n=size, axis=1) * window
    output, weights = np.zeros_like(padded), np.zeros_like(padded)
    for start, frame in zip(centers, processed):
        output[start:start + size] += frame
        weights[start:start + size] += window * window
    output /= np.maximum(weights, 1e-30)
    output = output[size // 2:size // 2 + len(signal)]
    return output, {'attenuated_frames': int(np.sum(strength > 0)),
                    'voiced_frames_attenuated': int(np.sum((strength > 0) & (f0 > 0))),
                    'minimum_frequency_gain': float(np.min(gains)),
                    'maximum_gain_difference_above_100hz': float(np.max(np.abs(gains[:, frequency >= 100] - 1))),
                    'maximum_attenuation_db': 6, 'offline_only': True}
