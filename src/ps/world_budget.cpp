// Offline Cortex-A9 budget probe, not a streaming audio implementation.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
#include <pthread.h>
#include <time.h>
#include "audioio.h"
#include "world/harvest.h"
#include "world/dio.h"
#include "world/stonemask.h"
#include "world/cheaptrick.h"
#include "world/d4c.h"
#include "world/synthesis.h"
#include "world_stream_synthesis.h"

static double now() {
  timespec stamp;
  clock_gettime(CLOCK_MONOTONIC, &stamp);
  return stamp.tv_sec + stamp.tv_nsec * 1e-9;
}

template<typename Job> static void *run_job(void *payload) {
  (*static_cast<Job *>(payload))();
  return nullptr;
}

int main(int argc, char **argv) {
  if ((argc != 4 && argc != 5) || (strcmp(argv[3], "harvest") && strcmp(argv[3], "dio")) ||
      (argc == 5 && strcmp(argv[4], "fast") && strcmp(argv[4], "fast4") &&
       strcmp(argv[4], "stream5") && strcmp(argv[4], "stream25") && strcmp(argv[4], "stream5fast4"))) {
    fprintf(stderr, "usage: world_budget input16k.wav output.wav harvest|dio [fast|fast4|stream5|stream25|stream5fast4]\n");
    return 2;
  }
  const int length = GetAudioLength(argv[1]);
  if (length < 4000 || length > 80000) return 2;
  std::vector<double> input(length);
  int rate = 0, bits = 0;
  wavread(argv[1], &rate, &bits, input.data());
  if (rate != 16000 || bits != 16) return 2;
  const bool fast = argc == 5;
  const bool downsample_pitch = argc == 5 && (!strcmp(argv[4], "fast4") || !strcmp(argv[4], "stream5fast4"));
  const int stream_frames = argc == 5 && (!strcmp(argv[4], "stream5") || !strcmp(argv[4], "stream5fast4")) ? 5 :
                             argc == 5 && !strcmp(argv[4], "stream25") ? 25 : 0;
  const double period = fast ? 10 : 5;
  const int radius = fast ? 1 : 2; // Similar smoothing duration, 30 vs 25 ms.
  const int frames = GetSamplesForHarvest(rate, length, period);
  std::vector<double> f0(frames), times(frames), refined(frames);
  const double start = now();
  if (!strcmp(argv[3], "harvest")) {
    HarvestOption option;
    InitializeHarvestOption(&option);
    option.f0_floor = 75; option.f0_ceil = 400; option.frame_period = period;
    Harvest(input.data(), length, rate, &option, times.data(), f0.data());
  } else {
    DioOption option;
    InitializeDioOption(&option);
    option.f0_floor = 75; option.f0_ceil = 400; option.frame_period = period;
    option.speed = downsample_pitch ? 4 : 1;
    Dio(input.data(), length, rate, &option, times.data(), f0.data());
  }
  const double pitch_end = now();
  StoneMask(input.data(), length, rate, times.data(), f0.data(), frames, refined.data());
  std::vector<double> energy(length + 1, 0);
  for (int i = 0; i < length; ++i) energy[i + 1] = energy[i] + input[i] * input[i];
  for (int i = 0; i < frames; ++i) {
    const int center = static_cast<int>(std::lround(times[i] * rate));
    const int left = std::max(0, center - 320), right = std::min(length, center + 320);
    if ((energy[right] - energy[left]) / std::max(1, right - left) < std::pow(10., -4.5))
      refined[i] = 0;
  }
  // Match the offline 5-frame median, confined to contiguous voiced runs.
  f0 = refined;
  for (int first = 0; first < frames;) {
    if (refined[first] <= 0) { ++first; continue; }
    int last = first + 1;
    while (last < frames && refined[last] > 0) ++last;
    for (int i = first; i < last; ++i) {
      std::vector<double> window(refined.begin() + std::max(first, i - radius),
                                 refined.begin() + std::min(last, i + radius + 1));
      std::sort(window.begin(), window.end());
      const size_t size = window.size();
      f0[i] = size % 2 ? window[size / 2] : (window[size / 2 - 1] + window[size / 2]) / 2;
    }
    first = last;
  }
  const double refine_end = now();
  const int bins = 513;
  std::vector<double> spectrum(frames * bins), ap(frames * bins);
  std::vector<double *> sp_rows(frames), ap_rows(frames);
  for (int i = 0; i < frames; ++i) {
    sp_rows[i] = spectrum.data() + i * bins;
    ap_rows[i] = ap.data() + i * bins;
  }
  CheapTrickOption spectral_option;
  InitializeCheapTrickOption(rate, &spectral_option);
  spectral_option.fft_size = 1024;
  D4COption ap_option;
  InitializeD4COption(&ap_option);
  double spectrum_seconds = 0, ap_seconds = 0;
  auto spectral_job = [&]() {
    const double begin = now();
    CheapTrick(input.data(), length, rate, times.data(), f0.data(), frames,
                &spectral_option, sp_rows.data());
    spectrum_seconds = now() - begin;
  };
  const auto ap_job = [&]() {
    const double begin = now();
    D4C(input.data(), length, rate, times.data(), f0.data(), frames, 1024, &ap_option, ap_rows.data());
    ap_seconds = now() - begin;
  };
  if (fast) {
    pthread_t spectral_thread;
    int error = pthread_create(&spectral_thread, nullptr,
                               run_job<decltype(spectral_job)>, &spectral_job);
    if (error) { fprintf(stderr, "PTHREAD_CREATE_FAILED %d\n", error); return 5; }
    ap_job();
    error = pthread_join(spectral_thread, nullptr);
    if (error) { fprintf(stderr, "PTHREAD_JOIN_FAILED %d\n", error); return 5; }
  } else {
    spectral_job(); ap_job();
  }
  const double ap_end = now();
  int voiced = 0;
  for (int i = 0; i < frames; ++i) {
    if (f0[i] <= 0) continue;
    ++voiced;
    std::vector<double> original(sp_rows[i], sp_rows[i] + bins);
    double before = 0, after = 0;
    for (int bin = 0; bin < bins; ++bin) {
      const double position = bin / 1.0975;
      const int low = static_cast<int>(position), high = std::min(bins - 1, low + 1);
      const double fraction = position - low;
      sp_rows[i][bin] = std::exp((1 - fraction) * std::log(original[low]) +
                                  fraction * std::log(original[high]));
      before += original[bin]; after += sp_rows[i][bin];
    }
    for (int bin = 0; bin < bins; ++bin) sp_rows[i][bin] *= before / after;
    f0[i] *= 108722. / 65536;
  }
  const double map_end = now();
  // WORLD synthesis may inspect one endpoint sample after this exact duration.
  std::vector<double> output(length + 80, 0);
  if (stream_frames) {
    if (!StreamSynthesize(f0, sp_rows, ap_rows, 1024, period, rate, stream_frames, output)) return 6;
  } else {
    Synthesis(f0.data(), frames, sp_rows.data(), ap_rows.data(), 1024, period, rate,
               static_cast<int>(output.size()), output.data());
  }
  const double end = now();
  double peak = 0, squares = 0;
  for (int i = 0; i < length; ++i) {
    if (!std::isfinite(output[i])) return 3;
    peak = std::max(peak, std::abs(output[i])); squares += output[i] * output[i];
  }
  wavwrite(output.data(), length, rate, 16, argv[2]);
  printf("{\"algorithm\":\"%s\",\"dio_speed\":%d,\"stream_parameter_frames\":%d,\"frame_period_ms\":%.1f,\"parallel_analysis\":%s,\"audio_s\":%.6f,\"pitch_s\":%.6f,"
         "\"refine_s\":%.6f,\"envelope_s\":%.6f,\"ap_s\":%.6f,"
         "\"warp_s\":%.6f,\"synthesis_s\":%.6f,\"total_compute_s\":%.6f,"
         "\"rtf\":%.6f,\"voiced_frames\":%d,\"peak\":%.9f,\"rms\":%.9f}\n",
         argv[3], downsample_pitch ? 4 : 1, stream_frames, period, fast ? "true" : "false", length / double(rate), pitch_end - start, refine_end - pitch_end,
         spectrum_seconds, ap_seconds, map_end - ap_end,
         end - map_end, end - start, (end - start) * rate / length, voiced,
         peak, std::sqrt(squares / length));
  return peak >= 1 ? 4 : 0;
}
