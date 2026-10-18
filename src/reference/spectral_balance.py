"""Experimental broad spectral tilt; not a source identity removal model."""
import numpy as np


def fit_balance(source_shape, target_shape):
    source, target = np.asarray(source_shape), np.asarray(target_shape)
    if source.shape != (513,) or target.shape != (513,) or not np.all(np.isfinite(source + target)):
        raise ValueError('Need finite 513-bin normalized log spectra')
    frequency = np.linspace(0, 8000, 513)
    roi = (frequency >= 300) & (frequency <= 4000)
    x = np.log2(np.maximum(frequency, 80) / 1000)
    delta_db = (target - source) * 10 / np.log(10)
    slope, intercept = np.polyfit(x[roi], delta_db[roi], 1, w=1 / np.sqrt(frequency[roi]))
    bounded = float(np.clip(slope, -4, 4))
    return {'kind': 'experimental_broad_spectral_balance', 'fitted_slope_db_per_octave': float(slope),
            'slope_db_per_octave': bounded, 'discarded_fit_intercept_db': float(intercept),
            'gain_limit_db': 4., 'fit_band_hz': [300, 4000],
            'power_tilt_db': np.clip(bounded * x, -4, 4).tolist(),
            'speaker_identity_accepted': False}


def low_band_ratio_db(shape):
    shape = np.asarray(shape)
    if shape.shape != (513,) or not np.all(np.isfinite(shape)):
        raise ValueError('Need a finite 513-bin log spectrum')
    frequency = np.linspace(0, 8000, 513)
    power = np.exp(shape - np.max(shape))
    low = power[(frequency >= 80) & (frequency < 400)].sum()
    high = power[(frequency >= 1000) & (frequency <= 4000)].sum()
    return float(10 * np.log10(low / high))


def fit_low_shelf(source_shape, target_shapes):
    source_ratio = low_band_ratio_db(source_shape)
    target_ratios = [low_band_ratio_db(shape) for shape in target_shapes]
    if not target_ratios:
        raise ValueError('Need target enrollment shapes')
    differences = source_ratio - np.asarray(target_ratios)
    # Require all target recordings to agree before reducing the source low band.
    consistent = bool(np.all(differences > 0))
    attenuation = float(np.clip(np.median(differences), 0, 4)) if consistent else 0.
    frequency = np.linspace(0, 8000, 513)
    low_shelf = np.clip((1000 - frequency) / 600, 0, 1)
    return {'kind': 'experimental_preparation_fitted_low_shelf',
            'source_low_high_ratio_db': source_ratio, 'target_low_high_ratios_db': target_ratios,
            'all_target_recordings_support_reduction': consistent, 'low_shelf_attenuation_db': attenuation,
            'power_tilt_db': (-attenuation * low_shelf).tolist(), 'gain_limit_db': 4.,
            'speaker_identity_accepted': False}


def apply_balance(spectrum, voiced, profile):
    original = np.asarray(spectrum, dtype=np.float64)
    voiced = np.asarray(voiced, dtype=bool)
    tilt = np.asarray(profile['power_tilt_db'])
    limit = float(profile['gain_limit_db'])
    if original.ndim != 2 or original.shape[1] != 513 or voiced.shape != (len(original),) or tilt.shape != (513,):
        raise ValueError('Profile or frame dimensions differ')
    if not np.all(np.isfinite(original)) or np.any(original <= 0) or not np.all(np.isfinite(tilt)) or not 0 < limit <= 4:
        raise ValueError('Invalid spectrum/profile')
    result = original.copy()
    active = original[voiced]
    if not len(active):
        return result
    total = active.sum(axis=1)
    # Solve a framewise gain offset while clipping the FINAL gains. This keeps
    # frame power and the absolute +/-4dB bound simultaneously; normalization
    # after ordinary clipping would violate the gain bound.
    low, high = np.full(len(active), -20.), np.full(len(active), 20.)
    for _ in range(44):
        middle = (low + high) / 2
        gain = 10 ** (np.clip(tilt[None, :] + middle[:, None], -limit, limit) / 10)
        excess = (active * gain).sum(axis=1) > total
        high = np.where(excess, middle, high)
        low = np.where(excess, low, middle)
    gain = 10 ** (np.clip(tilt[None, :] + ((low + high) / 2)[:, None], -limit, limit) / 10)
    result[voiced] = active * gain
    return result
