#include "gemm_s8.h"

unsigned gemm_s8(const ap_uint<64> *weights, const ap_uint<64> *input,
                      ap_int<32> *output, unsigned frames, unsigned input_channels, unsigned output_channels) {
#pragma HLS INTERFACE m_axi port=weights offset=slave bundle=weights_bus depth=32768 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=input offset=slave bundle=input_bus depth=1664 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=output offset=slave bundle=output_bus depth=13312 max_write_burst_length=64
#pragma HLS INTERFACE s_axilite port=weights bundle=control
#pragma HLS INTERFACE s_axilite port=input bundle=control
#pragma HLS INTERFACE s_axilite port=output bundle=control
#pragma HLS INTERFACE s_axilite port=frames bundle=control
#pragma HLS INTERFACE s_axilite port=input_channels bundle=control
#pragma HLS INTERFACE s_axilite port=output_channels bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    if (frames < 1 || frames > MAX_FRAMES) return 1;
    if (!input_channels || input_channels > CHANNELS || input_channels % LANES ||
        !output_channels || output_channels > CHANNELS || output_channels % LANES) return 2;
    // Eight 64-bit RAM banks: one packed bus word writes one bank, and eight
    // independent banks supply all64 signed8 multipliers each compute cycle.
    ap_uint<64> w[LANES / 8][CHANNELS * CHANNELS / LANES];
#pragma HLS ARRAY_PARTITION variable=w complete dim=1
#pragma HLS RESOURCE variable=w core=RAM_2P_BRAM
    ap_int<8> x[MAX_FRAMES][CHANNELS];
#pragma HLS ARRAY_PARTITION variable=x cyclic factor=8 dim=2
#pragma HLS RESOURCE variable=x core=RAM_2P_BRAM
load_weight_channels:
    for (unsigned k = 0; k < input_channels; ++k) {
#pragma HLS LOOP_TRIPCOUNT min=64 max=512 avg=512
load_weight_groups:
        for (unsigned group = 0; group < output_channels / 8; ++group) {
#pragma HLS LOOP_TRIPCOUNT min=8 max=64 avg=64
#pragma HLS PIPELINE II=1
            w[group % (LANES / 8)][(group / (LANES / 8)) * CHANNELS + k] = weights[k * (CHANNELS / 8) + group];
        }
    }
load_input_frames:
    for (unsigned t = 0; t < frames; ++t) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=26 avg=13
load_input_groups:
        for (unsigned group = 0; group < input_channels / 8; ++group) {
#pragma HLS PIPELINE II=1
            ap_uint<64> word = input[t * (CHANNELS / 8) + group];
unpack_input:
            for (int byte = 0; byte < 8; ++byte) {
#pragma HLS UNROLL
                x[t][group * 8 + byte] = word.range(byte * 8 + 7, byte * 8);
            }
        }
    }
compute_frames:
    for (unsigned t = 0; t < frames; ++t) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=26 avg=13
compute_tiles:
        for (unsigned tile = 0; tile < output_channels / LANES; ++tile) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=8 avg=8
            ap_int<32> acc[LANES];
#pragma HLS ARRAY_PARTITION variable=acc complete
zero_acc:
            for (int lane = 0; lane < LANES; ++lane) {
#pragma HLS UNROLL
                acc[lane] = 0;
            }
dot_product:
            for (unsigned k = 0; k < input_channels; ++k) {
#pragma HLS LOOP_TRIPCOUNT min=64 max=512 avg=512
#pragma HLS PIPELINE II=1
                ap_int<8> value = x[t][k];
parallel_groups:
                for (int group = 0; group < LANES / 8; ++group) {
#pragma HLS UNROLL
                    ap_uint<64> word = w[group][tile * CHANNELS + k];
parallel_bytes:
                    for (int byte = 0; byte < 8; ++byte) {
#pragma HLS UNROLL
                        ap_int<8> weight = word.range(byte * 8 + 7, byte * 8);
                        ap_int<16> product = value * weight;
#pragma HLS RESOURCE variable=product core=Mul
                        acc[group * 8 + byte] += product;
                    }
                }
            }
write_tile:
            for (int lane = 0; lane < LANES; ++lane) {
#pragma HLS PIPELINE II=1
                output[t * CHANNELS + tile * LANES + lane] = acc[lane];
            }
        }
    }
    return 0;
}
