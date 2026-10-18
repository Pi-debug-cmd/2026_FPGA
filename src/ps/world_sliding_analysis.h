// Shared causal-window analysis; owned arrays remain stable after publication.
#ifndef VOICE7020_WORLD_SLIDING_ANALYSIS_H
#define VOICE7020_WORLD_SLIDING_ANALYSIS_H
#include <algorithm>
#include <cmath>
#include <memory>
#include <time.h>
#include <vector>
#include "world/dio.h"
#include "world/stonemask.h"
#include "world/cheaptrick.h"
#include "world/d4c.h"
struct Parameters {
  std::vector<double> f0, spectrum, ap;
  std::vector<double *> sp_rows, ap_rows;
  explicit Parameters(int count): f0(count), spectrum(count * 513), ap(count * 513),
      sp_rows(count), ap_rows(count) {
    for (int i = 0; i < count; ++i) {
      sp_rows[i] = spectrum.data() + i * 513;
      ap_rows[i] = ap.data() + i * 513;
    }
  }
};

struct AnalysisTiming {
  double dio_s = 0, refine_s = 0, spectrum_s = 0, aperiodic_s = 0, warp_s = 0, last = 0;
  static double Clock() {
    timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
  }
  void Lap(double &seconds) { const double current = Clock(); seconds += current - last; last = current; }
};

static std::shared_ptr<Parameters> Analyze(const std::vector<double> &input, int first, int count,
                                          AnalysisTiming *timing = NULL) {
  if (timing) timing->last = AnalysisTiming::Clock();
  const int rate = 16000, hop = 160, history = 2560, future = 640;
  const int start = std::max(0, first * hop - history);
  const int end = std::min(static_cast<int>(input.size()), (first + count - 1) * hop + future);
  const int length = end - start;
  const double *signal = input.data() + start;
  DioOption option; InitializeDioOption(&option);
  option.f0_floor = 75; option.f0_ceil = 400; option.frame_period = 10; option.speed = 4;
  const int raw_count = GetSamplesForDIO(rate, length, 10);
  std::vector<double> raw(raw_count), raw_times(raw_count);
  Dio(signal, length, rate, &option, raw_times.data(), raw.data());
  if (timing) timing->Lap(timing->dio_s);
  // Refine just new frames plus one neighbor for the 3-frame voiced median.
  const int ref_first = std::max(0, first - 1);
  const int ref_last = std::min(static_cast<int>(input.size()) / hop, first + count);
  const int ref_count = ref_last - ref_first + 1;
  std::vector<double> ref_times(ref_count), estimates(ref_count), refined(ref_count);
  for (int i = 0; i < ref_count; ++i) {
    const int sample = (ref_first + i) * hop - start;
    ref_times[i] = sample / double(rate);
    const int index = sample / hop;
    estimates[i] = index >= 0 && index < raw_count ? raw[index] : 0;
  }
  StoneMask(signal, length, rate, ref_times.data(), estimates.data(), ref_count, refined.data());
  for (int i = 0; i < ref_count; ++i) {
    const int center = (ref_first + i) * hop - start;
    const int left = std::max(0, center - 320), right = std::min(length, center + 320);
    double energy = 0;
    for (int j = left; j < right; ++j) energy += signal[j] * signal[j];
    if (energy / std::max(1, right - left) < std::pow(10., -4.5)) refined[i] = 0;
  }
  std::shared_ptr<Parameters> result(new Parameters(count));
  std::vector<double> times(count);
  for (int i = 0; i < count; ++i) {
    const int index = first + i - ref_first;
    times[i] = ((first + i) * hop - start) / double(rate);
    if (refined[index] <= 0) continue;
    std::vector<double> median(1, refined[index]);
    if (index > 0 && refined[index - 1] > 0) median.push_back(refined[index - 1]);
    if (index + 1 < ref_count && refined[index + 1] > 0) median.push_back(refined[index + 1]);
    std::sort(median.begin(), median.end());
    const size_t n = median.size();
    result->f0[i] = n % 2 ? median[n / 2] : (median[n / 2 - 1] + median[n / 2]) / 2;
  }
  if (timing) timing->Lap(timing->refine_s);
  CheapTrickOption sp_option; InitializeCheapTrickOption(rate, &sp_option); sp_option.fft_size = 1024;
  CheapTrick(signal, length, rate, times.data(), result->f0.data(), count, &sp_option, result->sp_rows.data());
  if (timing) timing->Lap(timing->spectrum_s);
  D4COption ap_option; InitializeD4COption(&ap_option);
  D4C(signal, length, rate, times.data(), result->f0.data(), count, 1024, &ap_option, result->ap_rows.data());
  if (timing) timing->Lap(timing->aperiodic_s);
  for (int frame = 0; frame < count; ++frame) {
    if (result->f0[frame] <= 0) continue;
    std::vector<double> old(result->sp_rows[frame], result->sp_rows[frame] + 513);
    // Adjacent destination bins reuse source bins. Compute each logarithm once;
    // keep interpolation and energy-sum order identical to the original formula.
    double log_power[513];
    for (int bin = 0; bin < 513; ++bin) log_power[bin] = std::log(old[bin]);
    double before = 0, after = 0;
    for (int bin = 0; bin < 513; ++bin) {
      const double p = bin / 1.0975;
      const int low = static_cast<int>(p), high = std::min(512, low + 1);
      result->sp_rows[frame][bin] = std::exp((1 - (p - low)) * log_power[low] +
                                             (p - low) * log_power[high]);
      before += old[bin]; after += result->sp_rows[frame][bin];
    }
    for (int bin = 0; bin < 513; ++bin) result->sp_rows[frame][bin] *= before / after;
    result->f0[frame] *= 108722. / 65536;
  }
  if (timing) timing->Lap(timing->warp_s);
  return result;
}

#endif
