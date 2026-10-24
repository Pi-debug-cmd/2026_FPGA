"""Source-specific WORLD envelope mapping for the stage-1 fixed-male baseline.

The functions in this module are deliberately independent of PyWORLD.  They
operate on already analysed WORLD arrays so the numerical contract can be unit
tested without loading the offline evaluation models.
"""
from __future__ import annotations

import numpy as np


def warp_bins(values: np.ndarray, factor: float) -> np.ndarray:
    """Resample the last (frequency-bin) axis with edge clamping."""
    array = np.asarray(values, dtype=np.float64)
    if array.ndim not in (1, 2) or array.shape[-1] < 2:
        raise ValueError("values must be a 1-D or 2-D array with at least two bins")
    if not np.isfinite(array).all() or not np.isfinite(factor) or factor <= 0:
        raise ValueError("values and factor must be finite; factor must be positive")
    bins = array.shape[-1]
    source_positions = np.arange(bins, dtype=np.float64)
    query = source_positions / factor
    if array.ndim == 1:
        return np.interp(query, source_positions, array)
    return np.stack([np.interp(query, source_positions, row) for row in array])


def normalized_log_shape(spectra: np.ndarray, voiced: np.ndarray) -> np.ndarray:
    """Mean per-frame-energy-normalized log spectrum over voiced frames."""
    spectra = np.asarray(spectra, dtype=np.float64)
    voiced = np.asarray(voiced, dtype=bool)
    if spectra.ndim != 2 or voiced.shape != (spectra.shape[0],):
        raise ValueError("spectra must be frames x bins and voiced must match frames")
    if not np.isfinite(spectra).all() or np.any(spectra <= 0):
        raise ValueError("spectra must be finite and strictly positive")
    if int(voiced.sum()) < 1:
        raise ValueError("at least one voiced frame is required")
    log_spectra = np.log(spectra[voiced])
    centered = log_spectra - log_spectra.mean(axis=1, keepdims=True)
    return centered.mean(axis=0)


def map_log_f0(source_f0: np.ndarray, source_stats: tuple[float, float, float],
               target_stats: tuple[float, float, float], strength: float = 1.0,
               bounds_hz: tuple[float, float] = (75.0, 400.0)) -> np.ndarray:
    """Map voiced log-F0 quantiles and interpolate with the original pitch."""
    f0 = np.asarray(source_f0, dtype=np.float64)
    if f0.ndim != 1 or not np.isfinite(f0).all() or np.any(f0 < 0):
        raise ValueError("source_f0 must be finite and nonnegative")
    if not np.isfinite(strength) or not 0 <= strength <= 1.5:
        raise ValueError("strength must be in [0, 1.5]")
    src_p10, src_median, src_p90 = source_stats
    tgt_p10, tgt_median, tgt_p90 = target_stats
    if min(src_p10, src_median, src_p90, tgt_p10, tgt_median, tgt_p90) <= 0:
        raise ValueError("F0 statistics must be positive")
    src_spread = np.log(src_p90) - np.log(src_p10)
    tgt_spread = np.log(tgt_p90) - np.log(tgt_p10)
    scale = float(np.clip(tgt_spread / src_spread, 0.5, 2.0)) if src_spread >= 0.05 else 1.0
    result = f0.copy()
    voiced = f0 > 0
    source_log = np.log(f0[voiced])
    mapped_log = np.log(tgt_median) + scale * (source_log - np.log(src_median))
    mixed_log = source_log + strength * (mapped_log - source_log)
    result[voiced] = np.clip(np.exp(mixed_log), bounds_hz[0], bounds_hz[1])
    return result


def targetize_spectra(spectra: np.ndarray, voiced: np.ndarray,
                      source_shape: np.ndarray, target_shape: np.ndarray,
                      warp_factor: float, strength: float, detail_gain: float,
                      delta_limit_db: float) -> np.ndarray:
    """Move voiced spectral shapes toward the target while preserving power.

    ``detail_gain`` controls phonetic residuals around the enrolled source mean.
    ``strength`` interpolates from the warped source frame to the targetized
    frame.  A finite dB clamp limits the static target/source correction.
    """
    spectra = np.asarray(spectra, dtype=np.float64)
    voiced = np.asarray(voiced, dtype=bool)
    source_shape = np.asarray(source_shape, dtype=np.float64)
    target_shape = np.asarray(target_shape, dtype=np.float64)
    if spectra.ndim != 2 or voiced.shape != (spectra.shape[0],):
        raise ValueError("spectra must be frames x bins and voiced must match frames")
    if source_shape.shape != (spectra.shape[1],) or target_shape.shape != source_shape.shape:
        raise ValueError("profile shapes must match the spectral bin count")
    scalars = (warp_factor, strength, detail_gain, delta_limit_db)
    if not np.isfinite(scalars).all() or warp_factor <= 0 or strength < 0 or detail_gain < 0:
        raise ValueError("mapping parameters must be finite and nonnegative")
    if delta_limit_db <= 0:
        raise ValueError("delta_limit_db must be positive")
    if not np.isfinite(spectra).all() or np.any(spectra <= 0):
        raise ValueError("spectra must be finite and strictly positive")

    result = spectra.copy()
    warped_source = warp_bins(source_shape, warp_factor)
    limit_ln_power = delta_limit_db * np.log(10.0) / 10.0
    static_delta = np.clip(target_shape - warped_source, -limit_ln_power, limit_ln_power)
    for index in np.flatnonzero(voiced):
        original = spectra[index]
        log_frame = np.log(original)
        centered = log_frame - log_frame.mean()
        warped_frame = warp_bins(centered, warp_factor)
        residual = warped_frame - warped_source
        targetized = warped_source + static_delta + detail_gain * residual
        mapped_shape = warped_frame + strength * (targetized - warped_frame)
        mapped = np.exp(mapped_shape)
        mapped *= original.sum() / max(float(mapped.sum()), 1e-18)
        result[index] = mapped
    if not np.isfinite(result).all() or np.any(result <= 0):
        raise RuntimeError("mapping produced invalid spectra")
    return result


def blend_aperiodicity(source_ap: np.ndarray, target_ap: np.ndarray,
                       voiced: np.ndarray, mix: float) -> np.ndarray:
    """Blend voiced aperiodicity toward a target mean in logit space."""
    source_ap = np.asarray(source_ap, dtype=np.float64)
    target_ap = np.asarray(target_ap, dtype=np.float64)
    voiced = np.asarray(voiced, dtype=bool)
    if source_ap.ndim != 2 or target_ap.shape != (source_ap.shape[1],):
        raise ValueError("target_ap must match the source bin count")
    if voiced.shape != (source_ap.shape[0],) or not 0 <= mix <= 1:
        raise ValueError("voiced shape or mix is invalid")
    eps = 1e-6
    src = np.clip(source_ap, eps, 1 - eps)
    tgt = np.clip(target_ap, eps, 1 - eps)
    src_logit = np.log(src / (1 - src))
    tgt_logit = np.log(tgt / (1 - tgt))
    result = src.copy()
    result[voiced] = 1 / (1 + np.exp(-((1 - mix) * src_logit[voiced] + mix * tgt_logit)))
    return np.clip(result, 0.001, 0.999999999999)
