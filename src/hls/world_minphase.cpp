// Fixed 1024-point WORLD minimum-phase stage. Experimental resource probe.
// Retains the WORLD/Ooura conjugated-c2c convention explicitly.
#include <cmath>
#include "world_minphase_twiddles.h"

namespace {
const int N = 1024;
void Forward(float re[N], float im[N]) {
#pragma HLS INLINE off
  // One shared radix-2 butterfly; no dynamic allocation or host dependencies.
  for (unsigned i = 0; i < N; ++i) {
    unsigned j = 0;
    for (int bit = 0; bit < 10; ++bit) {
#pragma HLS UNROLL
      j |= ((i >> bit) & 1) << (9-bit);
    }
    if (i < j) {
      float t = re[i]; re[i] = re[j]; re[j] = t;
      t = im[i]; im[i] = im[j]; im[j] = t;
    }
  }
  for (int stage = 1; stage <= 10; ++stage) {
#pragma HLS LOOP_FLATTEN off
    const int length = 1 << stage, half = length >> 1;
    for (int butterfly = 0; butterfly < N/2; ++butterfly) {
#pragma HLS PIPELINE II=2
#pragma HLS DEPENDENCE variable=re inter false
#pragma HLS DEPENDENCE variable=im inter false
        // Every address appears exactly once in a stage; stages drain before
        // advancing. The inter-iteration independence above is intentional.
        const int k = butterfly & (half-1);
        const int first = (butterfly >> (stage-1)) << stage;
        const int index = k << (10-stage);
        const float wr = world_twiddle_re[index], wi = world_twiddle_im[index];
        const int a = first+k, b = a+half;
        const float tr = wr * re[b] - wi * im[b];
        const float ti = wr * im[b] + wi * re[b];
        const float ar = re[a], ai = im[a];
        re[a] = ar + tr; im[a] = ai + ti;
        re[b] = ar - tr; im[b] = ai - ti;
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
#pragma HLS PIPELINE II=1
    const float amplitude = std::exp(re[i] / N);
    filter_re[i] = amplitude * std::cos(im[i] / N);
    filter_im[i] = amplitude * std::sin(im[i] / N);
  }
}
