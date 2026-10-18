#ifndef GEMM_S8_H
#define GEMM_S8_H
#include <ap_int.h>
enum {CHANNELS=512, LANES=64, MAX_FRAMES=26, WEIGHT_WORDS=32768, INPUT_WORDS=1664};
// W[input][output], X[frame][input], Y[frame][output] all have a512-element row stride.
// Channels must be positive multiples of64, <=512. Unused Y positions untouched.
// Packed W and X are signed bytes, low byte first; Y is exact signed32 accumulation.
unsigned gemm_s8(const ap_uint<64>*weights,const ap_uint<64>*input,ap_int<32>*output,
                 unsigned frames,unsigned input_channels,unsigned output_channels);
#endif
