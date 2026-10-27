// Fixed 1024-point WORLD minimum-phase stage. Experimental resource probe.
// Retains the WORLD/Ooura conjugated-c2c convention explicitly.
#include <cmath>

namespace {
const int N = 1024;
void Forward(float re[N], float im[N]) {
  // One shared radix-2 butterfly; no dynamic allocation or host dependencies.
  for (unsigned i = 1, j = 0; i < N; ++i) {
    unsigned bit = N >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      float t = re[i]; re[i] = re[j]; re[j] = t;
      t = im[i]; im[i] = im[j]; im[j] = t;
    }
  }
  for (int stage = 1; stage <= 10; ++stage) {
    const int length = 1 << stage, half = length >> 1;
    for (int k = 0; k < half; ++k) {
      const float angle = -6.2831853071795864769f * k / length;
      const float wr = std::cos(angle), wi = std::sin(angle);
      for (int first = 0; first < N; first += length) {
        const int a = first + k, b = a + half;
        const float tr = wr * re[b] - wi * im[b];
        const float ti = wr * im[b] + wi * re[b];
        const float ar = re[a], ai = im[a];
        re[a] = ar + tr; im[a] = ai + ti;
        re[b] = ar - tr; im[b] = ai - ti;
      }
    }
  }
}
}

extern "C" void world_minphase(const float log_spectrum[513],
                                float filter_re[513], float filter_im[513]) {
#pragma HLS INTERFACE m_axi port=log_spectrum offset=slave bundle=input_mem depth=513
#pragma HLS INTERFACE m_axi port=filter_re offset=slave bundle=output_mem depth=513
#pragma HLS INTERFACE m_axi port=filter_im offset=slave bundle=output_mem depth=513
#pragma HLS INTERFACE s_axilite port=return bundle=control
  float re[N], im[N];
  for (int i = 0; i < N; ++i) {
    re[i] = log_spectrum[i <= N/2 ? i : N-i]; im[i] = 0;
  }
  Forward(re, im);
  // WORLD negates the imaginary cepstrum and its c2c adapter conjugates
  // the input again. Both signs cancel before the second standard FFT.
  im[0] = im[N/2] = 0;
  for (int i = 1; i < N/2; ++i) { re[i] *= 2; im[i] *= 2; }
  for (int i = N/2+1; i < N; ++i) re[i] = im[i] = 0;
  Forward(re, im);
  for (int i = 0; i <= N/2; ++i) {
    const float amplitude = std::exp(re[i] / N);
    filter_re[i] = amplitude * std::cos(im[i] / N);
    filter_im[i] = amplitude * std::sin(im[i] / N);
  }
}
