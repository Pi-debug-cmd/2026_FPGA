// 现场目标注册画像工具（Cortex-A9 / 主机通用，脱机运行，不依赖 PC）。
//
// 读入 16 kHz / 16 bit 单声道目标录音，用 WORLD 0.3.5 的 DIO+StoneMask / CheapTrick / D4C
// 分析出目标画像参数，写出可加载的画像文件，并返回质量门槛结果。
//
// 质量门槛（为“现场注册目标声源”服务，不合格必须拒绝并要求重录）：
//   2 参数不足；3 时长不足；4 采样格式不符；5 有声帧不足；6 数值非法。
//
// 只做文件读写，不碰 ALSA、不播放、不录音。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <numeric>
#include <string>
#include <vector>

#include "audioio.h"
#include "world/cheaptrick.h"
#include "world/d4c.h"
#include "world/dio.h"
#include "world/stonemask.h"

namespace {

constexpr double kFramePeriodMs = 10.0;
constexpr double kF0Floor = 75.0;
constexpr double kF0Ceil = 400.0;
constexpr int kMinSamples = 16000;      // 至少 1.0 秒
constexpr int kMinVoicedFrames = 100;   // 至少 1.0 秒有声

double Percentile(const std::vector<double> &sorted, double fraction) {
  if (sorted.empty()) return 0.0;
  const double position = fraction * static_cast<double>(sorted.size() - 1);
  const size_t low = static_cast<size_t>(std::floor(position));
  const size_t high = static_cast<size_t>(std::ceil(position));
  if (low == high) return sorted[low];
  const double weight = position - static_cast<double>(low);
  return sorted[low] * (1.0 - weight) + sorted[high] * weight;
}

struct BandEnergy {
  const char *name;
  double low_hz;
  double high_hz;
};

}  // namespace

int main(int argc, char **argv) {
  if (argc != 3) {
    fprintf(stderr, "usage: world_register input16k.wav profile.txt\n");
    return 2;
  }
  const char *input_path = argv[1];
  const char *profile_path = argv[2];

  const int length = GetAudioLength(input_path);
  if (length < kMinSamples) {
    fprintf(stderr, "REJECTED too_short samples=%d need=%d\n", length, kMinSamples);
    return 3;
  }
  std::vector<double> x(static_cast<size_t>(length));
  int rate = 0;
  int bits = 0;
  wavread(input_path, &rate, &bits, x.data());
  if (rate != 16000) {
    fprintf(stderr, "REJECTED bad_rate rate=%d need=16000\n", rate);
    return 4;
  }
  if (bits != 16) {
    fprintf(stderr, "REJECTED bad_bits bits=%d need=16\n", bits);
    return 4;
  }
  if (std::all_of(x.begin(), x.end(), [](double v) { return std::fabs(v) < 1e-7; })) {
    fprintf(stderr, "REJECTED silent_input\n");
    return 5;
  }

  DioOption dio_option;
  InitializeDioOption(&dio_option);
  dio_option.frame_period = kFramePeriodMs;
  dio_option.f0_floor = kF0Floor;
  dio_option.f0_ceil = kF0Ceil;
  dio_option.channels_in_octave = 2;
  dio_option.speed = 4;  // match world_convert / world_registration.py
  dio_option.allowed_range = 0.1;

  const int f0_length = GetSamplesForDIO(rate, length, kFramePeriodMs);
  std::vector<double> temporal_positions(static_cast<size_t>(f0_length));
  std::vector<double> f0(static_cast<size_t>(f0_length));
  Dio(x.data(), length, rate, &dio_option, temporal_positions.data(), f0.data());
  StoneMask(x.data(), length, rate, temporal_positions.data(), f0.data(), f0_length, f0.data());

  std::vector<size_t> voiced_index;
  voiced_index.reserve(static_cast<size_t>(f0_length));
  std::vector<double> voiced_f0;
  for (int i = 0; i < f0_length; ++i) {
    if (f0[static_cast<size_t>(i)] > 0.0) {
      voiced_index.push_back(static_cast<size_t>(i));
      voiced_f0.push_back(f0[static_cast<size_t>(i)]);
    }
  }
  if (static_cast<int>(voiced_index.size()) < kMinVoicedFrames) {
    fprintf(stderr, "REJECTED too_few_voiced voiced=%zu need=%d frames=%d\n",
            voiced_index.size(), kMinVoicedFrames, f0_length);
    return 5;
  }

  CheapTrickOption cheaptrick_option;
  InitializeCheapTrickOption(rate, &cheaptrick_option);
  cheaptrick_option.q1 = -0.15;
  cheaptrick_option.f0_floor = kF0Floor;
  cheaptrick_option.fft_size = 1024;  // fixed so profile and converter share one grid
  const int fft_size = 1024;
  const int bins = fft_size / 2 + 1;

  std::vector<double *> spectrogram(static_cast<size_t>(f0_length), nullptr);
  for (int i = 0; i < f0_length; ++i) {
    spectrogram[static_cast<size_t>(i)] = new double[static_cast<size_t>(bins)];
  }
  CheapTrick(x.data(), length, rate, temporal_positions.data(), f0.data(), f0_length,
             &cheaptrick_option, spectrogram.data());

  D4COption d4c_option;
  InitializeD4COption(&d4c_option);
  d4c_option.threshold = 0.85;
  std::vector<double *> aperiodicity(static_cast<size_t>(f0_length), nullptr);
  for (int i = 0; i < f0_length; ++i) {
    aperiodicity[static_cast<size_t>(i)] = new double[static_cast<size_t>(bins)];
  }
  D4C(x.data(), length, rate, temporal_positions.data(), f0.data(), f0_length,
      fft_size, &d4c_option, aperiodicity.data());

  // ---- 画像聚合：只用有声帧 ----
  std::vector<double> mean_power(static_cast<size_t>(bins), 0.0);
  std::vector<double> mean_ap(static_cast<size_t>(bins), 0.0);
  for (size_t index : voiced_index) {
    for (int b = 0; b < bins; ++b) {
      mean_power[static_cast<size_t>(b)] += spectrogram[index][b];
      mean_ap[static_cast<size_t>(b)] += aperiodicity[index][b];
    }
  }
  const double frames = static_cast<double>(voiced_index.size());
  for (int b = 0; b < bins; ++b) {
    mean_power[static_cast<size_t>(b)] /= frames;
    mean_ap[static_cast<size_t>(b)] /= frames;
  }

  std::vector<double> sorted_f0 = voiced_f0;
  std::sort(sorted_f0.begin(), sorted_f0.end());
  const double f0_median = Percentile(sorted_f0, 0.5);
  const double f0_p10 = Percentile(sorted_f0, 0.1);
  const double f0_p90 = Percentile(sorted_f0, 0.9);

  const BandEnergy bands[] = {{"80_400", 80.0, 400.0},
                              {"400_1000", 400.0, 1000.0},
                              {"1000_2000", 1000.0, 2000.0},
                              {"2000_4000", 2000.0, 4000.0},
                              {"4000_8000", 4000.0, 8000.0}};
  const double bin_hz = static_cast<double>(rate) / fft_size;
  const double total_energy =
      std::accumulate(mean_power.begin(), mean_power.end(), 0.0);
  if (!(total_energy > 0.0) || !std::isfinite(total_energy)) {
    fprintf(stderr, "REJECTED nonfinite_spectrum\n");
    return 6;
  }
  const BandEnergy ap_bands[] = {{"below_1000", 0.0, 1000.0},
                                 {"1000_3000", 1000.0, 3000.0},
                                 {"3000_8000", 3000.0, 8000.0}};

  FILE *out = fopen(profile_path, "w");
  if (out == nullptr) {
    fprintf(stderr, "REJECTED cannot_write_profile\n");
    return 2;
  }
  fprintf(out, "# target voice profile, WORLD 0.3.5 DIO+StoneMask/CheapTrick/D4C\n");
  fprintf(out, "rate %d\n", rate);
  fprintf(out, "frame_period_ms %.3f\n", kFramePeriodMs);
  fprintf(out, "fft_size %d\n", fft_size);
  fprintf(out, "samples %d\n", length);
  fprintf(out, "frames %d\n", f0_length);
  fprintf(out, "voiced_frames %zu\n", voiced_index.size());
  fprintf(out, "voiced_fraction %.6f\n",
          static_cast<double>(voiced_index.size()) / static_cast<double>(f0_length));
  fprintf(out, "f0_median_hz %.6f\n", f0_median);
  fprintf(out, "f0_p10_hz %.6f\n", f0_p10);
  fprintf(out, "f0_p90_hz %.6f\n", f0_p90);
  fprintf(out, "f0_min_hz %.6f\n", sorted_f0.front());
  fprintf(out, "f0_max_hz %.6f\n", sorted_f0.back());
  for (const auto &band : bands) {
    double energy = 0.0;
    for (int b = 0; b < bins; ++b) {
      const double hz = b * bin_hz;
      if (hz >= band.low_hz && hz < band.high_hz) energy += mean_power[static_cast<size_t>(b)];
    }
    fprintf(out, "band_db %s %.6f\n", band.name, 10.0 * std::log10(energy / total_energy));
  }
  for (const auto &band : ap_bands) {
    double sum = 0.0;
    int count = 0;
    for (int b = 0; b < bins; ++b) {
      const double hz = b * bin_hz;
      if (hz >= band.low_hz && hz < band.high_hz) {
        sum += mean_ap[static_cast<size_t>(b)];
        ++count;
      }
    }
    fprintf(out, "ap_mean %s %.6f\n", band.name, count > 0 ? sum / count : 0.0);
  }
  fprintf(out, "spectrum_bins %d\n", bins);
  fprintf(out, "spectrum_db");
  for (int b = 0; b < bins; ++b) {
    const double value = mean_power[static_cast<size_t>(b)];
    fprintf(out, " %.4f", 10.0 * std::log10(std::max(value, 1e-12)));
  }
  fprintf(out, "\n");
  fclose(out);

  for (int i = 0; i < f0_length; ++i) {
    delete[] spectrogram[static_cast<size_t>(i)];
    delete[] aperiodicity[static_cast<size_t>(i)];
  }

  printf("OK samples=%d frames=%d voiced=%zu voiced_fraction=%.6f f0_median=%.3f "
         "f0_p10=%.3f f0_p90=%.3f profile=%s\n",
         length, f0_length, voiced_index.size(),
         static_cast<double>(voiced_index.size()) / static_cast<double>(f0_length),
         f0_median, f0_p10, f0_p90, profile_path);
  return 0;
}
