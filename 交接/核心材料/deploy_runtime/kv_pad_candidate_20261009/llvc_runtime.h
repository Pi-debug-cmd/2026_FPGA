// llvc_runtime.h - model header, array indices and runtime state.
#ifndef LLVC_RUNTIME_H
#define LLVC_RUNTIME_H
#include <stdint.h>
#include <stddef.h>

#define HDR_SIZE 4096
#define ENC_DIM 384
#define DEC_DIM 192
#define N_ENC_LAYERS 6
#define NHEAD 6
#define HEAD_DIM 32
#define CHUNK 13
#define CTX_LEN 13
#define L_HOP 16
#define AUDIO_CHUNK 208        // 13 * 16
#define N_MATS 16

typedef struct {
    uint32_t magic, version;
    uint32_t L, enc_dim, dec_dim, chunk, ctx_len, pad;
    uint32_t float_off, scale_off, packed_off;
    uint32_t float_arr_off[128];
    uint32_t mat_packed_off[N_MATS];
    uint32_t mat_scale_off[N_MATS];
} model_header_t;

// Float array indices (fixed order, must match export).
enum {
    FA_IN_CONV_W = 48,
    FA_DCC_BASE = 49,                 // 7/block * 6 = 42 -> 49..90
    FA_PROJ_BASE = 91,               // 6 -> 91..96
    FA_TF_BASE = 97,                 // 12 -> 97..108
    FA_OUT_CONV_W = 109,
    FA_LABEL = 110,
    FA_POSENC_26 = 111
};
// per convnet block: 4 arrays (fw, fb, gw, gb), base = 4*i
// per DCC block: 7 arrays (dw, db, ln1w, ln1b, pb, ln2w, ln2b), base = 49+7*i
// proj: 105 e2d_e.w, 106 e2d_e.b, 107 e2d_l.w, 108 e2d_l.b, 109 d2e.w, 110 d2e.b
// transformer: 111 self.ipb,112 self.ob,113 cross.ipb,114 cross.ob,
//   115 ffn1.b,116 ffn2.b,117 norm1.w,118 norm1.b,119 norm2.w,120 norm2.b,
//   121 norm3.w,122 norm3.b

// Matrix indices (fixed order, must match export).
enum {
    M_ENC0=0, M_ENC1, M_ENC2, M_ENC3, M_ENC4, M_ENC5,
    M_SELF_Q, M_SELF_K, M_SELF_V, M_SELF_O,
    M_CROSS_Q, M_CROSS_K, M_CROSS_V, M_CROSS_O,
    M_FFN1, M_FFN2
};

// DCC per-layer context start indices (cumulative buf lengths).
static inline unsigned dcc_buf_start(unsigned i) {
    // sum_{h<i} 2*2^h = 2*(2^i - 1)
    return 2u * ((1u << i) - 1u);
}

typedef struct {
    const uint8_t *file;      // mmap base
    const model_header_t *hdr;
    const float *floats;
    const float *scales;
    const uint8_t *packed;
    // gemm packed input / int32 output
    uint8_t *xin;
    int32_t *yout;
    // named working buffers (encoder path: ENC_DIM stride, decoder path: DEC_DIM stride)
    float *e, *dccw, *dccout, *pwout, *l;
    float *base;               // in_conv output (mask is applied to THIS, not e)
    float *mem, *tgt, *q, *cq, *kv, *vv, *attn, *decout, *mout, *outin;
    // persistent state
    float *cn_ctx;            // convnet pre: 24 samples
    float *enc_buf;           // ring buffers, 204 frames, ENC_DIM stride
    float *mem_ctx;           // [13, DEC_DIM]
    float *tgt_ctx;           // [13, DEC_DIM]
    float *out_buf;           // [4, ENC_DIM]
    float *out_w_by_tap;      // optional transposed output-convolution weights
} llvc_t;

typedef struct {
    float e[CHUNK*ENC_DIM];
    float base[CHUNK*ENC_DIM];
    float l[CHUNK*ENC_DIM];
} llvc_features_t;

const float *fa(const llvc_t *m, uint32_t idx);
const uint8_t *mw(const llvc_t *m, uint32_t mi);
const float *ms(const llvc_t *m, uint32_t mi);

int llvc_load(llvc_t *m, const char *path);
// Process one 240-sample block built as cat(front(32), shifted(208)); writes 208.
void llvc_process_block(llvc_t *m, const float *block240, float *out208);
void llvc_process_front(llvc_t *m, const float *block240, llvc_features_t *features);
void llvc_process_back(llvc_t *m, const llvc_features_t *features, float *out208);
void llvc_reset_state(llvc_t *m);
#endif
