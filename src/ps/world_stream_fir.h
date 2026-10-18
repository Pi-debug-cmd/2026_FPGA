#ifndef VOICE7020_WORLD_STREAM_FIR_H
#define VOICE7020_WORLD_STREAM_FIR_H
#include <cmath>
struct Fir {
  double kernel[127], memory[254] = {};
  int pointer = 0;
  Fir() {
    const double pi = std::acos(-1.); double sum = 0;
    for (int i = 0; i < 127; ++i) {
      const int k = i - 63;
      kernel[i] = (k ? std::sin(2 * pi * .225 * k) / (pi * k) : .45) *
        (.54 - .46 * std::cos(2 * pi * i / 126));
      sum += kernel[i];
    }
    for (double &value : kernel) value /= sum;
  }
  double Step(double sample, bool calculate = true) {
    // Mirrored history removes a modulo from every tap without changing sum order.
    memory[pointer] = memory[pointer + 127] = sample; double sum = 0;
    if (calculate)
      for (int i = 0; i < 127; ++i) sum += kernel[i] * memory[pointer + 127 - i];
    if (++pointer == 127) pointer = 0;
    return sum;
  }
};

struct InterpolateFir {
  Fir coefficients;
  double memory[128] = {};
  int pointer = 0;
  void Step(double sample, double *pair) {
    memory[pointer] = memory[pointer + 64] = sample;
    pair[0] = pair[1] = 0;
    // Zero insertion leaves only even/odd coefficients in the two phases.
    // Keep the order of nonzero terms and the final factor of two unchanged.
    for (int i = 0; i < 64; ++i)
      pair[0] += coefficients.kernel[2 * i] * memory[pointer + 64 - i];
    for (int i = 0; i < 63; ++i)
      pair[1] += coefficients.kernel[2 * i + 1] * memory[pointer + 64 - i];
    pair[0] *= 2; pair[1] *= 2;
    if (++pointer == 64) pointer = 0;
  }
};

#endif
