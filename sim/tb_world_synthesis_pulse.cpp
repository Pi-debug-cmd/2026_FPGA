#include <cmath>
#include <complex>
#include <cstdio>
#include <vector>

extern "C" void world_synthesis_pulse(
    const float periodic_filter_re[513],
    const float periodic_filter_im[513],
    const float aperiodic_filter_re[513],
    const float aperiodic_filter_im[513],
    const float raw_noise[1024], int noise_size,
    const float dc_remover[512], float response[1024]);

namespace {
const int N = 1024;
const double PI = 3.1415926535897932384626433832795;

void Fft(std::vector<std::complex<double> > *data, bool inverse) {
  for (int i = 1, j = 0; i < N; ++i) {
    int bit = N >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) std::swap((*data)[i], (*data)[j]);
  }
  for (int length = 2; length <= N; length <<= 1) {
    const double angle = (inverse ? 2.0 : -2.0) * PI / length;
    const std::complex<double> step(std::cos(angle), std::sin(angle));
    for (int base = 0; base < N; base += length) {
      std::complex<double> twiddle(1.0, 0.0);
      for (int k = 0; k < length / 2; ++k) {
        const std::complex<double> even = (*data)[base + k];
        const std::complex<double> odd =
          (*data)[base + k + length / 2] * twiddle;
        (*data)[base + k] = even + odd;
        (*data)[base + k + length / 2] = even - odd;
        twiddle *= step;
      }
    }
  }
  if (inverse)
    for (int i = 0; i < N; ++i) (*data)[i] /= N;
}

void LoadHermitian(const float re[513], const float im[513],
                   std::vector<std::complex<double> > *spectrum) {
  for (int i = 0; i <= N / 2; ++i)
    (*spectrum)[i] = std::complex<double>(re[i],
      i == 0 || i == N / 2 ? 0.0 : im[i]);
  for (int i = N / 2 + 1; i < N; ++i)
    (*spectrum)[i] = std::conj((*spectrum)[N - i]);
}

unsigned Next(unsigned *state) {
  *state = *state * 1664525u + 1013904223u;
  return *state;
}

double Unit(unsigned *state) {
  return static_cast<double>(Next(state) >> 8) / 16777216.0;
}

void MakeDcRemover(float remover[512]) {
  double sum = 0.0;
  for (int i = 0; i < 256; ++i) {
    remover[i] = static_cast<float>(0.5 -
      0.5 * std::cos(2.0 * PI * (i + 1.0) / 513.0));
    remover[511 - i] = remover[i];
    sum += remover[i] * 2.0;
  }
  for (int i = 0; i < 512; ++i) remover[i] /= static_cast<float>(sum);
}

void Reference(const float periodic_re[513], const float periodic_im[513],
               const float aperiodic_re[513], const float aperiodic_im[513],
               const float raw_noise[N], int noise_size,
               const float dc_remover[512], double output[N]) {
  std::vector<std::complex<double> > periodic(N), noise(N), aperiodic(N);
  LoadHermitian(periodic_re, periodic_im, &periodic);
  Fft(&periodic, true);

  double average = 0.0;
  for (int i = 0; i < noise_size; ++i) average += raw_noise[i];
  average /= noise_size;
  for (int i = 0; i < noise_size; ++i)
    noise[i] = std::complex<double>(raw_noise[i] - average, 0.0);
  Fft(&noise, false);

  for (int i = 0; i <= N / 2; ++i) {
    const std::complex<double> filter(aperiodic_re[i],
      i == 0 || i == N / 2 ? 0.0 : aperiodic_im[i]);
    aperiodic[i] = filter * noise[i];
  }
  for (int i = N / 2 + 1; i < N; ++i)
    aperiodic[i] = std::conj(aperiodic[N - i]);
  Fft(&aperiodic, true);

  double dc = 0.0;
  for (int i = 0; i < N / 2; ++i) dc += periodic[i].real();
  for (int i = 0; i < N; ++i) {
    const int shifted = (i + N / 2) & (N - 1);
    const double periodic_sample = i < N / 2 ? 0.0 :
      periodic[shifted].real() - dc * dc_remover[i - N / 2];
    output[i] = periodic_sample * std::sqrt(static_cast<double>(noise_size)) +
      aperiodic[shifted].real();
  }
}
}  // namespace

int main() {
  float periodic_re[513], periodic_im[513];
  float aperiodic_re[513], aperiodic_im[513];
  float noise[N], dc_remover[512], actual[N];
  double expected[N];
  MakeDcRemover(dc_remover);
  const int sizes[] = {32, 80, 160, 400, 1024};
  double worst_relative_l2 = 0.0;
  double worst_absolute = 0.0;
  unsigned state = 0x5a17c9e3u;

  for (int test = 0; test < 5; ++test) {
    const bool voiced = test != 1;
    for (int bin = 0; bin <= N / 2; ++bin) {
      const double phase = 0.002 * bin + 0.08 * (Unit(&state) - 0.5);
      const double periodic_magnitude = voiced ?
        (0.2 + 0.8 * std::exp(-bin / 180.0)) : 0.0;
      const double aperiodic_magnitude = 0.1 + 0.35 * std::exp(-bin / 240.0);
      periodic_re[bin] = static_cast<float>(periodic_magnitude * std::cos(phase));
      periodic_im[bin] = static_cast<float>(periodic_magnitude * std::sin(phase));
      aperiodic_re[bin] = static_cast<float>(aperiodic_magnitude * std::cos(-phase));
      aperiodic_im[bin] = static_cast<float>(aperiodic_magnitude * std::sin(-phase));
    }
    periodic_im[0] = periodic_im[512] = 0.0f;
    aperiodic_im[0] = aperiodic_im[512] = 0.0f;
    for (int i = 0; i < N; ++i)
      noise[i] = static_cast<float>(2.0 * Unit(&state) - 1.0);

    Reference(periodic_re, periodic_im, aperiodic_re, aperiodic_im,
              noise, sizes[test], dc_remover, expected);
    world_synthesis_pulse(periodic_re, periodic_im,
                          aperiodic_re, aperiodic_im,
                          noise, sizes[test], dc_remover, actual);
    double error_power = 0.0;
    double reference_power = 0.0;
    for (int i = 0; i < N; ++i) {
      const double error = actual[i] - expected[i];
      error_power += error * error;
      reference_power += expected[i] * expected[i];
      worst_absolute = std::fmax(worst_absolute, std::fabs(error));
    }
    const double relative = std::sqrt(error_power / reference_power);
    worst_relative_l2 = std::fmax(worst_relative_l2, relative);
  }

  const bool passed = worst_relative_l2 < 2.0e-5 && worst_absolute < 2.0e-5;
  std::printf("{\"kind\":\"world_synthesis_pulse_host\","
              "\"cases\":5,\"worst_relative_l2\":%.12g,"
              "\"worst_absolute\":%.12g,\"passed\":%s}\n",
              worst_relative_l2, worst_absolute, passed ? "true" : "false");
  return passed ? 0 : 1;
}
