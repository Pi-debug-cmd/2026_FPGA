// Explicit PL backend for WORLD's fixed 1024-point minimum-phase stage.
#include "world/common.h"
#include "../kernel/world_minphase_ioctl.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <time.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>

namespace {
double Now() {
  timespec value; clock_gettime(CLOCK_MONOTONIC, &value);
  return value.tv_sec + value.tv_nsec * 1e-9;
}
struct Backend {
  int fd = -1;
  unsigned long calls = 0, fallback = 0;
  double prepare_s = 0, device_s = 0, unpack_s = 0, wait_s = 0;
  world_minphase_packet packet;
  std::mutex mutex;
  Backend() {
    const char *mode = std::getenv("WORLD_MINPHASE");
    if (!mode || !std::strcmp(mode, "cpu")) return;
    if (std::strcmp(mode, "pl")) std::abort();
    fd = open("/dev/world_minphase", O_RDWR | O_CLOEXEC);
    if (fd < 0) { std::perror("open /dev/world_minphase"); std::abort(); }
  }
  ~Backend() {
    if (fd >= 0) {
      std::fprintf(stderr,
        "{\"kind\":\"world_minphase_pl\",\"calls\":%lu,\"fallback\":%lu,"
        "\"prepare_s\":%.9f,\"device_s\":%.9f,\"unpack_s\":%.9f,\"wait_s\":%.9f}\n",
        calls, fallback, prepare_s, device_s, unpack_s, wait_s);
      close(fd);
    }
  }
} backend;
}

extern "C" void __real_GetMinimumPhaseSpectrum(const MinimumPhaseAnalysis *analysis);
extern "C" void __wrap_GetMinimumPhaseSpectrum(const MinimumPhaseAnalysis *analysis) {
  if (backend.fd < 0) { __real_GetMinimumPhaseSpectrum(analysis); return; }
  if (analysis->fft_size != 1024) {
    ++backend.fallback;
    __real_GetMinimumPhaseSpectrum(analysis);
    return;
  }
  double start = Now();
  std::lock_guard<std::mutex> guard(backend.mutex);
  double begin = Now();
  backend.wait_s += begin - start;
  for (int i = 0; i < WORLD_MINPHASE_BINS; ++i)
    backend.packet.input[i] = analysis->log_spectrum[i];
  double prepared = Now();
  if (ioctl(backend.fd, WORLD_MINPHASE_PROCESS, &backend.packet) < 0) {
    std::perror("WORLD_MINPHASE_PROCESS");
    std::abort();
  }
  double completed = Now();
  for (int i = 0; i < WORLD_MINPHASE_BINS; ++i) {
    analysis->minimum_phase_spectrum[i][0] = backend.packet.output_re[i];
    analysis->minimum_phase_spectrum[i][1] = backend.packet.output_im[i];
  }
  backend.prepare_s += prepared - begin;
  backend.device_s += completed - prepared;
  backend.unpack_s += Now() - completed;
  ++backend.calls;
}
