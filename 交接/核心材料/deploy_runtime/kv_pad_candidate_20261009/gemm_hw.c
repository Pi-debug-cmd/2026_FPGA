// gemm_hw.c - hardware gemm_s8 backend via /dev/gemm_dma (cached user mapping
// with explicit cache sync) and /dev/mem for regs.
#include "gemm_backend.h"
#include "llvc_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <arm_neon.h>
#ifdef LLVC_PIPELINE
#include <pthread.h>
static pthread_mutex_t gemm_mutex=PTHREAD_MUTEX_INITIALIZER;
#endif
#ifdef LLVC_PROFILE
#include <time.h>
double llvc_gemm_quant_seconds[2],llvc_gemm_pl_seconds[2],llvc_gemm_dequant_seconds[2];
static double gemm_now(void){struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);
    return (double)ts.tv_sec+(double)ts.tv_nsec*1e-9;}
#endif

#ifndef GEMM_REGS_PHYS
#define GEMM_REGS_PHYS 0x43D00000u
#endif
#define GEMM_DMA_DEV "/dev/gemm_dma"
#define GEMM_DMA_MAGIC 'G'
#define GEMM_DMA_GET_PHYS _IOR(GEMM_DMA_MAGIC, 1, unsigned long long)
#define GEMM_DMA_GET_SIZE _IOR(GEMM_DMA_MAGIC, 2, unsigned long long)
struct gemm_range_arg { unsigned long long off; unsigned long long size; };
#define GEMM_CACHE_CLEAN _IOW(GEMM_DMA_MAGIC, 3, struct gemm_range_arg)
#define GEMM_CACHE_INV   _IOW(GEMM_DMA_MAGIC, 4, struct gemm_range_arg)

#define W_STRIDE 262144u
#define N_W 18u
#define GEMM_IO_BYTES (26u*512u + 26u*512u*4u)
#define REGION_NEED (N_W*W_STRIDE + 2u*GEMM_IO_BYTES)
#define GEMM_LANES 128u
static unsigned padded_channels(unsigned channels) {
    return (channels + GEMM_LANES - 1u) & ~(GEMM_LANES - 1u);
}

static volatile uint32_t *regs;
static uint8_t *dma;
static int mem_fd;
static int dma_fd;
static int inited = 0;
static uint32_t dma_phys;
static uint32_t w_phys[N_W];
static float fused_kv_scales[2][384];
static uint32_t in_phys[2], out_phys[2];
static unsigned long long in_off[2], out_off[2];

static void cache_clean(unsigned long long off, unsigned long long size){
    struct gemm_range_arg ra={off,size};
    if(ioctl(dma_fd,GEMM_CACHE_CLEAN,&ra)) perror("cache_clean");
}
static void cache_inv(unsigned long long off, unsigned long long size){
    struct gemm_range_arg ra={off,size};
    if(ioctl(dma_fd,GEMM_CACHE_INV,&ra)) perror("cache_inv");
}

int gemm_setup(const void *llvc) {
    const llvc_t *m = (const llvc_t*)llvc;
    unsigned long long phys = 0, size = 0;

    dma_fd = open(GEMM_DMA_DEV, O_RDWR | O_SYNC);
    if (dma_fd < 0) { perror(GEMM_DMA_DEV); return 1; }
    if (ioctl(dma_fd, GEMM_DMA_GET_PHYS, &phys) < 0 ||
        ioctl(dma_fd, GEMM_DMA_GET_SIZE, &size) < 0) {
        perror("gemm_dma ioctl"); return 1;
    }
    if (size < REGION_NEED) {
        fprintf(stderr, "gemm_dma region too small: %llu < %u\n",
                size, REGION_NEED); return 1;
    }
    dma_phys = (uint32_t)phys;
    dma = mmap(NULL, (size_t)size, PROT_READ|PROT_WRITE, MAP_SHARED,
               dma_fd, 0);
    if (dma == MAP_FAILED) { perror("gemm_dma mmap"); return 1; }

    mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (mem_fd < 0) { perror("/dev/mem"); return 1; }
    regs = mmap(NULL, 0x10000, PROT_READ|PROT_WRITE, MAP_SHARED,
                mem_fd, GEMM_REGS_PHYS);
    if (regs == MAP_FAILED) { perror("regs mmap"); return 1; }

    for (unsigned i = 0; i < N_W; ++i) {
        w_phys[i] = dma_phys + i*W_STRIDE;
        if (i >= 16) continue;
        unsigned in_c;
        if (i < 6) in_c = 384;                       /* encoder pointwise */
        else if (i == 15) in_c = 384;                /* FFN2 */
        else in_c = 192;                             /* attention + FFN1 */
        size_t bytes = (size_t)in_c * 512;
        memset(dma + (size_t)i*W_STRIDE, 0, W_STRIDE);
        memcpy(dma + (size_t)i*W_STRIDE, mw(m, i), bytes);
    }
    // Each attention block reads the same 26x192 input for K and V. Pack the
    // two 192-output matrices side by side as one 384-output matrix.
    for (unsigned pair = 0; pair < 2; ++pair) {
        unsigned kmi = pair ? M_CROSS_K : M_SELF_K;
        uint8_t *combined = dma + (size_t)(16 + pair)*W_STRIDE;
        const uint8_t *kw = mw(m, kmi), *vw = mw(m, kmi + 1);
        memset(combined, 0, W_STRIDE);
        for (unsigned c = 0; c < DEC_DIM; ++c) {
            memcpy(combined + (size_t)c*512, kw + (size_t)c*512, DEC_DIM);
            memcpy(combined + (size_t)c*512 + DEC_DIM,
                   vw + (size_t)c*512, DEC_DIM);
        }
        memcpy(fused_kv_scales[pair], ms(m, kmi), DEC_DIM*sizeof(float));
        memcpy(fused_kv_scales[pair] + DEC_DIM, ms(m, kmi + 1),
               DEC_DIM*sizeof(float));
    }
    // writeback weights once
    cache_clean(0, N_W*W_STRIDE);

    for(unsigned group=0;group<2;++group){
        in_off[group]=N_W*W_STRIDE+(unsigned long long)group*GEMM_IO_BYTES;
        out_off[group]=in_off[group]+26u*512u;
        in_phys[group]=dma_phys+(uint32_t)in_off[group];
        out_phys[group]=dma_phys+(uint32_t)out_off[group];
    }
    inited = 1;
    return 0;
}

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
    float sx = amax/127.0f;
    memset(dst, 0, (size_t)frames*512);
    for (unsigned t = 0; t < frames; ++t) {
        const float *row = src + (size_t)t * 512;
        uint8_t *o = dst + (size_t)t*512;
        for (unsigned c = 0; c < channels; ++c) {
            float q = roundf(row[c]/sx);
            if (q > 127) q = 127;
            if (q < -128) q = -128;
            o[c] = (uint8_t)(int8_t)q;
        }
    }
    return sx;
}

int gemm_run_mi(unsigned mi, const uint8_t *weights, const uint8_t *input,
                int32_t *output, unsigned frames,
                unsigned input_channels, unsigned output_channels) {
    (void)weights;
    if (!inited) { fputs("gemm not set up\n", stderr); return 1; }
    unsigned group=mi<6?0:1;
    uint8_t *in_v = dma + in_off[group];
    memcpy(in_v, input, (size_t)frames*512);
    for (unsigned t=0;t<frames;++t)
        memset(in_v+(size_t)t*512+input_channels,0,
               padded_channels(input_channels)-input_channels);
    cache_clean(in_off[group], (unsigned long long)frames*512);

    regs[0x18/4] = w_phys[mi];
    regs[0x20/4] = in_phys[group];
    regs[0x28/4] = out_phys[group];
    regs[0x30/4] = frames;
    regs[0x38/4] = padded_channels(input_channels);
    regs[0x40/4] = padded_channels(output_channels);
    regs[0x00/4] = 1;
    while (!(regs[0x00/4] & 0x2)) { }

    size_t out_bytes = (size_t)frames*512*sizeof(int32_t);
    cache_inv(out_off[group], out_bytes);
    int32_t *out_v = (int32_t*)(dma + out_off[group]);
    memcpy(output, out_v, out_bytes);
    return 0;
}

// ---------- NEON quantize directly into DMA in region ----------
// src float rows are at src_stride; DMA in rows are fixed at 512 bytes.
static int32x4_t quantize_four(float32x4_t source,float32x4_t inv){
    float32x4_t v=vmulq_f32(source,inv);
    uint32x4_t positive=vcgeq_f32(v,vdupq_n_f32(0.0f));
    float32x4_t half=vbslq_f32(positive,vdupq_n_f32(0.5f),vdupq_n_f32(-0.5f));
    int32x4_t q=vcvtq_s32_f32(vaddq_f32(v,half));
    return vminq_s32(vmaxq_s32(q,vdupq_n_s32(-128)),vdupq_n_s32(127));
}
static float quantize_into_dma(const float *src, uint8_t *dst,
                               unsigned frames, unsigned in_c,
                               unsigned src_stride){
    float amax = 1e-8f;
    for (unsigned t=0;t<frames;++t){
        const float *r=src+(size_t)t*src_stride;
        float32x4_t vmax=vdupq_n_f32(1e-8f);
        for (unsigned c=0;c<in_c;c+=4)
            vmax=vmaxq_f32(vmax,vabsq_f32(vld1q_f32(r+c)));
        float32x2_t m=vpmax_f32(vget_low_f32(vmax),vget_high_f32(vmax));
        m=vpmax_f32(m,m);
        float a=vget_lane_f32(m,0);
        if (a>amax) amax=a;
    }
    float sx=amax/127.0f;
    float32x4_t vinv=vdupq_n_f32(1.0f/sx);
    for (unsigned t=0;t<frames;++t){
        const float *r=src+(size_t)t*src_stride;
        int8_t *o=(int8_t*)(dst+(size_t)t*512);
        for (unsigned c=0;c<in_c;c+=16){
            int32x4_t q0=quantize_four(vld1q_f32(r+c),vinv);
            int32x4_t q1=quantize_four(vld1q_f32(r+c+4),vinv);
            int32x4_t q2=quantize_four(vld1q_f32(r+c+8),vinv);
            int32x4_t q3=quantize_four(vld1q_f32(r+c+12),vinv);
            int16x8_t w0=vcombine_s16(vmovn_s32(q0),vmovn_s32(q1));
            int16x8_t w1=vcombine_s16(vmovn_s32(q2),vmovn_s32(q3));
            int8x16_t b=vcombine_s8(vmovn_s16(w0),vmovn_s16(w1));
            vst1q_s8(o+c,b);
        }
    }
    return sx;
}

// ---------- NEON dequant directly from DMA out int32 ----------
// DMA out rows are fixed at 512 int32; dst float rows are at dst_stride.
static void dequant_from_dma(const int32_t *yr, float *dst,
                             unsigned frames, unsigned out_c,
                             unsigned dst_stride,
                             float sx, const float *sw, const float *bias){
    float32x4_t vsx=vdupq_n_f32(sx);
    for (unsigned t=0;t<frames;++t){
        const int32_t *r=yr+(size_t)t*512;
        float *o=dst+(size_t)t*dst_stride;
        for (unsigned c=0;c<out_c;c+=4){
            float32x4_t vf=vcvtq_f32_s32(vld1q_s32(r+c));
            vf=vmulq_f32(vf,vsx);
            vf=vmulq_f32(vf,vld1q_f32(sw+c));
            vf=vaddq_f32(vf,vld1q_f32(bias+c));
            vst1q_f32(o+c,vf);
        }
    }
}

// ---------- fused dense (no intermediate CPU buffers) ----------
int gemm_dense_fused(unsigned mi, const uint8_t *weights,
                     const float *src, float *dst,
                     unsigned frames, unsigned in_c, unsigned out_c,
                     unsigned src_stride, unsigned dst_stride,
                     const float *sw, const float *bias){
    (void)weights;
    if (!inited){ fputs("gemm not set up\n", stderr); return 1; }
    unsigned group=mi<6?0:1;
#ifdef LLVC_PROFILE
    double t0=gemm_now();
#endif
    uint8_t *in_v=dma+in_off[group];
    // The kernel reads padded_channels(in_c), never the unused tail up to
    // 512. Quantization overwrites all valid columns; clear only padding.
    unsigned padded=padded_channels(in_c);
    for(unsigned t=0;t<frames;++t)
        memset(in_v+(size_t)t*512+in_c,0,padded-in_c);
    float sx=quantize_into_dma(src, in_v, frames, in_c, src_stride);
    cache_clean(in_off[group], (unsigned long long)frames*512);
#ifdef LLVC_PROFILE
    double t1=gemm_now();llvc_gemm_quant_seconds[group]+=t1-t0;
#endif
#ifdef LLVC_PIPELINE
    pthread_mutex_lock(&gemm_mutex);
#endif

    regs[0x18/4]=w_phys[mi];
    regs[0x20/4]=in_phys[group];
    regs[0x28/4]=out_phys[group];
    regs[0x30/4]=frames;
    regs[0x38/4]=padded_channels(in_c);
    regs[0x40/4]=padded_channels(out_c);
    regs[0x00/4]=1;
    while (!(regs[0x00/4] & 0x2)) { }
#ifdef LLVC_PIPELINE
    pthread_mutex_unlock(&gemm_mutex);
#endif
#ifdef LLVC_PROFILE
    double t2=gemm_now();llvc_gemm_pl_seconds[group]+=t2-t1;
#endif

    size_t out_bytes=(size_t)frames*512*sizeof(int32_t);
    cache_inv(out_off[group], out_bytes);
    int32_t *out_v=(int32_t*)(dma+out_off[group]);
    dequant_from_dma(out_v, dst, frames, out_c, dst_stride, sx, sw, bias);
#ifdef LLVC_PROFILE
    llvc_gemm_dequant_seconds[group]+=gemm_now()-t2;
#endif
    return 0;
}

int gemm_dense_kv_fused(unsigned kvmi, const float *src, float *dst,
                        unsigned frames, const float *kbias,
                        const float *vbias) {
    unsigned pair;
    if (kvmi == M_SELF_K) pair = 0;
    else if (kvmi == M_CROSS_K) pair = 1;
    else return 1;
    float bias[2*DEC_DIM];
    memcpy(bias, kbias, DEC_DIM*sizeof(float));
    memcpy(bias + DEC_DIM, vbias, DEC_DIM*sizeof(float));
    return gemm_dense_fused(16 + pair, NULL, src, dst, frames,
                            DEC_DIM, 2*DEC_DIM, DEC_DIM, 2*DEC_DIM,
                            fused_kv_scales[pair], bias);
}
