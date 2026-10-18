// gemm_backend.h - abstract int8 GEMM backend.
// Host build uses a reference C implementation; ARM build uses the gemm_s8 PL.
#ifndef GEMM_BACKEND_H
#define GEMM_BACKEND_H
#include <stdint.h>
#include <stddef.h>

// Packed weight matrix: W[input][output], each input row has 512B stride.
// Packed input: X[frame][input], each frame has 512B stride.
// Output: Y[frame][output], each frame has 512 int32 stride.
// mi is the packed matrix index (reference ignores it, hardware uses it).
// Returns 0 on success.
int gemm_run_mi(unsigned mi, const uint8_t *weights, const uint8_t *input,
                int32_t *output, unsigned frames,
                unsigned input_channels, unsigned output_channels);

// Hardware-only one-time setup (pre-stages the 18 packed weight matrices).
// Reference build provides a no-op.
int gemm_setup(const void *llvc);

// Quantize a float activation buffer (frames*channels, frame-major with 512
// column stride) into packed int8 input. Returns the activation scale.
float gemm_quantize_input(const float *src, uint8_t *dst,
                          unsigned frames, unsigned channels);

// Fused dense layer: quantize float src (frames rows, in_c valid, src_stride
// float col stride), run the int8 GEMM, dequant int32 into float dst (frames
// rows, out_c valid, dst_stride float col stride) applying per-channel scales
// sw and bias. The DMA always uses a fixed 512-byte/512-int32 frame stride.
// weights is the packed matrix for this mi (HW uses pre-staged mi instead).
int gemm_dense_fused(unsigned mi, const uint8_t *weights,
                     const float *src, float *dst,
                     unsigned frames, unsigned in_c, unsigned out_c,
                     unsigned src_stride, unsigned dst_stride,
                     const float *sw, const float *bias);
#endif
