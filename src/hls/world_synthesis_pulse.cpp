// Stateful-WORLD migration, pulse-response compute stage.
//
// The PS keeps pulse timing and the exact WORLD RandnState consumption order.
// It sends the raw random samples plus the two already-interpolated minimum-
// phase filters.  This kernel performs the three remaining FFT operations,
// noise centering, spectral multiplication, fftshift, periodic DC removal and
// final WORLD scaling for one pulse.  Keeping RNG on PS in this first stage
// makes the numerical contract replayable; RNG and overlap-add can be fused
// after this boundary is proven on RTL and board.
#include "world_minphase_twiddles.h"

namespace {
const int N = 1024;
const int BINS = N / 2 + 1;

void Transform(float re[N], float im[N], bool inverse) {
#pragma HLS INLINE off
  if (inverse)
    for (int i = 0; i < N; ++i) im[i] = -im[i];
  for (unsigned i = 0; i < N; ++i) {
    unsigned j = 0;
    for (int bit = 0; bit < 10; ++bit) {
#pragma HLS UNROLL
      j |= ((i >> bit) & 1) << (9 - bit);
    }
    if (i < j) {
      float value = re[i]; re[i] = re[j]; re[j] = value;
      value = im[i]; im[i] = im[j]; im[j] = value;
    }
  }
  for (int stage = 1; stage <= 10; ++stage) {
#pragma HLS LOOP_FLATTEN off
    const int length = 1 << stage;
    const int half = length >> 1;
    for (int butterfly = 0; butterfly < N / 2; ++butterfly) {
#pragma HLS PIPELINE II=2
#pragma HLS DEPENDENCE variable=re inter false
#pragma HLS DEPENDENCE variable=im inter false
      const int k = butterfly & (half - 1);
      const int first = (butterfly >> (stage - 1)) << stage;
      const int twiddle = k << (10 - stage);
      const int a = first + k;
      const int b = a + half;
      const float wr = world_twiddle_re[twiddle];
      const float wi = world_twiddle_im[twiddle];
      const float tr = wr * re[b] - wi * im[b];
      const float ti = wr * im[b] + wi * re[b];
      const float ar = re[a];
      const float ai = im[a];
      re[a] = ar + tr;
      im[a] = ai + ti;
      re[b] = ar - tr;
      im[b] = ai - ti;
    }
  }
  if (inverse)
    for (int i = 0; i < N; ++i) {
#pragma HLS PIPELINE II=1
      re[i] /= N;
      im[i] = -im[i] / N;
    }
}

void LoadHermitian(const float half_re[BINS], const float half_im[BINS],
                   float re[N], float im[N]) {
  for (int i = 0; i < BINS; ++i) {
    re[i] = half_re[i];
    im[i] = (i == 0 || i == N / 2) ? 0.0f : half_im[i];
  }
  for (int i = BINS; i < N; ++i) {
    re[i] = half_re[N - i];
    im[i] = -half_im[N - i];
  }
}
}  // namespace

extern "C" void world_synthesis_pulse(
    const float periodic_filter_re[BINS],
    const float periodic_filter_im[BINS],
    const float aperiodic_filter_re[BINS],
    const float aperiodic_filter_im[BINS],
    const float raw_noise[N], int noise_size,
    const float dc_remover[N / 2], float response[N]) {
#pragma HLS INTERFACE m_axi port=periodic_filter_re offset=slave bundle=filter_mem depth=513
#pragma HLS INTERFACE m_axi port=periodic_filter_im offset=slave bundle=filter_mem depth=513
#pragma HLS INTERFACE m_axi port=aperiodic_filter_re offset=slave bundle=filter_mem depth=513
#pragma HLS INTERFACE m_axi port=aperiodic_filter_im offset=slave bundle=filter_mem depth=513
#pragma HLS INTERFACE m_axi port=raw_noise offset=slave bundle=noise_mem depth=1024
#pragma HLS INTERFACE m_axi port=dc_remover offset=slave bundle=noise_mem depth=512
#pragma HLS INTERFACE m_axi port=response offset=slave bundle=output_mem depth=1024
#pragma HLS INTERFACE s_axilite port=noise_size bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#pragma HLS ALLOCATION function instances=Transform limit=1

  float periodic_re[N], periodic_im[N];
  float noise_re[N], noise_im[N];
  float aperiodic_re[N], aperiodic_im[N];

  LoadHermitian(periodic_filter_re, periodic_filter_im,
                periodic_re, periodic_im);
  Transform(periodic_re, periodic_im, true);

  const int used = noise_size < 1 ? 1 : (noise_size > N ? N : noise_size);
  float average = 0.0f;
  for (int i = 0; i < used; ++i) average += raw_noise[i];
  average /= used;
  for (int i = 0; i < N; ++i) {
    noise_re[i] = i < used ? raw_noise[i] - average : 0.0f;
    noise_im[i] = 0.0f;
  }
  Transform(noise_re, noise_im, false);

  for (int i = 0; i < BINS; ++i) {
    aperiodic_re[i] =
      aperiodic_filter_re[i] * noise_re[i] -
      aperiodic_filter_im[i] * noise_im[i];
    aperiodic_im[i] =
      aperiodic_filter_re[i] * noise_im[i] +
      aperiodic_filter_im[i] * noise_re[i];
  }
  for (int i = BINS; i < N; ++i) {
    aperiodic_re[i] = aperiodic_re[N - i];
    aperiodic_im[i] = -aperiodic_im[N - i];
  }
  aperiodic_im[0] = 0.0f;
  aperiodic_im[N / 2] = 0.0f;
  Transform(aperiodic_re, aperiodic_im, true);

  float dc_component = 0.0f;
  for (int i = 0; i < N / 2; ++i) dc_component += periodic_re[i];
  const float noise_gain = __builtin_sqrtf(static_cast<float>(used));
  for (int i = 0; i < N; ++i) {
#pragma HLS PIPELINE II=1
    const int shifted = (i + N / 2) & (N - 1);
    const float periodic = i < N / 2 ? 0.0f :
      periodic_re[shifted] - dc_component * dc_remover[i - N / 2];
    response[i] = periodic * noise_gain + aperiodic_re[shifted];
  }
}
