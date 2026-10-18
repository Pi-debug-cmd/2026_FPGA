// gemm_ref.c - reference C int8 GEMM (host verification build).
#include "gemm_backend.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

int gemm_setup(const void *llvc) { (void)llvc; return 0; }

float gemm_quantize_input(const float *src, uint8_t *dst,
                          unsigned frames, unsigned channels) {
    float amax = 1e-8f;
    for (unsigned t = 0; t < frames; ++t) {
        const float *row = src + (size_t)t * 512;
        for (unsigned c = 0; c < channels; ++c) {
            float a = fabsf(row[c]);
            if (a > amax) amax = a;
        }
    }
    float sx = amax / 127.0f;
    memset(dst, 0, (size_t)frames * 512);
    for (unsigned t = 0; t < frames; ++t) {
        const float *row = src + (size_t)t * 512;
        uint8_t *out = dst + (size_t)t * 512;
        for (unsigned c = 0; c < channels; ++c) {
            float q = roundf(row[c] / sx);
            if (q > 127.0f) q = 127.0f;
            if (q < -128.0f) q = -128.0f;
            out[c] = (uint8_t)(int8_t)q;
        }
    }
    return sx;
}

int gemm_run_mi(unsigned mi, const uint8_t *weights, const uint8_t *input,
                int32_t *output, unsigned frames,
                unsigned input_channels, unsigned output_channels) {
    (void)mi;
    for (unsigned t = 0; t < frames; ++t) {
        const uint8_t *xrow = input + (size_t)t * 512;
        int32_t *yrow = output + (size_t)t * 512;
        for (unsigned j = 0; j < output_channels; ++j) {
            int32_t acc = 0;
            for (unsigned k = 0; k < input_channels; ++k) {
                int8_t x = (int8_t)xrow[k];
                int8_t w = (int8_t)weights[(size_t)k * 512 + j];
                acc += (int32_t)x * (int32_t)w;
            }
            yrow[j] = acc;
        }
    }
    return 0;
}

int gemm_dense_fused(unsigned mi, const uint8_t *weights,
                     const float *src, float *dst,
                     unsigned frames, unsigned in_c, unsigned out_c,
                     unsigned src_stride, unsigned dst_stride,
                     const float *sw, const float *bias) {
    // per-activation scale from src rows (src_stride)
    float amax = 1e-8f;
    for (unsigned t = 0; t < frames; ++t) {
        const float *r = src + (size_t)t * src_stride;
        for (unsigned c = 0; c < in_c; ++c) {
            float a = fabsf(r[c]);
            if (a > amax) amax = a;
        }
    }
    float sx = amax / 127.0f;
    uint8_t *xin = (uint8_t*)calloc((size_t)frames * 512, 1);
    int32_t *yout = (int32_t*)calloc((size_t)frames * 512, sizeof(int32_t));
    for (unsigned t = 0; t < frames; ++t) {
        const float *r = src + (size_t)t * src_stride;
        uint8_t *o = xin + (size_t)t * 512;
        for (unsigned c = 0; c < in_c; ++c) {
            float q = roundf(r[c] / sx);
            if (q > 127.0f) q = 127.0f;
            if (q < -128.0f) q = -128.0f;
            o[c] = (uint8_t)(int8_t)q;
        }
    }
    gemm_run_mi(mi, weights, xin, yout, frames, in_c, out_c);
    for (unsigned t = 0; t < frames; ++t) {
        const int32_t *r = yout + (size_t)t * 512;
        float *o = dst + (size_t)t * dst_stride;
        for (unsigned c = 0; c < out_c; ++c)
            o[c] = (float)r[c] * sx * sw[c] + bias[c];
    }
    free(xin); free(yout);
    return 0;
}
