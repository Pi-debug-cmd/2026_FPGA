// Offline synthetic benchmark of the unchanged upstream D4C stages.
#include <chrono>
#include <cstdio>
#include <memory>
#include <vector>
#ifdef __linux__
#include <sched.h>
#endif
#include "../build/generated/world_source_v035/pyworld-0.3.5/lib/World/src/d4c.cpp"

static double Clock() {
  return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}

int main() {
#ifdef __linux__
  cpu_set_t cpus; CPU_ZERO(&cpus); CPU_SET(0, &cpus);
  if (sched_setaffinity(0, sizeof(cpus), &cpus)) return 2;
#endif
  const int rate = 16000, length = 3712, frames = 4, output_fft = 1024, rounds = 100;
  const int internal_fft = static_cast<int>(pow(2.0, 1.0 +
      static_cast<int>(log(4.0 * rate / world::kFloorF0D4C + 1) / world::kLog2)));
  const int bands = static_cast<int>(MyMinDouble(world::kUpperLimit,
      rate / 2.0 - world::kFrequencyInterval) / world::kFrequencyInterval);
  const int window_length = static_cast<int>(world::kFrequencyInterval * internal_fft / rate) * 2 + 1;
  std::vector<double> signal(length), f0(frames, 160), times(frames), ap0(frames);
  for (int i = 0; i < length; ++i)
    signal[i] = .05 * (sin(2 * world::kPi * 160 * i / rate) + .3 * sin(2 * world::kPi * 320 * i / rate));
  for (int i = 0; i < frames; ++i) times[i] = .16 + .01 * i;
  const char *names[] = {"setup", "vuv", "centroid", "power", "group_delay", "coarse", "conversion", "cleanup"};
  double totals[8] = {}, checksum = 0;
  int processed = 0;
  for (int round = 0; round < rounds; ++round) {
    double last = Clock();
    auto lap = [&](int stage) { const double now = Clock(); totals[stage] += now - last; last = now; };
    RandnState rng = {}; randn_reseed(&rng);
    ForwardRealFFT forward = {}; InitializeForwardRealFFT(internal_fft, &forward);
    std::vector<double> window(window_length), coarse(bands + 2), axis(bands + 2), frequency(output_fft / 2 + 1);
    NuttallWindow(window_length, window.data());
    coarse[0] = -60; coarse.back() = -world::kMySafeGuardMinimum;
    for (int i = 0; i <= bands; ++i) axis[i] = i * world::kFrequencyInterval;
    axis.back() = rate / 2.0;
    for (int i = 0; i <= output_fft / 2; ++i) frequency[i] = static_cast<double>(i) * rate / output_fft;
    lap(0);
    D4CLoveTrain(signal.data(), rate, length, f0.data(), frames, times.data(), ap0.data(), &rng);
    lap(1);
    for (int frame = 0; frame < frames; ++frame) {
      if (ap0[frame] <= world::kThreshold) continue;
      ++processed;
      std::unique_ptr<double[]> centroid(new double[internal_fft / 2 + 1]);
      std::unique_ptr<double[]> power(new double[internal_fft / 2 + 1]);
      std::unique_ptr<double[]> group(new double[internal_fft / 2 + 1]);
      std::vector<double> output(output_fft / 2 + 1);
      lap(0);
      GetStaticCentroid(signal.data(), length, rate, 160, internal_fft, times[frame],
                        &forward, centroid.get(), &rng);
      lap(2);
      GetSmoothedPowerSpectrum(signal.data(), length, rate, 160, internal_fft, times[frame],
                               &forward, power.get(), &rng);
      lap(3);
      GetStaticGroupDelay(centroid.get(), power.get(), rate, 160, internal_fft, group.get());
      lap(4);
      GetCoarseAperiodicity(group.get(), rate, internal_fft, bands, window.data(), window_length,
                           &forward, &coarse[1]);
      for (int i = 0; i < bands; ++i) coarse[i + 1] = MyMinDouble(0.0, coarse[i + 1] + (160 - 100) / 50.0);
      lap(5);
      GetAperiodicity(axis.data(), coarse.data(), bands, frequency.data(), output_fft, output.data());
      lap(6);
      for (double value : output) checksum += value;
      centroid.reset(); power.reset(); group.reset();
      lap(7);
    }
    DestroyForwardRealFFT(&forward); lap(7);
  }
  std::printf("{\"kind\":\"world_d4c_internal_benchmark\",\"rounds\":%d,\"processed_frames\":%d,"
              "\"internal_fft\":%d,\"bands\":%d,\"checksum\":%.12g,\"stage_s\":{",
              rounds, processed, internal_fft, bands, checksum);
  for (int i = 0; i < 8; ++i) std::printf("%s\"%s\":%.9f", i ? "," : "", names[i], totals[i]);
  std::printf("},\"limitation\":\"Synthetic calls to private upstream helpers; no ALSA, voice recording, or end-to-end latency.\"}\n");
  return processed > 0 ? 0 : 1;
}
