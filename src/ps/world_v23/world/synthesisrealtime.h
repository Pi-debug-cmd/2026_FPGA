//-----------------------------------------------------------------------------
// PS aperiodic-batch streaming synthesizer: extended header.
//
// This file SHADOWS build/generated/world_source_v035/.../src/world/
// synthesisrealtime.h for the optimized streaming build (our include directory
// comes first).  The upstream tree is not modified.  The WorldSynthesizer
// struct below is the upstream struct plus the anchor-window extension and
// timing counters; the layout before the extension is byte-identical to
// upstream, so the same source (world_live_stream.cpp, probes) works with
// either header by recompiling.
//-----------------------------------------------------------------------------
#ifndef WORLD_SYNTHESISREALTIME_H_
#define WORLD_SYNTHESISREALTIME_H_

#include "world/common.h"
#include "world/macrodefinitions.h"
#include "world/matlabfunctions.h"

WORLD_BEGIN_C_DECLS

//-----------------------------------------------------------------------------
// A slot of the rolling aperiodic minimum-phase anchor window.
// One slot per frame (frame % anchor_window_size); a slot is rebuilt when its
// frame index no longer matches.  Both vuv variants are stored only when used.
//-----------------------------------------------------------------------------
typedef struct {
  int frame;               // absolute analysis frame index, -1 = empty
  double *voiced_real;     // minimum-phase filter, log(|sp|*ap^2)/2 variant
  double *voiced_imag;
  double *unvoiced_real;   // log(|sp|)/2 variant
  double *unvoiced_imag;
  double voiced_energy;    // sum |H|^2, used by the transition fallback test
  double unvoiced_energy;
} PsOptAnchorSlot;

//-----------------------------------------------------------------------------
// A struct for real-time synthesis (upstream fields + anchor extension).
//-----------------------------------------------------------------------------
typedef struct {
  // Basic parameters
  int fs;
  double frame_period;
  int buffer_size;
  int number_of_pointers;
  int fft_size;

  // Sound buffer for output. The length is buffer_size [sample].
  double *buffer;
  int current_pointer;
  int i;

  // For DC removal
  double *dc_remover;

  // Speech parameters in each pointer.
  int *f0_length;
  int *f0_origin;
  double ***spectrogram;
  double ***aperiodicity;

  int current_pointer2;
  int head_pointer;
  int synthesized_sample;

  // Internal parameters.
  int handoff;
  double handoff_phase;
  double handoff_f0;
  int last_location;

  int cumulative_frame;
  int current_frame;

  double **interpolated_vuv;
  double **pulse_locations;
  int **pulse_locations_index;
  int *number_of_pulses;

  double *impulse_response;

  RandnState randn_state;

  // FFT
  MinimumPhaseAnalysis minimum_phase;
  InverseRealFFT inverse_real_fft;
  ForwardRealFFT forward_real_fft;

  //---------------------------------------------------------------------------
  // PS aperiodic-batch extension (not upstream).
  //---------------------------------------------------------------------------
  int anchor_window_size;      // ring slots = frames % anchor_window_size
  int anchor_active;           // 1 after InitializeSynthesizer()
  int anchor_interp_mode;      // 0: complex lerp, 1: magnitude-corrected lerp
  double anchor_fallback_ratio;// transition fallback threshold (0 = off)
  PsOptAnchorSlot *anchor_slots;
  // Scratch buffers reused by every pulse (upstream allocated per pulse).
  double *anchor_envelope;
  double *anchor_ratio;
  double *anchor_periodic;
  double *anchor_aperiodic;
  double *anchor_filter_real;
  double *anchor_filter_imag;
  // Instrumentation read by the file-streaming probe.
  double anchor_seconds;          // total time spent building anchors
  double anchor_max_seconds;      // worst single anchor build
  long long anchor_builds;        // number of minimum-phase anchor builds
  long long anchor_interpolated_pulses;
  long long anchor_fallback_pulses;
  long long anchor_allocated_bytes; // anchor filter memory currently held
  long long anchor_peak_bytes;      // high-water mark of the same
} WorldSynthesizer;

//-----------------------------------------------------------------------------
// Upstream-compatible API.
//-----------------------------------------------------------------------------
void InitializeSynthesizer(int fs, double frame_period, int fft_size,
  int buffer_size, int number_of_pointers, WorldSynthesizer *synth);

int AddParameters(double *f0, int f0_length, double **spectrogram,
  double **aperiodicity, WorldSynthesizer *synth);

void RefreshSynthesizer(WorldSynthesizer *synth);

void DestroySynthesizer(WorldSynthesizer *synth);

int IsLocked(WorldSynthesizer *synth);

int Synthesis2(WorldSynthesizer *synth);

WORLD_END_C_DECLS

#endif  // WORLD_SYNTHESISREALTIME_H_
