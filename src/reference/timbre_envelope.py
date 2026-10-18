"""Experimental spectral-envelope registration, not a speaker identity model."""
import numpy as np


def normalized_log_shape(envelope, voiced):
    envelope = np.asarray(envelope, dtype=np.float64)
    voiced = np.asarray(voiced, dtype=bool)
    if envelope.ndim != 2 or voiced.shape != (len(envelope),) or not voiced.any():
        raise ValueError('Need voiced spectral-envelope frames')
    if not np.all(np.isfinite(envelope)) or np.any(envelope <= 0):
        raise ValueError('Envelope must be finite and positive')
    shape = np.log(envelope[voiced])
    shape -= np.mean(shape, axis=1, keepdims=True)
    return np.mean(shape, axis=0)


def warp_log_shape(shape, factor):
    if not 0.85 <= factor <= 1.25:
        raise ValueError('Formant warp outside experimental bounds')
    bins = np.arange(len(shape), dtype=np.float64)
    return np.interp(bins / factor, bins, shape)


def register_envelope(source_shape, target_shape, rate):
    source_shape, target_shape = map(np.asarray, [source_shape, target_shape])
    if source_shape.shape != target_shape.shape or source_shape.ndim != 1:
        raise ValueError('Envelope grids differ')
    frequency = np.linspace(0, rate / 2, len(source_shape))
    roi = (frequency >= 300) & (frequency <= 4000)
    if not roi.any():
        raise ValueError('Envelope grid does not cover speech formants')
    scores = []
    for factor in np.linspace(0.85, 1.25, 17):
        delta = target_shape - warp_log_shape(source_shape, float(factor))
        centered = delta[roi] - np.mean(delta[roi])
        scores.append((float(np.mean(centered * centered)), float(factor)))
    _, factor = min(scores)
    delta = target_shape - warp_log_shape(source_shape, factor)
    size = 2 * (len(delta) - 1)
    cepstrum = np.fft.irfft(delta, n=size)
    cepstrum[0] = 0  # Do not encode microphone/recording loudness as timbre.
    cepstrum[25:size - 24] = 0
    smooth = np.fft.rfft(cepstrum).real
    # Envelope is power, hence 10log10 rather than 20log10.
    limit = 6 * np.log(10) / 10
    smooth = np.clip(smooth, -limit, limit)
    return {'kind': 'experimental_voiced_envelope_warp_and_mean_shift',
            'formant_warp': factor, 'log_power_delta': smooth.tolist(),
            'warp_fit_scores': [{'mse': score, 'factor': candidate} for score, candidate in scores],
            'gain_limit_db': 6, 'cepstral_order': 24,
            'limitation': 'Global averages mix phonetic content and microphone characteristics'}


def apply_envelope(envelope, voiced, profile, strength=0.65):
    if not 0 <= strength <= 1:
        raise ValueError('Strength outside [0, 1]')
    result = np.asarray(envelope, dtype=np.float64).copy()
    voiced = np.asarray(voiced, dtype=bool)
    delta = np.asarray(profile['log_power_delta'])
    if result.ndim != 2 or delta.shape != (result.shape[1],) or voiced.shape != (len(result),):
        raise ValueError('Profile/frame dimensions differ')
    if not np.all(np.isfinite(result)) or np.any(result <= 0) or not np.all(np.isfinite(delta)):
        raise ValueError('Invalid spectrum')
    factor = 1 + strength * (profile['formant_warp'] - 1)
    for index in np.flatnonzero(voiced):
        original = result[index].copy()
        mapped = np.exp(warp_log_shape(np.log(original), factor) + strength * delta)
        mapped *= np.sum(original) / np.sum(mapped)
        result[index] = mapped
    return result
