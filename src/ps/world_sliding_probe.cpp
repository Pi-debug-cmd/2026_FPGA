// Offline causal-window probe. No ALSA, DMA or PL access.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <memory>
#include <vector>
#include <time.h>
#include "audioio.h"
#include "world/dio.h"
#include "world/stonemask.h"
#include "world/cheaptrick.h"
#include "world/d4c.h"
#include "world/synthesisrealtime.h"

static double Now() {
  timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec + t.tv_nsec * 1e-9;
}

#include "world_sliding_analysis.h"

int main(int argc, char **argv) {
  if ((argc != 3 && argc != 4) || (argc == 4 && strcmp(argv[3], "hop40"))) {
    fprintf(stderr, "usage: world_sliding_probe input16k.wav output.wav [hop40]\n"); return 2;
  }
  const int frames_per_block = argc == 4 ? 4 : 3;
  const int length = GetAudioLength(argv[1]);
  if (length < 8000 || length > 80000) return 2;
  std::vector<double> input(length), output(length + 80);
  int rate, bits; wavread(argv[1], &rate, &bits, input.data());
  if (rate != 16000 || bits != 16) return 2;
  WorldSynthesizer synth = {};
  InitializeSynthesizer(rate, 10, 1024, 128, 16, &synth);
  std::shared_ptr<Parameters> owners[16], last;
  size_t written = 0;
  int id = 0, voiced = 0;
  double analysis_seconds = 0, synthesis_seconds = 0;
  std::vector<double> analysis_ms;
  const double started = Now();
  const int total_frames = length / 160 + 1;
  for (int first = 0; first < total_frames + 12;) {
    const double begin = Now();
    std::shared_ptr<Parameters> block;
    int count;
    if (first < total_frames) {
      count = std::min(frames_per_block, total_frames - first);
      block = Analyze(input, first, count);
      for (double f0 : block->f0) if (f0 > 0) ++voiced;
      analysis_ms.push_back((Now() - begin) * 1000);
      last = block;
    } else {
      count = 12;
      block.reset(new Parameters(count));
      for (int i = 0; i < count; ++i) {
        block->f0[i] = last->f0.back();
        std::copy(last->sp_rows.back(), last->sp_rows.back() + 513, block->sp_rows[i]);
        std::copy(last->ap_rows.back(), last->ap_rows.back() + 513, block->ap_rows[i]);
      }
    }
    analysis_seconds += Now() - begin;
    first += count;
    const double render_begin = Now();
    if (id - synth.current_pointer2 >= 16) { fprintf(stderr, "PARAMETER_QUEUE_FULL\n"); DestroySynthesizer(&synth); return 3; }
    owners[id % 16] = block;
    if (!AddParameters(block->f0.data(), count, block->sp_rows.data(), block->ap_rows.data(), &synth)) {
      DestroySynthesizer(&synth); return 3;
    }
    ++id;
    while (written < output.size() && Synthesis2(&synth)) {
      const size_t take = std::min(static_cast<size_t>(128), output.size() - written);
      std::copy(synth.buffer, synth.buffer + take, output.begin() + written);
      written += take;
    }
    synthesis_seconds += Now() - render_begin;
    if (written == output.size()) break;
  }
  const double elapsed = Now() - started;
  DestroySynthesizer(&synth);
  if (written != output.size()) { fprintf(stderr, "INCOMPLETE_OUTPUT\n"); return 4; }
  double peak = 0;
  for (int i = 0; i < length; ++i) {
    if (!std::isfinite(output[i])) return 4;
    peak = std::max(peak, std::abs(output[i]));
  }
  if (peak >= 1) return 5;
  wavwrite(output.data(), length, rate, 16, argv[2]);
  std::sort(analysis_ms.begin(), analysis_ms.end());
  printf("{\"kind\":\"offline_sliding_analysis_probe\",\"audio_s\":%.6f,\"analysis_s\":%.6f,"
         "\"synthesis_s\":%.6f,\"serial_total_s\":%.6f,\"analysis_rtf\":%.6f,\"synthesis_rtf\":%.6f,"
         "\"analysis_block_p95_ms\":%.6f,\"analysis_block_max_ms\":%.6f,\"hop_ms\":%d,"
         "\"history_ms\":160,\"future_ms\":40,\"synthesis_lookahead_ms\":32,\"voiced_frames\":%d,\"peak\":%.9f}\n",
         length / double(rate), analysis_seconds, synthesis_seconds, elapsed,
         analysis_seconds * rate / length, synthesis_seconds * rate / length,
         analysis_ms[static_cast<size_t>(.95 * (analysis_ms.size() - 1))], analysis_ms.back(),
         frames_per_block * 10, voiced, peak);
  return 0;
}
