#ifndef POINTWISE_S8_H
#define POINTWISE_S8_H
#include <ap_int.h>
// Prototype for the measured 512-channel pointwise bottleneck. No voice weights.
enum { CHANNELS = 512, MAX_FRAMES = 13, LANES = 64,
       WEIGHT_WORDS = CHANNELS * CHANNELS / 8,
       INPUT_WORDS = MAX_FRAMES * CHANNELS / 8 };
// weights: W[input][output], eight signed bytes per 64-bit word, low byte first.
// input: X[frame][input], same packing. output: exact signed32 dot products.
unsigned pointwise_s8(const ap_uint<64> *weights, const ap_uint<64> *input,
                      ap_int<32> *output, unsigned frames);
#endif
