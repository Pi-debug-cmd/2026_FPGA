#include "world/common.h"
#include "../kernel/world_minphase_ioctl.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>

int main() {
  int fd = open("/dev/world_minphase", O_RDWR | O_CLOEXEC);
  if (fd < 0) { std::perror("open"); return 2; }
  MinimumPhaseAnalysis reference = {};
  InitializeMinimumPhaseAnalysis(1024, &reference);
  world_minphase_packet packet = {};
  double worst = 0;
  for (int test = 0; test < 24; ++test) {
    for (int i = 0; i < WORLD_MINPHASE_BINS; ++i) {
      double value = -test * .3 + .8 * std::cos(i * (.01 + test * .003));
      if (test % 3 == 1) value += (i % 2 ? .2 : -.2);
      if (test % 3 == 2) value += .1 * std::sin(i * 2.123);
      packet.input[i] = value;
      reference.log_spectrum[i] = packet.input[i];
    }
    GetMinimumPhaseSpectrum(&reference);
    if (ioctl(fd, WORLD_MINPHASE_PROCESS, &packet) < 0) {
      std::perror("WORLD_MINPHASE_PROCESS"); return 3;
    }
    double error = 0, energy = 0;
    for (int i = 0; i < WORLD_MINPHASE_BINS; ++i) {
      double re = reference.minimum_phase_spectrum[i][0];
      double im = reference.minimum_phase_spectrum[i][1];
      error += (packet.output_re[i]-re)*(packet.output_re[i]-re) +
               (packet.output_im[i]-im)*(packet.output_im[i]-im);
      energy += re*re + im*im;
    }
    double relative = std::sqrt(error / energy);
    if (!std::isfinite(relative) || relative > 2e-5) return 4;
    if (relative > worst) worst = relative;
  }
  DestroyMinimumPhaseAnalysis(&reference);
  close(fd);
  std::printf("{\"cases\":24,\"relative_l2_max\":%.12g,\"passed\":true}\n", worst);
}
