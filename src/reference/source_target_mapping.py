"""Experimental per-source log-F0 mapping; no speaker identity claim."""
import numpy as np


def pitch_statistics(f0):
    values = np.asarray(f0, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError('Expected finite nonnegative F0')
    voiced = values[values > 0]
    if len(voiced) < 300:
        raise ValueError('Need at least 300 voiced calibration frames at 10 ms')
    low, median, high = np.percentile(np.log(voiced), [10, 50, 90])
    return {'log_median': float(median), 'log_p10': float(low),
            'log_p90': float(high), 'voiced_frames': len(voiced)}


def fit_pitch_mapping(source_f0, target_f0):
    source, target = pitch_statistics(source_f0), pitch_statistics(target_f0)
    # A nearly monotone enrollment cannot estimate expressive pitch variation.
    spread = source['log_p90'] - source['log_p10']
    target_spread = target['log_p90'] - target['log_p10']
    scale = float(np.clip(target_spread / spread, .5, 2)) if spread >= .05 else 1.
    return {'kind': 'experimental_source_target_log_f0', 'source': source,
            'target': target, 'scale': scale, 'output_bounds_hz': [75., 400.],
            'low_source_spread_fallback': bool(spread < .05),
            'speaker_identity_accepted': False}


def map_pitch(f0, profile):
    values = np.asarray(f0, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError('Expected finite nonnegative F0')
    result = values.copy()
    voiced = values > 0
    mapped = np.exp(profile['target']['log_median'] + profile['scale'] *
                    (np.log(values[voiced]) - profile['source']['log_median']))
    result[voiced] = np.clip(mapped, *profile['output_bounds_hz'])
    return result
