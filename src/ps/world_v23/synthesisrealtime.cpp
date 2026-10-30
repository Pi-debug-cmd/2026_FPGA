//-----------------------------------------------------------------------------
// PS aperiodic-batch streaming synthesizer (candidate c, real-time落地版).
//
// Base: WORLD 0.3.5 synthesisrealtime.cpp (sha256 6d0a1b04b4f7b1a5f4c5f7a7b2b9
// ... see build manifest; upstream file untouched).
//
// What changed vs upstream:
//   * The per-pulse aperiodic minimum-phase construction (2 FFTs + 513 log +
//     513 exp/cos/sin) is replaced by a rolling "anchor" table: one filter per
//     10 ms analysis frame, built lazily when a pulse first needs it, and
//     linearly interpolated in the complex spectrum at the pulse position.
//   * Two variants per anchor (voiced = log(|sp|*ap^2)/2, unvoiced = log|sp|/2)
//     are built only where used, matching the upstream vuv branch.
//   * Transition fallback: if the two bracketing anchors differ by more than
//     WORLD_AP_FALLBACK_RATIO in filter energy (hard onsets, vuv flips), the
//     pulse uses the upstream per-pulse minimum phase instead.
//   * Upstream per-pulse heap allocations (4 x fft_size doubles) become
//     preallocated scratch buffers.
//
// Interface contract with the streaming frame (world_live_stream.cpp and the
// file-streaming probe):
//   AddParameters(f0, 20, sp, ap, synth);      // one 200 ms parameter block
//   while (... && Synthesis2(synth)) ...      // 128-sample output blocks
//   Anchors are built inside Synthesis2 on first use, so a 200 ms block's
//   ~20 anchors are spread over its ~80 pulses (lazy prefetch also builds the
//   next frame's anchor one interval early), instead of a 13 ms burst.
//
// Rollback: WORLD_AP_MINPHASE_STRIDE=0 makes Synthesis2 use the untouched
// upstream path bit-for-bit (same output as the baseline binary).
//-----------------------------------------------------------------------------
#include "world/synthesisrealtime.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include <chrono>

#include "world/common.h"
#include "world/constantnumbers.h"
#include "world/matlabfunctions.h"

#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
extern "C" void world_synthesis_pulse(
    const float periodic_filter_re[513],
    const float periodic_filter_im[513],
    const float aperiodic_filter_re[513],
    const float aperiodic_filter_im[513],
    const float raw_noise[1024], int noise_size,
    const float dc_remover[512], float response[1024]);
#endif

namespace {

static double AnchorNow() {
  using namespace std::chrono;
  return duration_cast<duration<double> >(
      steady_clock::now().time_since_epoch()).count();
}

static int GetAnchorWindowSize() {
  const char *value = getenv("WORLD_AP_ANCHOR_WINDOW");
  if (value != 0) {
    const int size = atoi(value);
    if (size >= 4 && size <= 128) return size;
  }
  return 22;  // ~180 KB of anchor filters; covers current + next block frame
}

static int GetAnchorInterpMode() {
  const char *value = getenv("WORLD_AP_INTERP_MODE");
  if (value != 0) {
    const int mode = atoi(value);
    if (mode >= 0 && mode <= 1) return mode;
  }
  return 0;
}

static double GetAnchorFallbackRatio() {
  const char *value = getenv("WORLD_AP_FALLBACK_RATIO");
  if (value != 0) {
    const double ratio = atof(value);
    if (ratio >= 0.0) return ratio;
  }
  return 8.0;
}

static int GetAnchorStride() {
  const char *value = getenv("WORLD_AP_MINPHASE_STRIDE");
  if (value != 0) {
    const int stride = atoi(value);
    if (stride >= 0) return stride;
  }
  return 1;
}

#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
static int GetPulseModelEnabled() {
  const char *value = getenv("WORLD_SYNTH_PULSE_MODEL");
  return value != NULL && atoi(value) == 1 ? 1 : 0;
}
#endif

static void GetNoiseSpectrum(int noise_size, int fft_size,
    const ForwardRealFFT *forward_real_fft, RandnState* randn_state) {
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
// GetAperiodicResponse() - upstream per-pulse path (fallback and stride 0).
//-----------------------------------------------------------------------------
static void GetAperiodicResponse(int noise_size, int fft_size,
    const double *spectrum, const double *aperiodic_ratio, double current_vuv,
    const ForwardRealFFT *forward_real_fft,
    const InverseRealFFT *inverse_real_fft,
    const MinimumPhaseAnalysis *minimum_phase, double *aperiodic_response,
    RandnState* randn_state) {
  GetNoiseSpectrum(noise_size, fft_size, forward_real_fft, randn_state);

  if (current_vuv != 0.0)
    for (int i = 0; i <= minimum_phase->fft_size / 2; ++i)
      minimum_phase->log_spectrum[i] =
        log(spectrum[i] * aperiodic_ratio[i] +
        world::kMySafeGuardMinimum) / 2.0;
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
// GetAperiodicResponseFiltered() - excitation with a precomputed filter.
//-----------------------------------------------------------------------------
static void GetAperiodicResponseFiltered(int noise_size, int fft_size,
    const double *filter_real, const double *filter_imag,
    const ForwardRealFFT *forward_real_fft,
    const InverseRealFFT *inverse_real_fft, double *aperiodic_response,
    RandnState* randn_state) {
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

static void ClearRingBuffer(int start, int end, WorldSynthesizer *synth) {
  int pointer;
  for (int i = start; i < end; ++i) {
    pointer = i % synth->number_of_pointers;
    synth->number_of_pulses[pointer] = 0;
    if (synth->pulse_locations[pointer] != NULL) {
      delete[] synth->pulse_locations[pointer];
      synth->pulse_locations[pointer] = NULL;
    }
    if (synth->interpolated_vuv[pointer] != NULL) {
      delete[] synth->interpolated_vuv[pointer];
      synth->interpolated_vuv[pointer] = NULL;
    }
    if (synth->pulse_locations_index[pointer] != NULL) {
      delete[] synth->pulse_locations_index[pointer];
      synth->pulse_locations_index[pointer] = NULL;
    }
  }
}

static int SeekSynthesizer(double current_location, WorldSynthesizer *synth) {
  int frame_number = static_cast<int>(current_location / synth->frame_period);

  int tmp_pointer = synth->current_pointer2;
  int tmp;
  for (int i = 0; i < synth->head_pointer - synth->current_pointer2; ++i) {
    tmp = (tmp_pointer + i) % synth->number_of_pointers;
    if (synth->f0_origin[tmp] <= frame_number &&
        frame_number < synth->f0_origin[tmp] + synth->f0_length[tmp]) {
      tmp_pointer += i;
      break;
    }
  }
  ClearRingBuffer(synth->current_pointer2, tmp_pointer, synth);
  synth->current_pointer2 = tmp_pointer;
  return 1;
}

static void SearchPointer(int frame,  WorldSynthesizer *synth, int flag,
    double **front, double **next) {
  int pointer = synth->current_pointer2 % synth->number_of_pointers;
  int index = -1;
  for (int i = 0; i < synth->f0_length[pointer]; ++i)
    if (synth->f0_origin[pointer] + i == frame) {
      index = i;
      break;
    }

  double ***tmp_pointer =
    flag == 0 ? synth->spectrogram : synth->aperiodicity;

  *front = tmp_pointer[pointer][index];
  *next = index == synth->f0_length[pointer] - 1 ?
    tmp_pointer[(synth->current_pointer2 + 1) %
    synth->number_of_pointers][0] : tmp_pointer[pointer][index + 1];
}

//-----------------------------------------------------------------------------
// PS aperiodic-batch extension: rolling anchor window.
//-----------------------------------------------------------------------------
static void ResetAnchorSlot(PsOptAnchorSlot *slot) {
  delete[] slot->voiced_real;
  delete[] slot->voiced_imag;
  delete[] slot->unvoiced_real;
  delete[] slot->unvoiced_imag;
  slot->voiced_real = NULL;
  slot->voiced_imag = NULL;
  slot->unvoiced_real = NULL;
  slot->unvoiced_imag = NULL;
  slot->voiced_energy = -1.0;
  slot->unvoiced_energy = -1.0;
  slot->frame = -1;
}

static void ClearAnchorWindow(WorldSynthesizer *synth) {
  if (synth->anchor_slots == NULL) return;
  for (int i = 0; i < synth->anchor_window_size; ++i)
    ResetAnchorSlot(&synth->anchor_slots[i]);
  synth->anchor_seconds = 0.0;
  synth->anchor_max_seconds = 0.0;
  synth->anchor_builds = 0;
  synth->anchor_interpolated_pulses = 0;
  synth->anchor_fallback_pulses = 0;
  synth->anchor_allocated_bytes = 0;
  synth->anchor_peak_bytes = 0;
}

// Find the spectrogram/aperiodicity row of an absolute frame index in any
// still-alive parameter block of the ring.
static int FindParameterRow(WorldSynthesizer *synth, int frame,
    double **sp_row, double **ap_row) {
  for (int p = synth->current_pointer2; p < synth->head_pointer; ++p) {
    const int pointer = p % synth->number_of_pointers;
    if (synth->spectrogram[pointer] == NULL) continue;
    const int origin = synth->f0_origin[pointer];
    const int length = synth->f0_length[pointer];
    if (frame >= origin && frame < origin + length) {
      *sp_row = synth->spectrogram[pointer][frame - origin];
      *ap_row = synth->aperiodicity[pointer][frame - origin];
      return 1;
    }
  }
  return 0;
}

// Build (or reuse) one vuv variant of the anchor filter for an absolute frame.
static int BuildAnchor(WorldSynthesizer *synth, int frame, int voiced) {
  if (!synth->anchor_active || synth->anchor_slots == NULL || frame < 0)
    return 0;
  PsOptAnchorSlot *slot =
    &synth->anchor_slots[frame % synth->anchor_window_size];
  if (slot->frame != frame) {
    if (slot->frame >= 0) {
      const int bins = synth->fft_size / 2 + 1;
      if (slot->voiced_real != NULL)
        synth->anchor_allocated_bytes -= 2LL * bins * sizeof(double);
      if (slot->unvoiced_real != NULL)
        synth->anchor_allocated_bytes -= 2LL * bins * sizeof(double);
    }
    ResetAnchorSlot(slot);
    slot->frame = frame;
  }
  if (voiced ? slot->voiced_real != NULL : slot->unvoiced_real != NULL)
    return 1;

  double *sp_row = NULL;
  double *ap_row = NULL;
  if (!FindParameterRow(synth, frame, &sp_row, &ap_row)) return 0;

  const double begin = AnchorNow();
  const int bins = synth->fft_size / 2 + 1;
  if (voiced) {
    for (int i = 0; i < bins; ++i)
      synth->minimum_phase.log_spectrum[i] = log(fabs(sp_row[i]) *
        pow(GetSafeAperiodicity(ap_row[i]), 2.0)) / 2.0;
  } else {
    for (int i = 0; i < bins; ++i)
      synth->minimum_phase.log_spectrum[i] = log(fabs(sp_row[i])) / 2.0;
  }
  GetMinimumPhaseSpectrum(&synth->minimum_phase);
  double *real = new double[bins];
  double *imag = new double[bins];
  double energy = 0.0;
  for (int i = 0; i < bins; ++i) {
    real[i] = synth->minimum_phase.minimum_phase_spectrum[i][0];
    imag[i] = synth->minimum_phase.minimum_phase_spectrum[i][1];
    energy += real[i] * real[i] + imag[i] * imag[i];
  }
  if (voiced) {
    slot->voiced_real = real;
    slot->voiced_imag = imag;
    slot->voiced_energy = energy;
  } else {
    slot->unvoiced_real = real;
    slot->unvoiced_imag = imag;
    slot->unvoiced_energy = energy;
  }
  synth->anchor_allocated_bytes += 2LL * bins * sizeof(double);
  if (synth->anchor_allocated_bytes > synth->anchor_peak_bytes)
    synth->anchor_peak_bytes = synth->anchor_allocated_bytes;

  const double elapsed = AnchorNow() - begin;
  synth->anchor_seconds += elapsed;
  if (elapsed > synth->anchor_max_seconds) synth->anchor_max_seconds = elapsed;
  ++synth->anchor_builds;
  return 1;
}

// Interpolate the anchor filter for a pulse position.
// Return: 1 = filter written, 2 = transition fallback required, 0 = unavailable.
static int GetAnchorFilter(WorldSynthesizer *synth, int frame_low,
    int frame_high, double fraction, int voiced, double *real, double *imag) {
  if (!BuildAnchor(synth, frame_low, voiced)) return 0;
  if (frame_high != frame_low && !BuildAnchor(synth, frame_high, voiced))
    return 0;

  const int window = synth->anchor_window_size;
  PsOptAnchorSlot *low = &synth->anchor_slots[frame_low % window];
  PsOptAnchorSlot *high = frame_high == frame_low ? low :
    &synth->anchor_slots[frame_high % window];
  const double low_energy = voiced ? low->voiced_energy : low->unvoiced_energy;
  const double high_energy = voiced ? high->voiced_energy : high->unvoiced_energy;
  if (synth->anchor_fallback_ratio > 0.0 &&
      low_energy > 0.0 && high_energy > 0.0) {
    const double ratio = low_energy > high_energy ?
      low_energy / high_energy : high_energy / low_energy;
    if (ratio > synth->anchor_fallback_ratio) return 2;
  }

  const double *low_real = voiced ? low->voiced_real : low->unvoiced_real;
  const double *low_imag = voiced ? low->voiced_imag : low->unvoiced_imag;
  const double *high_real = voiced ? high->voiced_real : high->unvoiced_real;
  const double *high_imag = voiced ? high->voiced_imag : high->unvoiced_imag;
  const int bins = synth->fft_size / 2 + 1;
  if (synth->anchor_interp_mode == 0) {
    for (int i = 0; i < bins; ++i) {
      real[i] = (1.0 - fraction) * low_real[i] + fraction * high_real[i];
      imag[i] = (1.0 - fraction) * low_imag[i] + fraction * high_imag[i];
    }
  } else {
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
      const double lerp_magnitude =
        sqrt(lerp_real * lerp_real + lerp_imag * lerp_imag);
      const double scale = lerp_magnitude > 1e-12 ?
        target_magnitude / lerp_magnitude : 1.0;
      real[i] = lerp_real * scale;
      imag[i] = lerp_imag * scale;
    }
  }
  return 1;
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
    new_periodic_response[i] = 0.0;
  for (int i = fft_size / 2; i < fft_size; ++i)
    new_periodic_response[i] -= dc_component * dc_remover[i - fft_size / 2];
}

//-----------------------------------------------------------------------------
// GetPeriodicResponse() calculates an aperiodic response.
//-----------------------------------------------------------------------------
static void GetPeriodicResponse(int fft_size, const double *spectrum,
    const double *aperiodic_ratio, double current_vuv,
    const InverseRealFFT *inverse_real_fft,
    const MinimumPhaseAnalysis *minimum_phase,
    const double *dc_remover, double *periodic_response) {
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

  fft_execute(inverse_real_fft->inverse_fft);
  fftshift(inverse_real_fft->waveform, fft_size, periodic_response);
  RemoveDCComponent(periodic_response, fft_size, dc_remover,
      periodic_response);
}

#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
static void GetPeriodicFilterModel(const double *spectrum,
    const double *aperiodic_ratio, double current_vuv,
    WorldSynthesizer *synth) {
  const int bins = synth->fft_size / 2 + 1;
  if (current_vuv <= 0.5 || aperiodic_ratio[0] > 0.999) {
    for (int i = 0; i < bins; ++i) {
      synth->pulse_periodic_real[i] = 0.0f;
      synth->pulse_periodic_imag[i] = 0.0f;
    }
    return;
  }
  for (int i = 0; i < bins; ++i)
    synth->minimum_phase.log_spectrum[i] =
      log(spectrum[i] * (1.0 - aperiodic_ratio[i]) +
      world::kMySafeGuardMinimum) / 2.0;
  GetMinimumPhaseSpectrum(&synth->minimum_phase);
  for (int i = 0; i < bins; ++i) {
    synth->pulse_periodic_real[i] = static_cast<float>(
      synth->minimum_phase.minimum_phase_spectrum[i][0]);
    synth->pulse_periodic_imag[i] = static_cast<float>(
      synth->minimum_phase.minimum_phase_spectrum[i][1]);
  }
}

static void GetPulseResponseModel(int noise_size, const double *spectrum,
    const double *aperiodic_ratio, double current_vuv,
    const double *filter_real, const double *filter_imag,
    WorldSynthesizer *synth) {
  const int bins = synth->fft_size / 2 + 1;
  GetPeriodicFilterModel(spectrum, aperiodic_ratio, current_vuv, synth);
  for (int i = 0; i < bins; ++i) {
    synth->pulse_aperiodic_real[i] = static_cast<float>(filter_real[i]);
    synth->pulse_aperiodic_imag[i] = static_cast<float>(filter_imag[i]);
  }
  for (int i = 0; i < noise_size; ++i)
    synth->pulse_raw_noise[i] = static_cast<float>(randn(&synth->randn_state));
  world_synthesis_pulse(synth->pulse_periodic_real,
      synth->pulse_periodic_imag, synth->pulse_aperiodic_real,
      synth->pulse_aperiodic_imag, synth->pulse_raw_noise, noise_size,
      synth->pulse_dc_remover, synth->pulse_response);
  const float scale = 1.0f / static_cast<float>(synth->fft_size);
  for (int i = 0; i < synth->fft_size; ++i)
    synth->impulse_response[i] = synth->pulse_response[i] * scale;
}
#endif

static void GetSpectralEnvelope(double current_location,
    WorldSynthesizer *synth, double *spectral_envelope) {
  int current_frame_floor =
    static_cast<int>(current_location / synth->frame_period);

  int current_frame_ceil =
    static_cast<int>(ceil(current_location / synth->frame_period));
  double interpolation =
    current_location / synth->frame_period - current_frame_floor;
  double *front = NULL;
  double *next = NULL;
  SearchPointer(current_frame_floor, synth, 0, &front, &next);

  if (current_frame_floor == current_frame_ceil)
    for (int i = 0; i <= synth->fft_size / 2; ++i)
      spectral_envelope[i] = fabs(front[i]);
  else
    for (int i = 0; i <= synth->fft_size / 2; ++i)
      spectral_envelope[i] =
      (1.0 - interpolation) * fabs(front[i]) + interpolation * fabs(next[i]);
}

static void GetAperiodicRatio(double current_location,
    WorldSynthesizer *synth, double *aperiodic_spectrum) {
  int current_frame_floor =
    static_cast<int>(current_location / synth->frame_period);

  int current_frame_ceil =
    static_cast<int>(ceil(current_location / synth->frame_period));
  double interpolation =
    current_location / synth->frame_period - current_frame_floor;

  double *front = NULL;
  double *next = NULL;
  SearchPointer(current_frame_floor, synth, 1, &front, &next);

  if (current_frame_floor == current_frame_ceil)
    for (int i = 0; i <= synth->fft_size / 2; ++i)
      aperiodic_spectrum[i] = pow(GetSafeAperiodicity(front[i]), 2.0);
  else
    for (int i = 0; i <= synth->fft_size / 2; ++i)
      aperiodic_spectrum[i] =
        pow((1.0 - interpolation) * GetSafeAperiodicity(front[i]) +
        interpolation * GetSafeAperiodicity(next[i]), 2.0);
}

static double GetCurrentVUV(int current_location, WorldSynthesizer *synth) {
  double current_vuv = 0.0;
  int pointer = synth->current_pointer % synth->number_of_pointers;

  int start_sample = MyMaxInt(0,
    static_cast<int>(ceil((synth->f0_origin[pointer] - 1) *
    synth->frame_period * synth->fs)));

  current_vuv =
    synth->interpolated_vuv[pointer][current_location - start_sample + 1];
  return current_vuv;
}

//-----------------------------------------------------------------------------
// GetOneFrameSegment() calculates a periodic and aperiodic response at a time.
//-----------------------------------------------------------------------------
static void GetOneFrameSegment(int noise_size, int current_location,
    WorldSynthesizer *synth) {
  double *spectral_envelope = synth->anchor_envelope;
  double *aperiodic_ratio = synth->anchor_ratio;
  double *periodic_response = synth->anchor_periodic;
  double *aperiodic_response = synth->anchor_aperiodic;
  double *filter_real = synth->anchor_filter_real;
  double *filter_imag = synth->anchor_filter_imag;

  double tmp_location = static_cast<double>(current_location) / synth->fs;
  SeekSynthesizer(tmp_location, synth);
  const double current_vuv = GetCurrentVUV(current_location, synth);
  const int voiced = current_vuv > 0.5 ? 1 : 0;

  double frame_position = tmp_location / synth->frame_period;
  const int frame_low = static_cast<int>(floor(frame_position));
  const int frame_high = frame_low + 1;
  const double fraction = frame_position - frame_low;

  int anchor_status = 0;
  if (synth->anchor_active)
    anchor_status = GetAnchorFilter(synth, frame_low, frame_high, fraction,
        voiced, filter_real, filter_imag);
  const int use_anchor = anchor_status == 1;

  if (voiced || !use_anchor) {
    GetSpectralEnvelope(tmp_location, synth, spectral_envelope);
    GetAperiodicRatio(tmp_location, synth, aperiodic_ratio);
  }
#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
  if (synth->pulse_model_enabled && use_anchor) {
    GetPulseResponseModel(noise_size, spectral_envelope, aperiodic_ratio,
        current_vuv, filter_real, filter_imag, synth);
    ++synth->pulse_model_calls;
    ++synth->anchor_interpolated_pulses;
    BuildAnchor(synth, frame_high + 1, voiced);
    return;
  }
  if (synth->pulse_model_enabled && !use_anchor)
    ++synth->pulse_model_cpu_fallbacks;
#endif
  if (voiced) {
    GetPeriodicResponse(synth->fft_size, spectral_envelope, aperiodic_ratio,
        current_vuv, &synth->inverse_real_fft, &synth->minimum_phase,
        synth->dc_remover, periodic_response);
  } else {
    for (int i = 0; i < synth->fft_size; ++i) periodic_response[i] = 0.0;
  }

  if (use_anchor) {
    GetAperiodicResponseFiltered(noise_size, synth->fft_size, filter_real,
        filter_imag, &synth->forward_real_fft, &synth->inverse_real_fft,
        aperiodic_response, &synth->randn_state);
    ++synth->anchor_interpolated_pulses;
    // Lazy prefetch: build the next frame's anchor one interval early so the
    // 200 ms block cost is spread over pulses instead of one burst.
    BuildAnchor(synth, frame_high + 1, voiced);
  } else {
    GetAperiodicResponse(noise_size, synth->fft_size, spectral_envelope,
        aperiodic_ratio, current_vuv, &synth->forward_real_fft,
        &synth->inverse_real_fft, &synth->minimum_phase, aperiodic_response,
        &synth->randn_state);
    if (synth->anchor_active) ++synth->anchor_fallback_pulses;
  }

  double sqrt_noise_size = sqrt(static_cast<double>(noise_size));
  for (int i = 0; i < synth->fft_size; ++i)
    synth->impulse_response[i] =
    (periodic_response[i] * sqrt_noise_size + aperiodic_response[i]) /
      synth->fft_size;
}

static void GetTemporalParametersForTimeBase(const double *f0, int f0_length,
    WorldSynthesizer *synth, double *coarse_time_axis, double *coarse_f0,
    double *coarse_vuv) {
  int cumulative_frame = MyMaxInt(0, synth->cumulative_frame - f0_length);
  coarse_f0[0] = synth->handoff_f0;
  coarse_time_axis[0] = cumulative_frame * synth->frame_period;
  coarse_vuv[0] = synth->handoff_f0 == 0 ? 0.0 : 1.0;
  for (int i = 0; i < f0_length; ++i) {
    coarse_time_axis[i + synth->handoff] =
      (i + cumulative_frame + synth->handoff) * synth->frame_period;
    coarse_f0[i + synth->handoff] = f0[i];
    coarse_vuv[i + synth->handoff] = f0[i] == 0.0 ? 0.0 : 1.0;
  }
}

static void GetPulseLocationsForTimeBase(const double *interpolated_f0,
    const double *time_axis, int number_of_samples, double origin,
    WorldSynthesizer *synth) {
  double *total_phase = new double[number_of_samples + synth->handoff];
  total_phase[0] = synth->handoff == 1 ? synth->handoff_phase :
    2.0 * world::kPi * interpolated_f0[0] / synth->fs;

  total_phase[1] = total_phase[0] + 2.0 * world::kPi *
    interpolated_f0[0] / synth->fs;
  for (int i = 1 + synth->handoff; i < number_of_samples + synth->handoff; ++i)
    total_phase[i] = total_phase[i - 1] +
      2.0 * world::kPi * interpolated_f0[i - synth->handoff] / synth->fs;
  synth->handoff_phase = total_phase[number_of_samples - 1 + synth->handoff];

  double *wrap_phase = new double[number_of_samples + synth->handoff];
  for (int i = 0; i < number_of_samples + synth->handoff; ++i)
    wrap_phase[i] = fmod(total_phase[i], 2.0 * world::kPi);

  double *wrap_phase_abs = new double[number_of_samples + synth->handoff];
  for (int i = 0; i < number_of_samples - 1 + synth->handoff; ++i)
    wrap_phase_abs[i] = fabs(wrap_phase[i + 1] - wrap_phase[i]);

  int pointer = synth->head_pointer % synth->number_of_pointers;
  int number_of_pulses = 0;
  for (int i = 0; i < number_of_samples - 1 + synth->handoff; ++i)
    if (wrap_phase_abs[i] > world::kPi) {
      synth->pulse_locations[pointer][number_of_pulses] =
        time_axis[i] - static_cast<double>(synth->handoff) / synth->fs;
      synth->pulse_locations_index[pointer][number_of_pulses] =
        matlab_round(synth->pulse_locations[pointer][number_of_pulses] *
            synth->fs);
      ++number_of_pulses;
    }
  synth->number_of_pulses[pointer] = number_of_pulses;

  if (number_of_pulses != 0)
    synth->last_location =
      synth->pulse_locations_index[pointer][number_of_pulses - 1];
  delete[] wrap_phase_abs;
  delete[] wrap_phase;
  delete[] total_phase;
}

static void GetTimeBase(const double *f0, int f0_length, int start_sample,
    int number_of_samples, WorldSynthesizer *synth) {
  double *coarse_time_axis = new double[f0_length + synth->handoff];
  double *coarse_f0 = new double[f0_length + synth->handoff];
  double *coarse_vuv = new double[f0_length + synth->handoff];

  GetTemporalParametersForTimeBase(f0, f0_length, synth,
      coarse_time_axis, coarse_f0, coarse_vuv);

  double *interpolated_f0 = new double[number_of_samples];
  double *time_axis = new double[number_of_samples];

  for (int i = 0; i < number_of_samples; ++i)
    time_axis[i] = (i + start_sample) / static_cast<double>(synth->fs);

  int pointer = synth->head_pointer % synth->number_of_pointers;
  interp1(coarse_time_axis, coarse_f0, f0_length + synth->handoff, time_axis,
    number_of_samples, interpolated_f0);
  interp1(coarse_time_axis, coarse_vuv, f0_length + synth->handoff, time_axis,
    number_of_samples, synth->interpolated_vuv[pointer]);
  for (int i = 0; i < number_of_samples; ++i) {
    synth->interpolated_vuv[pointer][i] =
      synth->interpolated_vuv[pointer][i] > 0.5 ? 1.0 : 0.0;
    interpolated_f0[i] =
      synth->interpolated_vuv[pointer][i] == 0.0 ?
      world::kDefaultF0 : interpolated_f0[i];
  }

  GetPulseLocationsForTimeBase(interpolated_f0, time_axis, number_of_samples,
      coarse_time_axis[0], synth);

  synth->handoff_f0 = interpolated_f0[number_of_samples - 1];
  delete[] time_axis;
  delete[] interpolated_f0;
  delete[] coarse_time_axis;
  delete[] coarse_f0;
  delete[] coarse_vuv;
}

static int GetNextPulseLocationIndex(WorldSynthesizer *synth) {
  int pointer = synth->current_pointer % synth->number_of_pointers;
  if (synth->i < synth->number_of_pulses[pointer] - 1)
    return synth->pulse_locations_index[pointer][synth->i + 1];
  else if (synth->current_pointer == synth->head_pointer - 1)
    return 0;

  for (int i = 1; i < synth->number_of_pointers; ++i) {
    pointer = (i + synth->current_pointer) % synth->number_of_pointers;
    if (synth->number_of_pulses[pointer] != 0)
      return synth->pulse_locations_index[pointer][0];
  }
  return 0;
}

static int UpdateSynthesizer(int current_location, WorldSynthesizer *synth) {
  int pointer = synth->current_pointer % synth->number_of_pointers;
  if (synth->i < synth->number_of_pulses[pointer] - 1) {
    synth->i++;
    return 1;
  } else {
    if (synth->current_pointer == synth->head_pointer - 1) return 0;
  }

  for (int i = 1; i < synth->number_of_pointers; ++i) {
    pointer = (i + synth->current_pointer) % synth->number_of_pointers;
    if (synth->number_of_pulses[pointer] != 0) {
      synth->i = 0;
      synth->current_pointer += i;
      return 1;
    }
  }
  return 0;
}

static int CheckSynthesizer(WorldSynthesizer *synth) {
  if (synth->synthesized_sample + synth->buffer_size >= synth->last_location)
    return 0;

  int pointer = synth->current_pointer % synth->number_of_pointers;
  while (synth->number_of_pulses[pointer] == 0) {
    if (synth->current_pointer == synth->head_pointer) break;
    synth->current_pointer++;
    pointer = synth->current_pointer % synth->number_of_pointers;
  }
  return 1;
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

void InitializeSynthesizer(int fs, double frame_period, int fft_size,
    int buffer_size, int number_of_pointers, WorldSynthesizer *synth) {
  // Set basic parameters
  synth->fs = fs;
  synth->frame_period = frame_period / 1000.0;
  synth->buffer_size = buffer_size;
  synth->number_of_pointers = number_of_pointers;
  synth->fft_size = fft_size;

  // Memory allocations
  synth->f0_length = new int[number_of_pointers];
  synth->spectrogram = new double**[number_of_pointers];
  synth->aperiodicity = new double**[number_of_pointers];
  synth->interpolated_vuv = new double*[number_of_pointers];
  synth->pulse_locations = new double*[number_of_pointers];
  synth->pulse_locations_index = new int*[number_of_pointers];
  synth->number_of_pulses = new int[number_of_pointers];
  synth->f0_origin = new int[number_of_pointers];
  for (int i = 0; i < number_of_pointers; ++i) {
    synth->interpolated_vuv[i] = NULL;
    synth->pulse_locations[i] = NULL;
    synth->pulse_locations_index[i] = NULL;
  }

  synth->buffer = new double[buffer_size * 2 + fft_size];
  synth->impulse_response = new double[synth->fft_size];
  synth->dc_remover = new double[synth->fft_size / 2];

  // PS aperiodic-batch extension.
  synth->anchor_active = GetAnchorStride() > 0 ? 1 : 0;
  synth->anchor_window_size = GetAnchorWindowSize();
  synth->anchor_interp_mode = GetAnchorInterpMode();
  synth->anchor_fallback_ratio = GetAnchorFallbackRatio();
  synth->anchor_slots = new PsOptAnchorSlot[synth->anchor_window_size];
  for (int i = 0; i < synth->anchor_window_size; ++i) {
    synth->anchor_slots[i].frame = -1;
    synth->anchor_slots[i].voiced_real = NULL;
    synth->anchor_slots[i].voiced_imag = NULL;
    synth->anchor_slots[i].unvoiced_real = NULL;
    synth->anchor_slots[i].unvoiced_imag = NULL;
    synth->anchor_slots[i].voiced_energy = -1.0;
    synth->anchor_slots[i].unvoiced_energy = -1.0;
  }
  synth->anchor_envelope = new double[synth->fft_size];
  synth->anchor_ratio = new double[synth->fft_size];
  synth->anchor_periodic = new double[synth->fft_size];
  synth->anchor_aperiodic = new double[synth->fft_size];
  synth->anchor_filter_real = new double[synth->fft_size];
  synth->anchor_filter_imag = new double[synth->fft_size];
  synth->anchor_seconds = 0.0;
  synth->anchor_max_seconds = 0.0;
  synth->anchor_builds = 0;
  synth->anchor_interpolated_pulses = 0;
  synth->anchor_fallback_pulses = 0;
  synth->anchor_allocated_bytes = 0;
  synth->anchor_peak_bytes = 0;

#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
  synth->pulse_model_enabled =
    GetPulseModelEnabled() && synth->fft_size == 1024 ? 1 : 0;
  synth->pulse_model_calls = 0;
  synth->pulse_model_cpu_fallbacks = 0;
  const int pulse_bins = synth->fft_size / 2 + 1;
  synth->pulse_periodic_real = new float[pulse_bins];
  synth->pulse_periodic_imag = new float[pulse_bins];
  synth->pulse_aperiodic_real = new float[pulse_bins];
  synth->pulse_aperiodic_imag = new float[pulse_bins];
  synth->pulse_raw_noise = new float[synth->fft_size];
  synth->pulse_dc_remover = new float[synth->fft_size / 2];
  synth->pulse_response = new float[synth->fft_size];
#endif

  // Initilize internal parameters
  RefreshSynthesizer(synth);

#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
  for (int i = 0; i < synth->fft_size / 2; ++i)
    synth->pulse_dc_remover[i] = static_cast<float>(synth->dc_remover[i]);
#endif

  InitializeMinimumPhaseAnalysis(fft_size, &synth->minimum_phase);
  InitializeInverseRealFFT(fft_size, &synth->inverse_real_fft);
  InitializeForwardRealFFT(fft_size, &synth->forward_real_fft);
}

int AddParameters(double *f0, int f0_length, double **spectrogram,
    double **aperiodicity, WorldSynthesizer *synth) {
  if (synth->head_pointer - synth->current_pointer2 ==
    synth->number_of_pointers)
    return 0;  // Since the queue is full, we cannot add the parameters.
  int pointer = synth->head_pointer % synth->number_of_pointers;
  synth->f0_length[pointer] = f0_length;
  synth->f0_origin[pointer] = synth->cumulative_frame + 1;
  synth->cumulative_frame += f0_length;

  synth->spectrogram[pointer] = spectrogram;
  synth->aperiodicity[pointer] = aperiodicity;
  if (synth->cumulative_frame < 1) {
    synth->handoff_f0 = f0[f0_length - 1];
    synth->number_of_pulses[pointer] = 0;
    synth->head_pointer++;
    synth->handoff = 1;
    return 1;
  }

  int start_sample =
    MyMaxInt(0, static_cast<int>(ceil((synth->cumulative_frame - f0_length) *
      synth->frame_period * synth->fs)));
  int end_sample =
    static_cast<int>(ceil((synth->cumulative_frame) *
      synth->frame_period * synth->fs));
  int number_of_samples = end_sample - start_sample;

  // Memory allocation
  synth->interpolated_vuv[pointer] = new double[number_of_samples + 1];
  synth->pulse_locations[pointer] = new double[number_of_samples];
  synth->pulse_locations_index[pointer] = new int[number_of_samples];

  GetTimeBase(f0, f0_length, start_sample, number_of_samples, synth);

  synth->handoff_f0 = f0[f0_length - 1];
  synth->head_pointer++;
  synth->handoff = 1;
  return 1;
}

void RefreshSynthesizer(WorldSynthesizer *synth) {
  ClearRingBuffer(0, synth->number_of_pointers, synth);
  ClearAnchorWindow(synth);
  synth->handoff_phase = 0;
  synth->handoff_f0 = 0;
  synth->cumulative_frame = -1;
  synth->last_location = 0;

  synth->current_pointer = 0;
  synth->current_pointer2 = 0;
  synth->head_pointer = 0;
  synth->handoff = 0;

  synth->i = 0;
  synth->current_frame = 0;

  synth->synthesized_sample = 0;

  for (int i = 0; i < synth->buffer_size * 2 + synth->fft_size; ++i)
    synth->buffer[i] = 0;
  GetDCRemover(synth->fft_size / 2, synth->dc_remover);
  randn_reseed(&synth->randn_state);
}

void DestroySynthesizer(WorldSynthesizer *synth) {
#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
  if (synth->pulse_model_enabled)
    fprintf(stderr, "{\"kind\":\"world_synthesis_pulse_model\","
        "\"calls\":%lld,\"cpu_fallbacks\":%lld}\n",
        synth->pulse_model_calls, synth->pulse_model_cpu_fallbacks);
#endif
  RefreshSynthesizer(synth);
  delete[] synth->f0_length;

  delete[] synth->spectrogram;
  delete[] synth->aperiodicity;

  delete[] synth->buffer;
  delete[] synth->impulse_response;
  delete[] synth->dc_remover;

  delete[] synth->interpolated_vuv;
  delete[] synth->pulse_locations;
  delete[] synth->pulse_locations_index;
  delete[] synth->number_of_pulses;
  delete[] synth->f0_origin;

  if (synth->anchor_slots != NULL) {
    ClearAnchorWindow(synth);
    delete[] synth->anchor_slots;
    synth->anchor_slots = NULL;
  }
  delete[] synth->anchor_envelope;
  delete[] synth->anchor_ratio;
  delete[] synth->anchor_periodic;
  delete[] synth->anchor_aperiodic;
  delete[] synth->anchor_filter_real;
  delete[] synth->anchor_filter_imag;

#if defined(WORLD_SYNTH_PULSE_MODEL_AVAILABLE)
  delete[] synth->pulse_periodic_real;
  delete[] synth->pulse_periodic_imag;
  delete[] synth->pulse_aperiodic_real;
  delete[] synth->pulse_aperiodic_imag;
  delete[] synth->pulse_raw_noise;
  delete[] synth->pulse_dc_remover;
  delete[] synth->pulse_response;
#endif

  DestroyMinimumPhaseAnalysis(&synth->minimum_phase);
  DestroyInverseRealFFT(&synth->inverse_real_fft);
  DestroyForwardRealFFT(&synth->forward_real_fft);
}

int IsLocked(WorldSynthesizer *synth) {
  int judge = 0;
  if (synth->head_pointer - synth->current_pointer2 ==
      synth->number_of_pointers)
    judge++;
  if (synth->synthesized_sample + synth->buffer_size >= synth->last_location)
    judge++;

  return judge == 2 ? 1 : 0;
}

int Synthesis2(WorldSynthesizer *synth) {
  if (CheckSynthesizer(synth) == 0)
    return 0;
  for (int i = 0; i < synth->buffer_size + synth->fft_size; ++i)
    synth->buffer[i] = synth->buffer[i + synth->buffer_size];

  int pointer = synth->current_pointer % synth->number_of_pointers;
  int noise_size, offset, tmp, index;
  int current_location = synth->pulse_locations_index[pointer][synth->i];
  while (current_location < synth->synthesized_sample + synth->buffer_size) {
    tmp = GetNextPulseLocationIndex(synth);
    noise_size = tmp - current_location;

    GetOneFrameSegment(noise_size, current_location, synth);
    offset =
      current_location - synth->synthesized_sample - synth->fft_size / 2 + 1;
    for (int i = MyMaxInt(0, -offset); i < synth->fft_size; ++i) {
      index = i + offset;
      synth->buffer[index] += synth->impulse_response[i];
    }
    current_location = tmp;
    UpdateSynthesizer(current_location, synth);
  }
  synth->synthesized_sample += synth->buffer_size;
  SeekSynthesizer(synth->synthesized_sample, synth);
  return 1;
}
