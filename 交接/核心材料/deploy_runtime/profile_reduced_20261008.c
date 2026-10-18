/* Whole-model board timing on fixed float32 mono input. No audio device touched. */
#define _POSIX_C_SOURCE 200809L
#include "llvc_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef LLVC_PROFILE
extern double llvc_stage_seconds[8];
extern double llvc_gemm_quant_seconds[2],llvc_gemm_pl_seconds[2],llvc_gemm_dequant_seconds[2];
static const char *stage_names[8] = {
    "preprocess", "input_conv", "encoder", "projection_context",
    "self_attention", "cross_attention", "feed_forward", "output"
};
#endif

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s model.bin input.float32\n", argv[0]);
        return 2;
    }
    llvc_t model;
    if (llvc_load(&model, argv[1])) return 3;
    FILE *f = fopen(argv[2], "rb");
    if (!f) { perror("input"); return 4; }
    fseek(f, 0, SEEK_END);
    long bytes = ftell(f);
    fseek(f, 0, SEEK_SET);
    float *samples = malloc((size_t)bytes);
    if (!samples || fread(samples, 1, (size_t)bytes, f) != (size_t)bytes) return 5;
    fclose(f);
    const size_t n = (size_t)bytes / sizeof(float);
    float front[32] = {0}, block[240], output[208];
    double worst = 0, timed = 0;
    size_t chunks = 0, timed_chunks = 0;
    for (size_t start = 0; start + 224 <= n; start += 208) {
        memcpy(block, front, 32*sizeof(float));
        memcpy(block + 32, samples + start + 16, 208*sizeof(float));
        double before = now_seconds();
        llvc_process_block(&model, block, output);
        double elapsed = now_seconds() - before;
        memcpy(front, block + 32 + 176, 32*sizeof(float));
        if (chunks >= 10) {
            timed += elapsed;
            timed_chunks++;
            if (elapsed > worst) worst = elapsed;
        }
        chunks++;
    }
    printf("chunks=%zu timed=%zu mean_ms=%.3f max_ms=%.3f budget_ms=13.000 realtime_factor=%.2f\n",
           chunks, timed_chunks, 1000*timed/timed_chunks, 1000*worst,
           timed/(timed_chunks*0.013));
#ifdef LLVC_PROFILE
    for (unsigned i=0; i<8; ++i)
        printf("stage %-20s %.3f ms/chunk\n", stage_names[i],
               llvc_stage_seconds[i]*1000/chunks);
    for (unsigned i=0; i<2; ++i)
        printf("gemm_%s quant=%.3f pl=%.3f dequant=%.3f ms/chunk\n",
               i?"decoder":"encoder",llvc_gemm_quant_seconds[i]*1000/chunks,
               llvc_gemm_pl_seconds[i]*1000/chunks,
               llvc_gemm_dequant_seconds[i]*1000/chunks);
#endif
    free(samples);
    return 0;
}
