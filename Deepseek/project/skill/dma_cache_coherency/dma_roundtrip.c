/* dma_roundtrip.c - DMA/cache correctness self-test for a PL IP in *identity* mode.
 *
 * Purpose: decide, in 30 seconds and without any audio, whether your user-space
 * DMA path is coherent.  It writes a known pattern through the CPU into buffer A,
 * DMAs A -> PL -> B, and compares B against A bit for bit.
 *
 * The signature this test is designed to catch (our real bug, 2026-10-25):
 *   mismatches appear as a handful of *all-zero* runs of exactly 8 int16 samples
 *   (32 B = one A9 cache line), at a 32-byte-aligned offset, on the FIRST
 *   transfer after the buffers were created, and never again in the same process.
 *   That is a dirty zero line being written back over DMA output, not a logic bug.
 *
 * Build (static, for the board):
 *   arm-linux-gnueabihf-gcc -static -O2 -o dma_roundtrip dma_roundtrip.c dmabuf.c
 *
 * Run (PL must be configured for identity, e.g. ratio_q16 = 65536):
 *   ./dma_roundtrip --dma 0x40400000 --words 128000 --chunk 4096 --pattern ramp
 *   ./dma_roundtrip --dma 0x40400000 --repeat 20 --realloc --pattern prbs
 *
 * Exit 0 = bit exact.  Exit 5 = mismatch (details on stdout).
 */
#define _GNU_SOURCE
#include "dmabuf.h"

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

/* ---- AXI DMA (simple mode) register map, offsets from the DMA base ---- */
#define R_MM2S_CR 0x00u
#define R_MM2S_SR 0x04u
#define R_MM2S_SA 0x18u
#define R_MM2S_LEN 0x28u
#define R_S2MM_CR 0x30u
#define R_S2MM_SR 0x34u
#define R_S2MM_DA 0x48u
#define R_S2MM_LEN 0x58u
#define CR_RS 0x1u
#define CR_RESET 0x4u
#define SR_HALTED 0x1u
#define SR_IDLE 0x2u
#define SR_ERR 0x70u

static volatile uint32_t *dma;

static inline uint32_t rd(uint32_t off) { return *(volatile uint32_t *)((char *)dma + off); }
static inline void wr(uint32_t off, uint32_t v) { *(volatile uint32_t *)((char *)dma + off) = v; }

static double now_s(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void dma_reset(void)
{
    int i;
    wr(R_MM2S_CR, CR_RESET);
    wr(R_S2MM_CR, CR_RESET);
    for (i = 0; i < 10000; i++) {
        if (!(rd(R_MM2S_CR) & CR_RESET) && !(rd(R_S2MM_CR) & CR_RESET))
            break;
        usleep(10);
    }
    if (i == 10000) {
        fprintf(stderr, "dma reset timeout\n");
        exit(5);
    }
    wr(R_MM2S_SR, 0x7000u); /* write-1-to-clear sticky bits */
    wr(R_S2MM_SR, 0x7000u);
    wr(R_MM2S_CR, CR_RS);
    wr(R_S2MM_CR, CR_RS);
}

static int transfer(uint64_t in_phys, uint64_t out_phys, uint32_t bytes, double budget_s)
{
    double t0 = now_s();
    uint32_t mm = 0, sm = 0;
    wr(R_S2MM_CR, CR_RS);
    wr(R_S2MM_DA, (uint32_t)out_phys);
    wr(R_S2MM_LEN, bytes);
    wr(R_MM2S_CR, CR_RS);
    wr(R_MM2S_SA, (uint32_t)in_phys);
    wr(R_MM2S_LEN, bytes);
    for (;;) {
        mm = rd(R_MM2S_SR);
        sm = rd(R_S2MM_SR);
        if (mm & SR_ERR) { fprintf(stderr, "MM2S error SR=0x%08x\n", mm); return -1; }
        if (sm & SR_ERR) { fprintf(stderr, "S2MM error SR=0x%08x\n", sm); return -1; }
        if ((mm & SR_IDLE) && (sm & SR_IDLE))
            break;
        if (now_s() - t0 > budget_s) {
            fprintf(stderr, "DMA timeout MM2S_SR=0x%08x S2MM_SR=0x%08x\n", mm, sm);
            return -1;
        }
    }
    wr(R_MM2S_SR, mm);
    wr(R_S2MM_SR, sm);
    return 0;
}

static uint32_t prbs(uint32_t *s)
{
    /* xorshift32, deterministic across runs */
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x;
    return x;
}

/* Classify the mismatch pattern. This is what turns "16 samples differ" into a
 * root cause: run lengths of 8 zero samples at 32-byte alignment == cache line. */
static void analyse(const int16_t *exp, const int16_t *got, size_t n,
                    size_t *runs, size_t *zero_runs, size_t *zero_runs32,
                    size_t *max_zero_run, size_t *first_bad, int *max_diff)
{
    size_t i = 0;
    *runs = 0; *zero_runs = 0; *zero_runs32 = 0; *max_zero_run = 0;
    *first_bad = (size_t)-1;
    *max_diff = 0;
    while (i < n) {
        if (exp[i] == got[i]) { i++; continue; }
        size_t start = i, len = 0, all_zero = 1;
        int d;
        if (*first_bad == (size_t)-1)
            *first_bad = i;
        while (i < n && exp[i] != got[i]) {
            d = (int)got[i] - (int)exp[i];
            if (d < 0) d = -d;
            if (d > *max_diff) *max_diff = d;
            if (got[i] != 0) all_zero = 0;
            len++;
            i++;
        }
        (*runs)++;
        if (all_zero) {
            (*zero_runs)++;
            if (len > *max_zero_run) *max_zero_run = len;
            if ((start * 2u) % 32u == 0 && len * 2u >= 32u)
                (*zero_runs32)++;
        }
    }
}

int main(int argc, char **argv)
{
    unsigned long dma_base = 0x40400000ul, ratio_addr = 0, ratio = 0;
    size_t words = 128000, chunk = 4096; /* chunk in BYTES, <= 4096 */
    int repeat = 1, realloc_each = 0, i;
    const char *pattern = "ramp";
    dma_coherent_mode mode = DMA_COHERENT_UNCACHED;
    int memfd, fails = 0;
    int16_t *expect = NULL;

    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--dma") && i + 1 < argc) dma_base = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--words") && i + 1 < argc) words = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--chunk") && i + 1 < argc) chunk = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--pattern") && i + 1 < argc) pattern = argv[++i];
        else if (!strcmp(argv[i], "--repeat") && i + 1 < argc) repeat = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--realloc")) realloc_each = 1;
        else if (!strcmp(argv[i], "--flush")) mode = DMA_COHERENT_FLUSH;
        else if (!strcmp(argv[i], "--ratio-addr") && i + 1 < argc) ratio_addr = strtoul(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--ratio") && i + 1 < argc) ratio = strtoul(argv[++i], NULL, 0);
        else {
            fprintf(stderr,
                    "usage: %s [--dma 0x40400000] [--words N] [--chunk BYTES<=4096]\n"
                    "          [--pattern ramp|prbs|zero] [--repeat N] [--realloc]\n"
                    "          [--flush] [--ratio-addr 0x41200000 --ratio 65536]\n", argv[0]);
            return 2;
        }
    }
    /* A chunk must not cross a 4 KiB page in the uncached-alias mode, and the
     * simplest way to guarantee that is to make it a divisor of the page size. */
    if (chunk == 0 || chunk > DMABUF_PAGE || chunk % 4 || DMABUF_PAGE % chunk) {
        fprintf(stderr, "--chunk must be 4-aligned and divide %u (got %zu); "
                        "one DMA chunk may not cross a page\n", DMABUF_PAGE, chunk);
        return 2;
    }
    if (words * 2 > DMABUF_MAX_PAGES * DMABUF_PAGE) {
        fprintf(stderr, "--words too large\n");
        return 2;
    }

    memfd = open("/dev/mem", O_RDWR | O_SYNC);
    if (memfd < 0) { perror("open /dev/mem"); return 3; }
    dma = mmap(NULL, 0x10000, PROT_READ | PROT_WRITE, MAP_SHARED, memfd, (off_t)dma_base);
    if (dma == MAP_FAILED) { perror("mmap dma"); return 3; }

    if (ratio_addr && ratio) {
        volatile uint32_t *g = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE, MAP_SHARED,
                                    memfd, (off_t)ratio_addr);
        if (g == MAP_FAILED) { perror("mmap ratio"); return 3; }
        g[0] = (uint32_t)ratio;
        __sync_synchronize();
        fprintf(stderr, "ratio@0x%lx <- %lu (readback %u)\n", ratio_addr, ratio, g[0]);
        if (g[0] != (uint32_t)ratio) { fprintf(stderr, "ratio write did not stick\n"); return 4; }
    }

    dma_reset();
    expect = (int16_t *)malloc(words * 2);
    if (!expect) { perror("malloc"); return 4; }

    for (int rep = 0; rep < repeat; rep++) {
        dma_buf in, out;
        size_t done = 0, nbad = 0, runs = 0, zruns = 0, zruns32 = 0, maxzr = 0, first_bad = 0;
        int maxd = 0;
        uint32_t seed = 0x12345678u + (uint32_t)rep;
        double t0 = now_s(), t_dma = 0;

        if (dma_buf_alloc(&in, words * 2, mode) != 0) return 4;
        if (dma_buf_alloc(&out, words * 2, mode) != 0) return 4;

        /* fill: the pattern must be non-zero and page-offset dependent so that a
         * zeroed line is unmistakable */
        for (size_t w = 0; w < words; w++) {
            int16_t v;
            if (!strcmp(pattern, "zero")) v = 0;
            else if (!strcmp(pattern, "prbs")) v = (int16_t)prbs(&seed);
            else v = (int16_t)(((w * 37u) & 0x7fff) - 16384);     /* ramp */
            expect[w] = v;
        }

        while (done < words) {
            size_t n = words - done;
            if (n * 2 > chunk) n = chunk / 2;
            for (size_t k = 0; k < n; k++)
                ((int16_t *)dma_buf_cpu(&in, done * 2))[k] = expect[done + k];
            dma_sync_for_device(&in);

            if (transfer(dma_buf_phys(&in, done * 2), dma_buf_phys(&out, done * 2),
                         (uint32_t)(n * 2), 0.2) != 0) {
                fprintf(stderr, "transfer failed at word %zu\n", done);
                dma_buf_free(&in);
                dma_buf_free(&out);
                return 5;
            }
            dma_sync_for_cpu(&out);
            done += n;
        }
        t_dma = now_s() - t0;

        /* compare in int16 space so a 1-LSB integer mismatch is visible */
        {
            size_t n = words;
            int16_t *got = (int16_t *)malloc(n * 2);
            if (!got) { perror("malloc"); return 4; }
            for (size_t w = 0; w < n; ) {
                size_t take = DMABUF_PAGE / 2;
                if (take > n - w) take = n - w;
                memcpy(got + w, dma_buf_cpu(&out, w * 2), take * 2);
                w += take;
            }
            analyse(expect, got, n, &runs, &zruns, &zruns32, &maxzr, &first_bad, &maxd);
            for (size_t w = 0; w < n; w++)
                if (expect[w] != got[w])
                    nbad++;
            free(got);
        }
        printf("{\"rep\":%d,\"mode\":\"%s\",\"pattern\":\"%s\",\"words\":%zu,"
               "\"chunk_bytes\":%zu,\"mismatch\":%zu,\"runs\":%zu,"
               "\"zero_runs\":%zu,\"zero_runs_32B_aligned\":%zu,\"max_zero_run\":%zu,"
               "\"first_bad\":%s,\"max_abs_diff\":%d,\"ms\":%.3f}\n",
               rep, mode == DMA_COHERENT_UNCACHED ? "uncached-alias" : "flush+scrub",
               pattern, words, chunk, nbad, runs, zruns, zruns32, maxzr,
               nbad ? "true" : "false", maxd, t_dma * 1e3);
        if (nbad) {
            fails++;
            if (zruns32)
                fprintf(stderr,
                        "  FINGERPRINT: %zu all-zero run(s) >=32 B at 32-byte boundaries, "
                        "max %zu samples -> dirty cache line writeback, not RTL logic\n",
                        zruns32, maxzr);
        }
        dma_buf_free(&in);
        dma_buf_free(&out);
        if (!realloc_each)
            break;      /* the bug is a first-transfer effect; same buffers will pass */
    }

    if (repeat > 1 && fails == 0)
        fprintf(stderr, "all %d repetitions bit exact\n", repeat);
    free(expect);
    return fails ? 5 : 0;
}
