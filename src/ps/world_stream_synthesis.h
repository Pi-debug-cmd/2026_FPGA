// Offline scheduling probe: analysis is still performed on the whole recording.
#ifndef VOICE7020_WORLD_STREAM_SYNTHESIS_H
#define VOICE7020_WORLD_STREAM_SYNTHESIS_H
#include <algorithm>
#include <cstdio>
#include <vector>
#include "world/synthesisrealtime.h"

static bool StreamSynthesize(const std::vector<double> &source_f0,
    const std::vector<double *> &source_sp, const std::vector<double *> &source_ap,
    int fft_size, double period, int rate, int block_frames,
    std::vector<double> &output) {
  // Keep parameter storage alive until consumption finishes. Tail padding only
  // drains the final FFT response; it is not microphone lookahead evidence.
  std::vector<double> f0(source_f0);
  f0.insert(f0.end(), 12, f0.back());
  std::vector<double *> sp(source_sp), ap(source_ap);
  sp.insert(sp.end(), 12, sp.back()); ap.insert(ap.end(), 12, ap.back());
  WorldSynthesizer synth = {};
  InitializeSynthesizer(rate, period, fft_size, 128, 16, &synth);
  size_t written = 0;
  bool success = true;
  for (size_t first = 0; first < f0.size() && written < output.size(); first += block_frames) {
    const int count = std::min(static_cast<size_t>(block_frames), f0.size() - first);
    if (!AddParameters(f0.data() + first, count, sp.data() + first, ap.data() + first, &synth)) {
      fprintf(stderr, "STREAM_PARAMETER_QUEUE_FULL\n"); success = false; break;
    }
    while (written < output.size() && Synthesis2(&synth)) {
      const size_t count_out = std::min(static_cast<size_t>(128), output.size() - written);
      std::copy(synth.buffer, synth.buffer + count_out, output.begin() + written);
      written += count_out;
    }
  }
  if (written != output.size()) {
    fprintf(stderr, "STREAM_INCOMPLETE %zu/%zu\n", written, output.size()); success = false;
  }
  DestroySynthesizer(&synth);
  return success;
}
#endif
