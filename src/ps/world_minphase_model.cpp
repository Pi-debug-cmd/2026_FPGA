// Host-only full-speech regression for the fused minimum-phase HLS candidate.
#include "world/common.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
extern "C" void world_minphase(const float[513], float[513], float[513]);
namespace {
struct Stats {
  unsigned long calls = 0;
  ~Stats() { std::fprintf(stderr, "{\"kind\":\"world_minphase_model\",\"calls\":%lu}\n", calls); }
} stats;
}
extern "C" void __real_GetMinimumPhaseSpectrum(const MinimumPhaseAnalysis*);
extern "C" void __wrap_GetMinimumPhaseSpectrum(const MinimumPhaseAnalysis* p) {
  const char* mode = std::getenv("WORLD_MINPHASE_MODEL");
  if (!mode || !std::strcmp(mode, "cpu")) { __real_GetMinimumPhaseSpectrum(p); return; }
  if (std::strcmp(mode, "fused") || p->fft_size != 1024) std::abort();
  float input[513], re[513], im[513];
  for (int i = 0; i < 513; ++i) input[i] = p->log_spectrum[i];
  world_minphase(input, re, im);
  for (int i = 0; i < 513; ++i) {
    p->minimum_phase_spectrum[i][0] = re[i];
    p->minimum_phase_spectrum[i][1] = im[i];
  }
  ++stats.calls;
}
