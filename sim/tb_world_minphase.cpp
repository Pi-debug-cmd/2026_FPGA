#include "world/common.h"
#include <cmath>
#include <cstdio>
extern "C" void world_minphase(const float[513], float[513], float[513]);
int main() {
  MinimumPhaseAnalysis reference = {};
  InitializeMinimumPhaseAnalysis(1024, &reference);
  double worst = 0;
  for (int test = 0; test < 24; ++test) {
    float input[513], re[513], im[513];
    for (int i = 0; i < 513; ++i) {
      // Smooth log envelopes at several absolute levels, plus alternating
      // and deterministic irregular bins to expose FFT sign mistakes.
      double value = -test * .3 + .8 * std::cos(i * (.01 + test * .003));
      if (test % 3 == 1) value += (i % 2 ? .2 : -.2);
      if (test % 3 == 2) value += .1 * std::sin(i * 2.123);
      input[i] = value;
      reference.log_spectrum[i] = input[i];
    }
    GetMinimumPhaseSpectrum(&reference);
    world_minphase(input, re, im);
    double error = 0, energy = 0;
    for (int i = 0; i < 513; ++i) {
      const double a = reference.minimum_phase_spectrum[i][0];
      const double b = reference.minimum_phase_spectrum[i][1];
      error += (re[i]-a)*(re[i]-a) + (im[i]-b)*(im[i]-b);
      energy += a*a + b*b;
    }
    const double relative = std::sqrt(error/energy);
    if (!std::isfinite(relative) || relative > 2e-5) return 1;
    if (relative > worst) worst = relative;
  }
  DestroyMinimumPhaseAnalysis(&reference);
  std::printf("{\"cases\":24,\"relative_l2_max\":%.12g,\"passed\":true}\n", worst);
}
