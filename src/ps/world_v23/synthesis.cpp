//-----------------------------------------------------------------------------
// Prototype of the PS-side aperiodic-branch optimization (candidate c).
//
// Base: WORLD 0.3.5 synthesis.cpp (sha256
// 9888973e28f2194a0eb9807e18e36680f3d912bef3ddf174dc640fedc4e08b4c).
// This copy lives in build/generated/ps_opt_20261018/ and is the ONLY file of
// the synthesis path that is changed.  The upstream tree
// build/generated/world_source_v035/... is not touched.
//
// Change (aperiodic branch only):
//   The aperiodic response needs a minimum-phase spectrum built from
//   log(|sp| * ap^2) at every pulse (~2 pulses per 10 ms frame).  That call is
//   2 FFTs + 513 log + 513 exp/cos/sin and is 37% of the synthesis time.
//   Instead the minimum-phase spectra are pre-computed on a coarse grid of
//   parameter frames (the "parameter update" anchors) and each pulse
//   interpolates the complex spectrum of its two surrounding anchors.
//   Number of anchors = f0_length / stride + 1.  Stride 1 = one anchor per
//   10 ms frame (halves the calls); stride 20 = one anchor per 200 ms update
//   period (max saving, 5 anchors for 1 s audio).
//
// The periodic branch, the noise generation, the time base and the overlap-add
// are byte-for-byte the upstream algorithm.  The noise generator consumes the
// exact same randn() sequence per pulse, so the only difference is the
// aperiodic filter.
//
// Runtime knob: WORLD_AP_MINPHASE_STRIDE (default 1).  Kept as an environment
// variable so that the same binary can be used to sweep stride values without
// recompiling; the production point would be a compile-time constant.
//-----------------------------------------------------------------------------
#include "world/synthesis.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "world/common.h"
#include "world/constantnumbers.h"
#include "world/matlabfunctions.h"

namespace {

// Stride (in analysis frames) of the aperiodic minimum-phase anchor grid.
// 0 selects the untouched per-pulse reference path (diagnostic only).
int GetAperiodicAnchorStride() {
  const char *value = getenv("WORLD_AP_MINPHASE_STRIDE");
  if (value != 0) {
    const int stride = atoi(value);
    if (stride >= 0) return stride;
  }
  return 1;
}

// Aperiodic branch filters pre-computed on the parameter-frame grid.
struct AperiodicFilterTable {
  int number_of_anchors;
  int half_bins;
  int f0_length;
  int interpolation_mode;  // 0: complex lerp, 1: magnitude-corrected lerp
  int voiced_filter_count;
  int unvoiced_filter_count;
  int unstable_interval_count;
  int *anchor_frame;       // analysis frame index of each anchor
  // Intervals whose two anchors differ too much (hard onsets, voicing changes,
  // spectral bursts).  Pulses in those intervals fall back to the upstream
  // per-pulse minimum phase; the anchor interpolation is only used where the
  // filter changes slowly.  This is the hybrid safe path.
  char *unstable_interval; // [number_of_anchors] flag of interval [a, a+1]
  // Two variants per anchor, allocated only where a pulse actually uses them:
  // voiced pulses use log(|sp|*ap^2)/2, unvoiced pulses use log(|sp|)/2,
  // exactly like the upstream GetAperiodicResponse() branch.  Without this,
  // unvoiced pulses across a voiced/unvoiced transition get the suppressed
  // (voiced) filter and the onset transient is attenuated.
  double **voiced_real;    // [number_of_anchors][half_bins + 1] or NULL
  double **voiced_imag;
  double **unvoiced_real;
  double **unvoiced_imag;
};

int GetAperiodicInterpolationMode() {
  const char *value = getenv("WORLD_AP_INTERP_MODE");
  if (value != 0) {
    const int mode = atoi(value);
    if (mode >= 0 && mode <= 1) return mode;
  }
  return 0;
}

// Intervals whose anchor filter energies differ by more than this factor fall
// back to the per-pulse reference path (0 disables the fallback).
// 8.0 (9 dB) keeps the multi-sentence quality at corr >= 0.9995 while only
// ~7% of the pulses fall back (board cost of a fallback pulse ~0.65 ms).
double GetAperiodicFallbackRatio() {
  const char *value = getenv("WORLD_AP_FALLBACK_RATIO");
  if (value != 0) {
    const double ratio = atof(value);
    if (ratio >= 0.0) return ratio;
  }
  return 8.0;
}

// Find the anchor interval [low, low+1] and the interpolation weight for a
// pulse time.  Shared by the anchor pre-pass and the per-pulse interpolation.
static void FindAnchorInterval(const AperiodicFilterTable *table,
    double pulse_time, double frame_period, int *low, double *fraction) {
  const int last_frame = table->f0_length - 1;
  double position = pulse_time / frame_period;
  if (position < 0.0) position = 0.0;
  if (position > last_frame) position = last_frame;
  if (table->number_of_anchors == 1) {
    *low = 0;
    *fraction = 0.0;
    return;
  }
  int index = static_cast<int>(floor(position / static_cast<double>(
    table->anchor_frame[1] - table->anchor_frame[0])));
  if (index > table->number_of_anchors - 2) index = table->number_of_anchors - 2;
  if (index < 0) index = 0;
  const double span =
    table->anchor_frame[index + 1] - table->anchor_frame[index];
  double weight = (position - table->anchor_frame[index]) / span;
  if (weight < 0.0) weight = 0.0;
  if (weight > 1.0) weight = 1.0;
  *low = index;
  *fraction = weight;
}

static void InitializeAperiodicFilterTable(int fft_size, int f0_length,
    const double * const *spectrogram, const double * const *aperiodicity,
    int stride, const double *pulse_locations,
    const int *pulse_locations_index, const double *interpolated_vuv,
    int number_of_pulses, double frame_period,
    MinimumPhaseAnalysis *minimum_phase, AperiodicFilterTable *table) {
  const int last_frame = f0_length - 1;
  table->half_bins = fft_size / 2;
  table->f0_length = f0_length;
  int count = last_frame / stride + 1;
  if (last_frame % stride != 0) ++count;
  table->number_of_anchors = count;
  table->interpolation_mode = GetAperiodicInterpolationMode();
  table->voiced_filter_count = 0;
  table->unvoiced_filter_count = 0;
  table->anchor_frame = new int[count];
  for (int anchor = 0; anchor < count; ++anchor) {
    int frame = anchor * stride;
    if (frame > last_frame) frame = last_frame;
    table->anchor_frame[anchor] = frame;
  }
  table->voiced_real = new double *[count]();
  table->voiced_imag = new double *[count]();
  table->unvoiced_real = new double *[count]();
  table->unvoiced_imag = new double *[count]();
  table->unstable_interval = new char[count]();
  table->unstable_interval_count = 0;

  // Which variants does the actual pulse sequence consume?
  char *need_voiced = new char[count]();
  char *need_unvoiced = new char[count]();
  for (int i = 0; i < number_of_pulses; ++i) {
    int low = 0;
    double fraction = 0.0;
    FindAnchorInterval(table, pulse_locations[i], frame_period, &low, &fraction);
    const int high = (low + 1 < count) ? low + 1 : low;
    if (interpolated_vuv[pulse_locations_index[i]] > 0.5) {
      need_voiced[low] = 1;
      need_voiced[high] = 1;
    } else {
      need_unvoiced[low] = 1;
      need_unvoiced[high] = 1;
    }
  }

  const int bins = table->half_bins + 1;
  double *voiced_energy = new double[count]();
  double *unvoiced_energy = new double[count]();
  for (int anchor = 0; anchor < count; ++anchor) {
    const int frame = table->anchor_frame[anchor];
    if (need_voiced[anchor]) {
      table->voiced_real[anchor] = new double[bins];
      table->voiced_imag[anchor] = new double[bins];
      // Same formula as GetAperiodicRatio() but evaluated at the frame itself:
      // aperiodicity = pow(GetSafeAperiodicity(ap), 2.0), no interpolation.
      for (int i = 0; i < bins; ++i)
        minimum_phase->log_spectrum[i] = log(fabs(spectrogram[frame][i]) *
          pow(GetSafeAperiodicity(aperiodicity[frame][i]), 2.0)) / 2.0;
      GetMinimumPhaseSpectrum(minimum_phase);
      for (int i = 0; i < bins; ++i) {
        table->voiced_real[anchor][i] =
          minimum_phase->minimum_phase_spectrum[i][0];
        table->voiced_imag[anchor][i] =
          minimum_phase->minimum_phase_spectrum[i][1];
        voiced_energy[anchor] +=
          table->voiced_real[anchor][i] * table->voiced_real[anchor][i] +
          table->voiced_imag[anchor][i] * table->voiced_imag[anchor][i];
      }
      ++table->voiced_filter_count;
    }
    if (need_unvoiced[anchor]) {
      table->unvoiced_real[anchor] = new double[bins];
      table->unvoiced_imag[anchor] = new double[bins];
      // Upstream unvoiced branch: log(spectrum) / 2.
      for (int i = 0; i < bins; ++i)
        minimum_phase->log_spectrum[i] = log(fabs(spectrogram[frame][i])) / 2.0;
      GetMinimumPhaseSpectrum(minimum_phase);
      for (int i = 0; i < bins; ++i) {
        table->unvoiced_real[anchor][i] =
          minimum_phase->minimum_phase_spectrum[i][0];
        table->unvoiced_imag[anchor][i] =
          minimum_phase->minimum_phase_spectrum[i][1];
        unvoiced_energy[anchor] +=
          table->unvoiced_real[anchor][i] * table->unvoiced_real[anchor][i] +
          table->unvoiced_imag[anchor][i] * table->unvoiced_imag[anchor][i];
      }
      ++table->unvoiced_filter_count;
    }
  }

  // Mark intervals where the two anchors are too different for a safe complex
  // interpolation (hard onsets, voicing flips).  Pulses there use the upstream
  // per-pulse minimum phase path instead.
  const double fallback_ratio = GetAperiodicFallbackRatio();
  if (fallback_ratio > 0.0) {
    for (int anchor = 0; anchor + 1 < count; ++anchor) {
      double low_energy = -1.0, high_energy = -1.0;
      if (table->voiced_real[anchor] != 0 &&
          table->voiced_real[anchor + 1] != 0) {
        low_energy = voiced_energy[anchor];
        high_energy = voiced_energy[anchor + 1];
      } else if (table->unvoiced_real[anchor] != 0 &&
                 table->unvoiced_real[anchor + 1] != 0) {
        low_energy = unvoiced_energy[anchor];
        high_energy = unvoiced_energy[anchor + 1];
      }
      if (low_energy <= 0.0 || high_energy <= 0.0) {
        table->unstable_interval[anchor] = 1;
      } else {
        const double ratio = low_energy > high_energy
          ? low_energy / high_energy : high_energy / low_energy;
        if (ratio > fallback_ratio) table->unstable_interval[anchor] = 1;
      }
      if (table->unstable_interval[anchor]) ++table->unstable_interval_count;
    }
  }
  delete[] unvoiced_energy;
  delete[] voiced_energy;
  delete[] need_unvoiced;
  delete[] need_voiced;
}

static void DestroyAperiodicFilterTable(AperiodicFilterTable *table) {
  for (int anchor = 0; anchor < table->number_of_anchors; ++anchor) {
    delete[] table->voiced_real[anchor];
    delete[] table->voiced_imag[anchor];
    delete[] table->unvoiced_real[anchor];
    delete[] table->unvoiced_imag[anchor];
  }
  delete[] table->voiced_real;
  delete[] table->voiced_imag;
  delete[] table->unvoiced_real;
  delete[] table->unvoiced_imag;
  delete[] table->unstable_interval;
  delete[] table->anchor_frame;
  table->number_of_anchors = 0;
}

// Linear interpolation of the complex minimum-phase spectrum at a pulse time,
// using the filter variant that matches the pulse voicing.
static void GetAperiodicFilter(const AperiodicFilterTable *table, int voiced,
    double pulse_time, double frame_period, double *real, double *imag) {
  const int bins = table->half_bins + 1;
  int low = 0;
  double fraction = 0.0;
  FindAnchorInterval(table, pulse_time, frame_period, &low, &fraction);
  const int high =
    (low + 1 < table->number_of_anchors) ? low + 1 : low;

  int use_voiced = voiced ? 1 : 0;
  if (use_voiced &&
      (table->voiced_real[low] == 0 || table->voiced_real[high] == 0))
    use_voiced = 0;
  if (!use_voiced &&
      (table->unvoiced_real[low] == 0 || table->unvoiced_real[high] == 0))
    use_voiced = 1;
  double *const *table_real =
    use_voiced ? table->voiced_real : table->unvoiced_real;
  double *const *table_imag =
    use_voiced ? table->voiced_imag : table->unvoiced_imag;
  if (table_real[low] == 0) {
    for (int i = 0; i < bins; ++i) {
      real[i] = 0.0;
      imag[i] = 0.0;
    }
    return;
  }

  const double *low_real = table_real[low];
  const double *low_imag = table_imag[low];
  const double *high_real = table_real[high];
  const double *high_imag = table_imag[high];
  if (table->interpolation_mode == 0) {
    for (int i = 0; i < bins; ++i) {
      real[i] = (1.0 - fraction) * low_real[i] + fraction * high_real[i];
      imag[i] = (1.0 - fraction) * low_imag[i] + fraction * high_imag[i];
    }
  } else {
    // Magnitude-corrected complex interpolation: keep the interpolated phase
    // but rescale each bin to the linear interpolation of the magnitudes, so
    // that two filters with different phase cannot cancel each other.
    for (int i = 0; i < bins; ++i) {
      const double low_magnitude =
        sqrt(low_real[i] * low_real[i] + low_imag[i] * low_imag[i]);
      const double high_magnitude =
        sqrt(high_real[i] * high_real[i] + high_imag[i] * high_imag[i]);
      const double target_magnitude =
        (1.0 - fraction) * low_magnitude + fraction * high_magnitude;
      const double lerp_real =
        (1.0 - fraction) * low_real[i] + fraction * high_real[i];
      const double lerp_imag =
        (1.0 - fraction) * low_imag[i] + fraction * high_imag[i];
      const double lerp_magnitude = sqrt(lerp_real * lerp_real +
                                        lerp_imag * lerp_imag);
      const double scale = lerp_magnitude > 1e-12 ?
        target_magnitude / lerp_magnitude : 1.0;
      real[i] = lerp_real * scale;
      imag[i] = lerp_imag * scale;
    }
  }
}

//-----------------------------------------------------------------------------
// GetNoiseSpectrum() is unchanged from the upstream implementation.
//-----------------------------------------------------------------------------
static void GetNoiseSpectrum(int noise_size, int fft_size,
    const ForwardRealFFT *forward_real_fft, RandnState *randn_state) {
  double average = 0.0;
  for (int i = 0; i < noise_size; ++i) {
    forward_real_fft->waveform[i] = randn(randn_state);
    average += forward_real_fft->waveform[i];
  }

  average /= noise_size;
  for (int i = 0; i < noise_size; ++i)
    forward_real_fft->waveform[i] -= average;
  for (int i = noise_size; i < fft_size; ++i)
    forward_real_fft->waveform[i] = 0.0;
  fft_execute(forward_real_fft->forward_fft);
}

//-----------------------------------------------------------------------------
// GetAperiodicResponse() with a pre-computed minimum-phase filter.
// The excitation, inverse FFT and fftshift are identical to upstream.
//-----------------------------------------------------------------------------
static void GetAperiodicResponse(const double *filter_real,
    const double *filter_imag, int noise_size, int fft_size,
    const ForwardRealFFT *forward_real_fft,
    const InverseRealFFT *inverse_real_fft, double *aperiodic_response,
    RandnState *randn_state) {
  GetNoiseSpectrum(noise_size, fft_size, forward_real_fft, randn_state);

  for (int i = 0; i <= fft_size / 2; ++i) {
    inverse_real_fft->spectrum[i][0] =
      filter_real[i] * forward_real_fft->spectrum[i][0] -
      filter_imag[i] * forward_real_fft->spectrum[i][1];
    inverse_real_fft->spectrum[i][1] =
      filter_real[i] * forward_real_fft->spectrum[i][1] +
      filter_imag[i] * forward_real_fft->spectrum[i][0];
  }
  fft_execute(inverse_real_fft->inverse_fft);
  fftshift(inverse_real_fft->waveform, fft_size, aperiodic_response);
}

//-----------------------------------------------------------------------------
// GetAperiodicResponsePerPulse() is the untouched upstream reference path.
// It is only reachable through WORLD_AP_MINPHASE_STRIDE=0 and exists to prove
// that the refactoring itself (buffers, function boundaries) is neutral.
//-----------------------------------------------------------------------------
static void GetAperiodicResponsePerPulse(int noise_size, int fft_size,
    const double *spectrum, const double *aperiodic_ratio, double current_vuv,
    const ForwardRealFFT *forward_real_fft,
    const InverseRealFFT *inverse_real_fft,
    const MinimumPhaseAnalysis *minimum_phase, double *aperiodic_response,
    RandnState *randn_state) {
  GetNoiseSpectrum(noise_size, fft_size, forward_real_fft, randn_state);

  if (current_vuv != 0.0)
    for (int i = 0; i <= minimum_phase->fft_size / 2; ++i)
      minimum_phase->log_spectrum[i] =
        log(spectrum[i] * aperiodic_ratio[i]) / 2.0;
  else
    for (int i = 0; i <= minimum_phase->fft_size / 2; ++i)
      minimum_phase->log_spectrum[i] = log(spectrum[i]) / 2.0;
  GetMinimumPhaseSpectrum(minimum_phase);

  for (int i = 0; i <= fft_size / 2; ++i) {
    inverse_real_fft->spectrum[i][0] =
      minimum_phase->minimum_phase_spectrum[i][0] *
      forward_real_fft->spectrum[i][0] -
      minimum_phase->minimum_phase_spectrum[i][1] *
      forward_real_fft->spectrum[i][1];
    inverse_real_fft->spectrum[i][1] =
      minimum_phase->minimum_phase_spectrum[i][0] *
      forward_real_fft->spectrum[i][1] +
      minimum_phase->minimum_phase_spectrum[i][1] *
      forward_real_fft->spectrum[i][0];
  }
  fft_execute(inverse_real_fft->inverse_fft);
  fftshift(inverse_real_fft->waveform, fft_size, aperiodic_response);
}

//-----------------------------------------------------------------------------
// RemoveDCComponent()
//-----------------------------------------------------------------------------
static void RemoveDCComponent(const double *periodic_response, int fft_size,
    const double *dc_remover, double *new_periodic_response) {
  double dc_component = 0.0;
  for (int i = fft_size / 2; i < fft_size; ++i)
    dc_component += periodic_response[i];
  for (int i = 0; i < fft_size / 2; ++i)
    new_periodic_response[i] = -dc_component * dc_remover[i];
  for (int i = fft_size / 2; i < fft_size; ++i)
    new_periodic_response[i] -= dc_component * dc_remover[i];
}

//-----------------------------------------------------------------------------
// GetSpectrumWithFractionalTimeShift()
//-----------------------------------------------------------------------------
static void GetSpectrumWithFractionalTimeShift(int fft_size,
    double coefficient, const InverseRealFFT *inverse_real_fft) {
  double re, im, re2, im2;
  for (int i = 0; i <= fft_size / 2; ++i) {
    re = inverse_real_fft->spectrum[i][0];
    im = inverse_real_fft->spectrum[i][1];
    re2 = cos(coefficient * i);
    im2 = sqrt(1.0 - re2 * re2);  // sin(pshift)

    inverse_real_fft->spectrum[i][0] = re * re2 + im * im2;
    inverse_real_fft->spectrum[i][1] = im * re2 - re * im2;
  }
}

//-----------------------------------------------------------------------------
// GetPeriodicResponse()
//-----------------------------------------------------------------------------
static void GetPeriodicResponse(int fft_size, const double *spectrum,
    const double *aperiodic_ratio, double current_vuv,
    const InverseRealFFT *inverse_real_fft,
    const MinimumPhaseAnalysis *minimum_phase, const double *dc_remover,
    double fractional_time_shift, int fs, double *periodic_response) {
  if (current_vuv <= 0.5 || aperiodic_ratio[0] > 0.999) {
    for (int i = 0; i < fft_size; ++i) periodic_response[i] = 0.0;
    return;
  }

  for (int i = 0; i <= minimum_phase->fft_size / 2; ++i)
    minimum_phase->log_spectrum[i] =
      log(spectrum[i] * (1.0 - aperiodic_ratio[i]) +
      world::kMySafeGuardMinimum) / 2.0;
  GetMinimumPhaseSpectrum(minimum_phase);

  for (int i = 0; i <= fft_size / 2; ++i) {
    inverse_real_fft->spectrum[i][0] =
      minimum_phase->minimum_phase_spectrum[i][0];
    inverse_real_fft->spectrum[i][1] =
      minimum_phase->minimum_phase_spectrum[i][1];
  }

  // apply fractional time delay of fractional_time_shift seconds
  // using linear phase shift
  double coefficient =
    2.0 * world::kPi * fractional_time_shift * fs / fft_size;
  GetSpectrumWithFractionalTimeShift(fft_size, coefficient, inverse_real_fft);

  fft_execute(inverse_real_fft->inverse_fft);
  fftshift(inverse_real_fft->waveform, fft_size, periodic_response);
  RemoveDCComponent(periodic_response, fft_size, dc_remover,
      periodic_response);
}

static void GetSpectralEnvelope(double current_time, double frame_period,
    int f0_length, const double * const *spectrogram, int fft_size,
    double *spectral_envelope) {
  int current_frame_floor = MyMinInt(f0_length - 1,
    static_cast<int>(floor(current_time / frame_period)));
  int current_frame_ceil = MyMinInt(f0_length - 1,
    static_cast<int>(ceil(current_time / frame_period)));
  double interpolation = current_time / frame_period - current_frame_floor;

  if (current_frame_floor == current_frame_ceil)
    for (int i = 0; i <= fft_size / 2; ++i)
      spectral_envelope[i] = fabs(spectrogram[current_frame_floor][i]);
  else
    for (int i = 0; i <= fft_size / 2; ++i)
      spectral_envelope[i] =
        (1.0 - interpolation) * fabs(spectrogram[current_frame_floor][i]) +
        interpolation * fabs(spectrogram[current_frame_ceil][i]);
}

static void GetAperiodicRatio(double current_time, double frame_period,
    int f0_length, const double * const *aperiodicity, int fft_size,
    double *aperiodic_spectrum) {
  int current_frame_floor = MyMinInt(f0_length - 1,
    static_cast<int>(floor(current_time / frame_period)));
  int current_frame_ceil = MyMinInt(f0_length - 1,
    static_cast<int>(ceil(current_time / frame_period)));
  double interpolation = current_time / frame_period - current_frame_floor;

  if (current_frame_floor == current_frame_ceil)
    for (int i = 0; i <= fft_size / 2; ++i)
      aperiodic_spectrum[i] =
        pow(GetSafeAperiodicity(aperiodicity[current_frame_floor][i]), 2.0);
  else
    for (int i = 0; i <= fft_size / 2; ++i)
      aperiodic_spectrum[i] = pow((1.0 - interpolation) *
          GetSafeAperiodicity(aperiodicity[current_frame_floor][i]) +
          interpolation *
          GetSafeAperiodicity(aperiodicity[current_frame_ceil][i]), 2.0);
}

//-----------------------------------------------------------------------------
// GetOneFrameSegment() calculates a periodic and aperiodic response at a time.
// Only the aperiodic minimum phase filter is taken from the anchor table.
//-----------------------------------------------------------------------------
static void GetOneFrameSegment(double current_vuv, int noise_size,
    const double * const *spectrogram, int fft_size,
    const double * const *aperiodicity, int f0_length, double frame_period,
    double current_time, double fractional_time_shift, int fs,
    const ForwardRealFFT *forward_real_fft,
    const InverseRealFFT *inverse_real_fft,
    const MinimumPhaseAnalysis *minimum_phase, const double *dc_remover,
    const AperiodicFilterTable *anchor_table, double *spectral_envelope,
    double *aperiodic_ratio, double *periodic_response,
    double *aperiodic_response, double *filter_real, double *filter_imag,
    double *response, RandnState* randn_state, int pulse_index,
    int debug_limit) {
  const bool use_anchor_table = anchor_table->number_of_anchors > 0;
  bool use_anchor_filter = use_anchor_table;
  if (use_anchor_filter) {
    int low = 0;
    double fraction = 0.0;
    FindAnchorInterval(anchor_table, current_time, frame_period, &low,
        &fraction);
    if (anchor_table->unstable_interval[low]) use_anchor_filter = false;
  }
  // The polar synthesis only needs the spectral envelope and the aperiodicity
  // when the pulse is voiced; unvoiced pulses only use the aperiodic branch.
  // The reference path (fallback or stride 0) needs both for every pulse.
  if (current_vuv > 0.5 || !use_anchor_filter) {
    GetSpectralEnvelope(current_time, frame_period, f0_length, spectrogram,
        fft_size, spectral_envelope);
    GetAperiodicRatio(current_time, frame_period, f0_length, aperiodicity,
        fft_size, aperiodic_ratio);
  }
  if (current_vuv > 0.5) {
    GetPeriodicResponse(fft_size, spectral_envelope, aperiodic_ratio,
        current_vuv, inverse_real_fft, minimum_phase, dc_remover,
        fractional_time_shift, fs, periodic_response);
  } else {
    for (int i = 0; i < fft_size; ++i) periodic_response[i] = 0.0;
  }

  if (use_anchor_filter) {
    GetAperiodicFilter(anchor_table, current_vuv > 0.5 ? 1 : 0, current_time,
        frame_period, filter_real, filter_imag);
    GetAperiodicResponse(filter_real, filter_imag, noise_size, fft_size,
        forward_real_fft, inverse_real_fft, aperiodic_response, randn_state);
  } else {
    GetAperiodicResponsePerPulse(noise_size, fft_size, spectral_envelope,
        aperiodic_ratio, current_vuv, forward_real_fft, inverse_real_fft,
        minimum_phase, aperiodic_response, randn_state);
  }

  if (use_anchor_filter && pulse_index < debug_limit) {
    // Diagnostic (WORLD_AP_DEBUG_PULSES): compare the interpolated anchor
    // filter with the per-pulse reference filter at the same time.
    double *debug_envelope = spectral_envelope;
    double *debug_ratio = aperiodic_ratio;
    if (current_vuv <= 0.5) {
      GetSpectralEnvelope(current_time, frame_period, f0_length, spectrogram,
          fft_size, debug_envelope);
      GetAperiodicRatio(current_time, frame_period, f0_length, aperiodicity,
          fft_size, debug_ratio);
    }
    for (int i = 0; i <= minimum_phase->fft_size / 2; ++i)
      minimum_phase->log_spectrum[i] = (current_vuv > 0.5)
        ? log(debug_envelope[i] * debug_ratio[i]) / 2.0
        : log(debug_envelope[i]) / 2.0;
    GetMinimumPhaseSpectrum(minimum_phase);
    double reference_energy = 0.0;
    double anchor_energy = 0.0;
    for (int i = 0; i <= minimum_phase->fft_size / 2; ++i) {
      reference_energy +=
        minimum_phase->minimum_phase_spectrum[i][0] *
        minimum_phase->minimum_phase_spectrum[i][0] +
        minimum_phase->minimum_phase_spectrum[i][1] *
        minimum_phase->minimum_phase_spectrum[i][1];
      anchor_energy += filter_real[i] * filter_real[i] +
        filter_imag[i] * filter_imag[i];
    }
    fprintf(stderr,
        "AP_DEBUG pulse=%d t=%.6f vuv=%.0f noise=%d refE=%.6e anchorE=%.6e "
        "ratio=%.4f\n", pulse_index, current_time, current_vuv, noise_size,
        reference_energy, anchor_energy, anchor_energy / reference_energy);
  }

  double sqrt_noise_size = sqrt(static_cast<double>(noise_size));
  for (int i = 0; i < fft_size; ++i)
    response[i] =
      (periodic_response[i] * sqrt_noise_size + aperiodic_response[i]) /
      fft_size;
}

static void GetTemporalParametersForTimeBase(const double *f0, int f0_length,
    int fs, int y_length, double frame_period, double lowest_f0,
    double *time_axis, double *coarse_time_axis, double *coarse_f0,
    double *coarse_vuv) {
  for (int i = 0; i < y_length; ++i)
    time_axis[i] = i / static_cast<double>(fs);
  // the array 'coarse_time_axis' is supposed to have 'f0_length + 1' positions
  for (int i = 0; i < f0_length; ++i) {
    coarse_time_axis[i] = i * frame_period;
    coarse_f0[i] = f0[i] < lowest_f0 ? 0.0 : f0[i];
    coarse_vuv[i] = coarse_f0[i] == 0.0 ? 0.0 : 1.0;
  }
  coarse_time_axis[f0_length] = f0_length * frame_period;
  coarse_f0[f0_length] = coarse_f0[f0_length - 1] * 2 -
    coarse_f0[f0_length - 2];
  coarse_vuv[f0_length] = coarse_vuv[f0_length - 1] * 2 -
    coarse_vuv[f0_length - 2];
}

static int GetPulseLocationsForTimeBase(const double *interpolated_f0,
    const double *time_axis, int y_length, int fs, double *pulse_locations,
    int *pulse_locations_index, double *pulse_locations_time_shift) {
  double *total_phase = new double[y_length];
  double *wrap_phase = new double[y_length];
  double *wrap_phase_abs = new double[y_length - 1];
  total_phase[0] = 2.0 * world::kPi * interpolated_f0[0] / fs;
  wrap_phase[0] = fmod(total_phase[0], 2.0 * world::kPi);
  for (int i = 1; i < y_length; ++i) {
    total_phase[i] = total_phase[i - 1] +
      2.0 * world::kPi * interpolated_f0[i] / fs;
    wrap_phase[i] = fmod(total_phase[i], 2.0 * world::kPi);
    wrap_phase_abs[i - 1] = fabs(wrap_phase[i] - wrap_phase[i - 1]);
  }

  int number_of_pulses = 0;
  for (int i = 0; i < y_length - 1; ++i) {
    if (wrap_phase_abs[i] > world::kPi) {
      pulse_locations[number_of_pulses] = time_axis[i];
      pulse_locations_index[number_of_pulses] = i;

      // calculate the time shift in seconds between exact fractional pulse
      // position and the integer pulse position (sample i)
      // as we don't have access to the exact pulse position, we infer it
      // from the point between sample i and sample i + 1 where the
      // accummulated phase cross a multiple of 2pi
      // this point is found by solving y1 + x * (y2 - y1) = 0 for x, where y1
      // and y2 are the phases corresponding to sample i and i + 1, offset so
      // they cross zero; x >= 0
      double y1 = wrap_phase[i] - 2.0 * world::kPi;
      double y2 = wrap_phase[i + 1];
      double x = -y1 / (y2 - y1);
      pulse_locations_time_shift[number_of_pulses] = x / fs;

      ++number_of_pulses;
    }
  }

  delete[] wrap_phase_abs;
  delete[] wrap_phase;
  delete[] total_phase;

  return number_of_pulses;
}

static int GetTimeBase(const double *f0, int f0_length, int fs,
    double frame_period, int y_length, double lowest_f0,
    double *pulse_locations, int *pulse_locations_index,
    double *pulse_locations_time_shift, double *interpolated_vuv) {
  double *time_axis = new double[y_length];
  double *coarse_time_axis = new double[f0_length + 1];
  double *coarse_f0 = new double[f0_length + 1];
  double *coarse_vuv = new double[f0_length + 1];
  GetTemporalParametersForTimeBase(f0, f0_length, fs, y_length, frame_period,
      lowest_f0, time_axis, coarse_time_axis, coarse_f0, coarse_vuv);
  double *interpolated_f0 = new double[y_length];
  interp1(coarse_time_axis, coarse_f0, f0_length + 1,
      time_axis, y_length, interpolated_f0);
  interp1(coarse_time_axis, coarse_vuv, f0_length + 1,
      time_axis, y_length, interpolated_vuv);

  for (int i = 0; i < y_length; ++i) {
    interpolated_vuv[i] = interpolated_vuv[i] > 0.5 ? 1.0 : 0.0;
    interpolated_f0[i] =
      interpolated_vuv[i] == 0.0 ? world::kDefaultF0 : interpolated_f0[i];
  }

  int number_of_pulses = GetPulseLocationsForTimeBase(interpolated_f0,
      time_axis, y_length, fs, pulse_locations, pulse_locations_index,
      pulse_locations_time_shift);

  delete[] coarse_vuv;
  delete[] coarse_f0;
  delete[] coarse_time_axis;
  delete[] time_axis;
  delete[] interpolated_f0;

  return number_of_pulses;
}

static void GetDCRemover(int fft_size, double *dc_remover) {
  double dc_component = 0.0;
  for (int i = 0; i < fft_size / 2; ++i) {
    dc_remover[i] = 0.5 -
      0.5 * cos(2.0 * world::kPi * (i + 1.0) / (1.0 + fft_size));
    dc_remover[fft_size - i - 1] = dc_remover[i];
    dc_component += dc_remover[i] * 2.0;
  }
  for (int i = 0; i < fft_size / 2; ++i) {
    dc_remover[i] /= dc_component;
    dc_remover[fft_size - i - 1] = dc_remover[i];
  }
}

}  // namespace

void Synthesis(const double *f0, int f0_length,
    const double * const *spectrogram, const double * const *aperiodicity,
    int fft_size, double frame_period, int fs, int y_length, double *y) {
  RandnState randn_state = {};
  randn_reseed(&randn_state);

  double *impulse_response = new double[fft_size];

  for (int i = 0; i < y_length; ++i) y[i] = 0.0;

  MinimumPhaseAnalysis minimum_phase = {0};
  InitializeMinimumPhaseAnalysis(fft_size, &minimum_phase);
  InverseRealFFT inverse_real_fft = {0};
  InitializeInverseRealFFT(fft_size, &inverse_real_fft);
  ForwardRealFFT forward_real_fft = {0};
  InitializeForwardRealFFT(fft_size, &forward_real_fft);

  double *pulse_locations = new double[y_length];
  int *pulse_locations_index = new int[y_length];
  double *pulse_locations_time_shift = new double[y_length];
  double *interpolated_vuv = new double[y_length];
  int number_of_pulses = GetTimeBase(f0, f0_length, fs, frame_period / 1000.0,
      y_length, fs / fft_size + 1.0, pulse_locations, pulse_locations_index,
      pulse_locations_time_shift, interpolated_vuv);

  double *dc_remover = new double[fft_size];
  GetDCRemover(fft_size, dc_remover);

  const double frame_period_seconds = frame_period / 1000.0;
  const int anchor_stride = GetAperiodicAnchorStride();
  AperiodicFilterTable anchor_table = {0};
  if (anchor_stride > 0)
    InitializeAperiodicFilterTable(fft_size, f0_length, spectrogram,
        aperiodicity, anchor_stride, pulse_locations, pulse_locations_index,
        interpolated_vuv, number_of_pulses, frame_period_seconds,
        &minimum_phase, &anchor_table);
  int voiced_pulse_count = 0;
  int fallback_pulse_count = 0;
  for (int i = 0; i < number_of_pulses; ++i) {
    if (interpolated_vuv[pulse_locations_index[i]] > 0.5) ++voiced_pulse_count;
    int low = 0;
    double fraction = 0.0;
    FindAnchorInterval(&anchor_table, pulse_locations[i], frame_period_seconds,
        &low, &fraction);
    if (anchor_table.unstable_interval[low]) ++fallback_pulse_count;
  }
  fprintf(stderr,
      "AP_MINPHASE_ANCHORS stride=%d anchors=%d frames=%d pulses=%d "
      "voiced_pulses=%d voiced_filter_calls=%d unvoiced_filter_calls=%d "
      "fallback_intervals=%d fallback_pulses=%d\n",
      anchor_stride, anchor_table.number_of_anchors, f0_length,
      number_of_pulses, voiced_pulse_count, anchor_table.voiced_filter_count,
      anchor_table.unvoiced_filter_count, anchor_table.unstable_interval_count,
      fallback_pulse_count);

  double *spectral_envelope = new double[fft_size];
  double *aperiodic_ratio = new double[fft_size];
  double *periodic_response = new double[fft_size];
  double *aperiodic_response = new double[fft_size];
  double *filter_real = new double[fft_size];
  double *filter_imag = new double[fft_size];

  int noise_size;
  int index, offset, lower_limit, upper_limit;
  const char *debug_value = getenv("WORLD_AP_DEBUG_PULSES");
  const int debug_limit = debug_value != 0 ? atoi(debug_value) : 0;
  for (int i = 0; i < number_of_pulses; ++i) {
    noise_size = pulse_locations_index[MyMinInt(number_of_pulses - 1, i + 1)] -
      pulse_locations_index[i];

    GetOneFrameSegment(interpolated_vuv[pulse_locations_index[i]], noise_size,
        spectrogram, fft_size, aperiodicity, f0_length, frame_period_seconds,
        pulse_locations[i], pulse_locations_time_shift[i], fs,
        &forward_real_fft, &inverse_real_fft, &minimum_phase, dc_remover,
        &anchor_table, spectral_envelope, aperiodic_ratio, periodic_response,
        aperiodic_response, filter_real, filter_imag, impulse_response,
        &randn_state, i, debug_limit);
    offset = pulse_locations_index[i] - fft_size / 2 + 1;
    lower_limit = MyMaxInt(0, -offset);
    upper_limit = MyMinInt(fft_size, y_length - offset);
    for (int j = lower_limit; j < upper_limit; ++j) {
      index = j + offset;
      y[index] += impulse_response[j];
    }
  }

  delete[] filter_imag;
  delete[] filter_real;
  delete[] aperiodic_response;
  delete[] periodic_response;
  delete[] aperiodic_ratio;
  delete[] spectral_envelope;
  DestroyAperiodicFilterTable(&anchor_table);
  delete[] dc_remover;
  delete[] pulse_locations;
  delete[] pulse_locations_index;
  delete[] pulse_locations_time_shift;
  delete[] interpolated_vuv;

  DestroyMinimumPhaseAnalysis(&minimum_phase);
  DestroyInverseRealFFT(&inverse_real_fft);
  DestroyForwardRealFFT(&forward_real_fft);

  delete[] impulse_response;
}
