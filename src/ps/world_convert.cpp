// On-board registration -> conversion closed loop (file replay, no PC in the loop).
//
// usage: world_convert input16k.wav profile.txt output.wav [--identity]
//
// Reads a 16 kHz / 16 bit mono source WAV and a target profile produced by world_register,
// then converts with WORLD 0.3.5 (DIO+StoneMask / CheapTrick / D4C / Synthesis):
//   * F0: per-utterance log-F0 statistics mapped onto the target statistics,
//         scale clipped to [0.5, 2] and output clipped to [75, 400] Hz.
//   * envelope: linear resampling warp (factor searched in [0.85, 1.25]) plus a per-bin
//         log-power delta clipped to +/-3 dB, applied with strength 0.65 and total-power
//         preserving normalisation per voiced frame.
// This deliberately omits the historical order-24 cepstral smoothing, so it is NOT a
// re-implementation of the archived recipe; its effect is measured, not assumed.
// `--identity` skips mapping and only re-synthesises, to check the analysis/synthesis path.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <numeric>
#include <vector>

#include "audioio.h"
#include "world/cheaptrick.h"
#include "world/d4c.h"
#include "world/dio.h"
#include "world/stonemask.h"
#include "world/synthesis.h"

namespace {

template <typename T> T Clamp(T value, T low, T high) {
  return value < low ? low : (value > high ? high : value);
}

constexpr int kRate = 16000;
constexpr double kFramePeriodMs = 10.0;
constexpr double kF0Floor = 75.0;
constexpr double kF0Ceil = 400.0;
constexpr int kDioSpeed = 4;
constexpr int kFftSize = 1024;
constexpr int kBins = kFftSize / 2 + 1;
constexpr double kEnvelopeStrength = 0.65;
constexpr double kDeltaLimit = 3.0 * std::log(10.0) / 10.0;  // 3 dB in log power
constexpr double kEnergyFloor = 3.162277660168379e-05;  // 10^-4.5
constexpr int kMinSamples = 16000;

double Percentile(const std::vector<double> &sorted, double fraction) {
  if (sorted.empty()) return 0.0;
  const double position = fraction * static_cast<double>(sorted.size() - 1);
  const size_t low = static_cast<size_t>(std::floor(position));
  const size_t high = static_cast<size_t>(std::ceil(position));
  if (low == high) return sorted[low];
  const double weight = position - static_cast<double>(low);
  return sorted[low] * (1.0 - weight) + sorted[high] * weight;
}

// np.interp(x, bins, shape) with edge clamping.
std::vector<double> WarpShape(const std::vector<double> &shape, double factor) {
  std::vector<double> out(shape.size(), 0.0);
  const double last = static_cast<double>(shape.size() - 1);
  for (size_t i = 0; i < shape.size(); ++i) {
    double x = static_cast<double>(i) / factor;
    if (x <= 0.0) {
      out[i] = shape.front();
      continue;
    }
    if (x >= last) {
      out[i] = shape.back();
      continue;
    }
    const size_t index = static_cast<size_t>(std::floor(x));
    const double weight = x - static_cast<double>(index);
    out[i] = shape[index] * (1.0 - weight) + shape[index + 1] * weight;
  }
  return out;
}

struct Profile {
  double f0_p10 = 0.0, f0_median = 0.0, f0_p90 = 0.0;
  std::vector<double> spectrum_db;
  bool valid() const { return f0_median > 0.0 && spectrum_db.size() == kBins; }
};

Profile LoadProfile(const char *path) {
  Profile profile;
  FILE *file = fopen(path, "r");
  if (file == nullptr) return profile;
  char line[8192];
  while (fgets(line, sizeof(line), file) != nullptr) {
    if (line[0] == '#') continue;
    if (!strncmp(line, "spectrum_db", 11)) {
      char *cursor = line + 11;
      char *end = nullptr;
      while (true) {
        const double v = strtod(cursor, &end);
        if (end == cursor) break;
        profile.spectrum_db.push_back(v);
        cursor = end;
      }
      continue;
    }
    char key[64] = {0};
    double value = 0.0;
    if (sscanf(line, "%63s %lf", key, &value) == 2) {
      if (!strcmp(key, "f0_p10_hz")) profile.f0_p10 = value;
      else if (!strcmp(key, "f0_median_hz")) profile.f0_median = value;
      else if (!strcmp(key, "f0_p90_hz")) profile.f0_p90 = value;
    }
  }
  fclose(file);
  return profile;
}

}  // namespace

int main(int argc, char **argv) {
  const bool identity = argc == 5 && !strcmp(argv[4], "--identity");
  if (argc != 4 && !identity) {
    fprintf(stderr, "usage: world_convert input16k.wav profile.txt output.wav [--identity]\n");
    return 2;
  }
  const Profile target = LoadProfile(argv[2]);
  if (!target.valid()) {
    fprintf(stderr, "REJECTED bad_profile bins=%zu need=%d\n", target.spectrum_db.size(), kBins);
    return 3;
  }

  const int length = GetAudioLength(argv[1]);
  if (length < kMinSamples) {
    fprintf(stderr, "REJECTED too_short samples=%d\n", length);
    return 3;
  }
  std::vector<double> x(static_cast<size_t>(length));
  int rate = 0, bits = 0;
  wavread(argv[1], &rate, &bits, x.data());
  if (rate != kRate || bits != 16) {
    fprintf(stderr, "REJECTED bad_format rate=%d bits=%d\n", rate, bits);
    return 4;
  }

  DioOption dio_option;
  InitializeDioOption(&dio_option);
  dio_option.frame_period = kFramePeriodMs;
  dio_option.f0_floor = kF0Floor;
  dio_option.f0_ceil = kF0Ceil;
  dio_option.channels_in_octave = 2;
  dio_option.speed = kDioSpeed;
  dio_option.allowed_range = 0.1;

  const int f0_length = GetSamplesForDIO(kRate, length, kFramePeriodMs);
  std::vector<double> time_axis(static_cast<size_t>(f0_length));
  std::vector<double> f0(static_cast<size_t>(f0_length));
  Dio(x.data(), length, kRate, &dio_option, time_axis.data(), f0.data());
  StoneMask(x.data(), length, kRate, time_axis.data(), f0.data(), f0_length, f0.data());

  // Energy gate copied from src/reference/world_registration.py (mean power < 1e-4.5 -> unvoiced).
  for (int i = 0; i < f0_length; ++i) {
    const long center = static_cast<long>(std::llround(time_axis[static_cast<size_t>(i)] * kRate));
    const long left = std::max<long>(0, center - 320);
    const long right = std::min<long>(length, center + 320);
    double energy = 0.0;
    for (long n = left; n < right; ++n) energy += x[static_cast<size_t>(n)] * x[static_cast<size_t>(n)];
    const double mean = energy / static_cast<double>(std::max<long>(1, right - left));
    if (mean < kEnergyFloor) f0[static_cast<size_t>(i)] = 0.0;
  }

  CheapTrickOption cheaptrick_option;
  InitializeCheapTrickOption(kRate, &cheaptrick_option);
  cheaptrick_option.q1 = -0.15;
  cheaptrick_option.f0_floor = kF0Floor;
  cheaptrick_option.fft_size = kFftSize;
  std::vector<double *> sp(static_cast<size_t>(f0_length), nullptr);
  for (int i = 0; i < f0_length; ++i) sp[static_cast<size_t>(i)] = new double[kBins];
  CheapTrick(x.data(), length, kRate, time_axis.data(), f0.data(), f0_length,
             &cheaptrick_option, sp.data());

  D4COption d4c_option;
  InitializeD4COption(&d4c_option);
  d4c_option.threshold = 0.85;
  std::vector<double *> ap(static_cast<size_t>(f0_length), nullptr);
  for (int i = 0; i < f0_length; ++i) ap[static_cast<size_t>(i)] = new double[kBins];
  D4C(x.data(), length, kRate, time_axis.data(), f0.data(), f0_length, kFftSize,
      &d4c_option, ap.data());

  std::vector<size_t> voiced;
  std::vector<double> voiced_f0;
  for (int i = 0; i < f0_length; ++i) {
    if (f0[static_cast<size_t>(i)] > 0.0) {
      voiced.push_back(static_cast<size_t>(i));
      voiced_f0.push_back(f0[static_cast<size_t>(i)]);
    }
  }
  if (voiced.size() < 30) {
    fprintf(stderr, "REJECTED too_few_voiced voiced=%zu\n", voiced.size());
    return 5;
  }

  // Source statistics: log-F0 percentiles and the mean normalised log envelope.
  std::vector<double> log_f0(voiced_f0.size());
  for (size_t i = 0; i < voiced_f0.size(); ++i) log_f0[i] = std::log(voiced_f0[i]);
  std::vector<double> sorted_log = log_f0;
  std::sort(sorted_log.begin(), sorted_log.end());
  const double src_p10 = Percentile(sorted_log, 0.10);
  const double src_median = Percentile(sorted_log, 0.50);
  const double src_p90 = Percentile(sorted_log, 0.90);

  const double tgt_p10 = std::log(target.f0_p10);
  const double tgt_median = std::log(target.f0_median);
  const double tgt_p90 = std::log(target.f0_p90);
  const double src_spread = src_p90 - src_p10;
  const double tgt_spread = tgt_p90 - tgt_p10;
  double scale = 1.0;
  if (src_spread >= 0.05) {
    scale = Clamp(tgt_spread / src_spread, 0.5, 2.0);
  }

  std::vector<double> source_shape(kBins, 0.0);
  for (size_t index : voiced) {
    double mean = 0.0;
    for (int b = 0; b < kBins; ++b) mean += std::log(sp[index][b]);
    mean /= kBins;
    for (int b = 0; b < kBins; ++b) source_shape[b] += std::log(sp[index][b]) - mean;
  }
  for (int b = 0; b < kBins; ++b) source_shape[b] /= static_cast<double>(voiced.size());

  std::vector<double> target_shape(kBins, 0.0);
  double target_mean = 0.0;
  for (int b = 0; b < kBins; ++b) target_mean += target.spectrum_db[b];
  target_mean /= kBins;
  const double db_to_ln = std::log(10.0) / 10.0;
  for (int b = 0; b < kBins; ++b) target_shape[b] = (target.spectrum_db[b] - target_mean) * db_to_ln;

  // Search the formant warp factor on 300-4000 Hz, minimising the centred MSE.
  const double bin_hz = static_cast<double>(kRate) / kFftSize;
  const int roi_low = static_cast<int>(std::ceil(300.0 / bin_hz));
  const int roi_high = std::min(kBins - 1, static_cast<int>(std::floor(4000.0 / bin_hz)));
  double best_factor = 1.0;
  double best_score = 1e300;
  for (int step = 0; step <= 16; ++step) {
    const double factor = 0.85 + 0.025 * step;
    const std::vector<double> warped = WarpShape(source_shape, factor);
    double mean = 0.0;
    for (int b = roi_low; b <= roi_high; ++b) mean += target_shape[b] - warped[b];
    mean /= static_cast<double>(roi_high - roi_low + 1);
    double score = 0.0;
    for (int b = roi_low; b <= roi_high; ++b) {
      const double value = (target_shape[b] - warped[b]) - mean;
      score += value * value;
    }
    score /= static_cast<double>(roi_high - roi_low + 1);
    if (score < best_score) {
      best_score = score;
      best_factor = factor;
    }
  }

  const std::vector<double> warped_source = WarpShape(source_shape, best_factor);
  std::vector<double> delta(kBins, 0.0);
  for (int b = 0; b < kBins; ++b) {
    delta[b] = Clamp(target_shape[b] - warped_source[b], -kDeltaLimit, kDeltaLimit);
  }

  const double frame_factor = 1.0 + kEnvelopeStrength * (best_factor - 1.0);
  std::vector<double> mapped_f0 = f0;
  double peak = 0.0;
  if (!identity) {
    for (size_t index : voiced) {
      const double value = std::exp(tgt_median + scale *
                                    (std::log(f0[index]) - src_median));
      mapped_f0[index] = Clamp(value, kF0Floor, kF0Ceil);
    }
    for (size_t index : voiced) {
      std::vector<double> log_frame(kBins, 0.0);
      double mean = 0.0;
      for (int b = 0; b < kBins; ++b) {
        log_frame[b] = std::log(sp[index][b]);
        mean += log_frame[b];
      }
      mean /= kBins;
      for (int b = 0; b < kBins; ++b) log_frame[b] -= mean;
      const std::vector<double> warped = WarpShape(log_frame, frame_factor);
      double original_power = 0.0;
      double mapped_power = 0.0;
      std::vector<double> mapped(kBins, 0.0);
      for (int b = 0; b < kBins; ++b) {
        mapped[b] = std::exp(warped[b] + kEnvelopeStrength * delta[b]);
        original_power += sp[index][b];
        mapped_power += mapped[b];
      }
      if (!(mapped_power > 0.0)) continue;
      const double gain = original_power / mapped_power;
      for (int b = 0; b < kBins; ++b) sp[index][b] = mapped[b] * gain;
    }
  }

  std::vector<double> output(static_cast<size_t>(length), 0.0);
  Synthesis(mapped_f0.data(), f0_length, sp.data(), ap.data(), kFftSize, kFramePeriodMs, kRate, length,
            output.data());
  output.resize(static_cast<size_t>(length));

  for (double sample : output) {
    if (!std::isfinite(sample)) {
      fprintf(stderr, "REJECTED nonfinite_output\n");
      return 6;
    }
    peak = std::max(peak, std::fabs(sample));
  }
  int clipped = 0;
  for (double &sample : output) {
    if (sample > 1.0) { sample = 1.0; ++clipped; }
    if (sample < -1.0) { sample = -1.0; ++clipped; }
  }
  wavwrite(output.data(), length, kRate, 16, argv[3]);

  printf("OK samples=%d frames=%d voiced=%zu scale=%.6f warp=%.4f delta_db_rms=%.4f "
         "peak=%.6f clipped=%d\n",
         length, f0_length, voiced.size(), identity ? 1.0 : scale, identity ? 1.0 : best_factor,
         [&delta] {
           double sum = 0.0;
           for (double value : delta) sum += value * value;
           return 10.0 / std::log(10.0) * std::sqrt(sum / delta.size());
         }(),
         peak, clipped);

  for (int i = 0; i < f0_length; ++i) {
    delete[] sp[static_cast<size_t>(i)];
    delete[] ap[static_cast<size_t>(i)];
  }
  return 0;
}
