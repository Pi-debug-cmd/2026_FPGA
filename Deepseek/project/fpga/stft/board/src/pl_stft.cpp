// pl_stft.cpp - user-space driver for the PL STFT/gain/ISTFT core.
//
// One frame on the wire: 1537 32-bit words = 1024 sign-extended int16 samples
// followed by 513 Q4.19 gains.  The core returns 1024 words, z * 256.
// Per-frame AXI DMA simple-mode transfers out of a 12 KiB buffer whose three
// pages are checked for physical contiguity, so no kernel module is needed.
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "pl_stft.h"

#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>

#define DMA_BASE    0x40400000UL
#define GPIO_BASE   0x41200000UL
#define PAGE_SIZE   4096u
#define FRAME_WORDS 1537u
#define NSAMP       1024u
#define NBIN        513u

#define R_MM2S_CR    0x00u
#define R_MM2S_SR    0x04u
#define R_MM2S_SA    0x18u
#define R_MM2S_LEN   0x28u
#define R_S2MM_CR    0x30u
#define R_S2MM_SR    0x34u
#define R_S2MM_DA    0x48u
#define R_S2MM_LEN   0x58u

#define CR_RS      0x00000001u
#define CR_RESET   0x00000004u
#define SR_IDLE    0x00000002u
#define SR_ERR     0x00000070u

#ifndef __ARM_NR_cacheflush
#define __ARM_NR_cacheflush 0x0f0002
#endif

static volatile uint32_t *g_dma = nullptr;
static volatile uint32_t *g_in = nullptr;
static volatile uint32_t *g_out = nullptr;
static uint64_t g_in_phys = 0, g_out_phys = 0;
static int g_memfd = -1;
static double g_last_s = 0.0;

static inline uint32_t rd(uint32_t off) { return *(volatile uint32_t *)((char *)g_dma + off); }
static inline void wr(uint32_t off, uint32_t v) { *(volatile uint32_t *)((char *)g_dma + off) = v; }

static double now_s()
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void *map_mem(uint64_t phys, size_t len)
{
    void *p = mmap(nullptr, len, PROT_READ | PROT_WRITE, MAP_SHARED, g_memfd, (off_t)phys);
    if (p == MAP_FAILED) {
        fprintf(stderr, "pl_stft: mmap 0x%llx failed: %s\n",
                (unsigned long long)phys, strerror(errno));
        return nullptr;
    }
    return p;
}

static uint64_t page_phys(void *addr)
{
    int fd = open("/proc/self/pagemap", O_RDONLY);
    uint64_t e = 0;
    if (fd < 0) return 0;
    if (pread(fd, &e, 8, (off_t)(((uintptr_t)addr / PAGE_SIZE) * 8)) != 8) { close(fd); return 0; }
    close(fd);
    if (!(e & (1ULL << 63))) return 0;
    return (e & ((1ULL << 55) - 1)) * PAGE_SIZE;
}

static void dma_reset()
{
    wr(R_MM2S_CR, CR_RESET);
    wr(R_S2MM_CR, CR_RESET);
    for (int i = 0; i < 10000; ++i) {
        if (!(rd(R_MM2S_CR) & CR_RESET) && !(rd(R_S2MM_CR) & CR_RESET)) break;
        usleep(10);
    }
    wr(R_MM2S_SR, 0x00007000u);
    wr(R_S2MM_SR, 0x00007000u);
    wr(R_MM2S_CR, CR_RS);
    wr(R_S2MM_CR, CR_RS);
}

int pl_stft_init()
{
    static int state = -1;
    if (state >= 0) return state;
    state = 0;

    g_memfd = open("/dev/mem", O_RDWR | O_SYNC);
    if (g_memfd < 0) { perror("pl_stft: open /dev/mem"); return 0; }
    void *d = map_mem(DMA_BASE, 0x10000);
    if (!d) return 0;
    g_dma = (volatile uint32_t *)d;
    void *gp = map_mem(GPIO_BASE, 0x1000);
    if (!gp) return 0;
    (void)gp;

    // three physically contiguous pages: frame in at +0, frame out at +2 pages
    unsigned char *anon = (unsigned char *)MAP_FAILED;
    uint64_t p0 = 0, p1 = 0, p2 = 0;
    int attempt;
    for (attempt = 0; attempt < 200; ++attempt) {
        anon = (unsigned char *)mmap(nullptr, 3 * PAGE_SIZE, PROT_READ | PROT_WRITE,
                                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (anon == MAP_FAILED) { perror("pl_stft: mmap anon"); return 0; }
        memset(anon, 0, 3 * PAGE_SIZE);
        mlock(anon, 3 * PAGE_SIZE);
        p0 = page_phys(anon);
        p1 = page_phys(anon + PAGE_SIZE);
        p2 = page_phys(anon + 2 * PAGE_SIZE);
        if (p0 && p1 == p0 + PAGE_SIZE && p2 == p1 + PAGE_SIZE) break;
        munmap(anon, 3 * PAGE_SIZE);
        anon = (unsigned char *)MAP_FAILED;
    }
    if (anon == (unsigned char *)MAP_FAILED || attempt >= 200) {
        fprintf(stderr, "pl_stft: no 3 physically contiguous pages\n");
        return 0;
    }
    if (syscall(__ARM_NR_cacheflush, anon, anon + 3 * PAGE_SIZE, 0) != 0) {
        perror("pl_stft: cacheflush");
        return 0;
    }
    g_in_phys = p0;
    g_out_phys = p2;
    g_in = (volatile uint32_t *)map_mem(p0, 2 * PAGE_SIZE);
    g_out = (volatile uint32_t *)map_mem(p2, PAGE_SIZE);
    if (!g_in || !g_out) return 0;

    // evict dirty L2 lines before the first DMA (see pl_build_20261025.md 5.4)
    size_t sweep = 2u * 1024u * 1024u;
    unsigned char *scrub = (unsigned char *)mmap(nullptr, sweep, PROT_READ | PROT_WRITE,
                                                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (scrub != MAP_FAILED) {
        memset(scrub, 0x5a, sweep);
        usleep(20000);
        munmap(scrub, sweep);
    }

    dma_reset();
    usleep(100);
    state = 1;
    return 1;
}

int pl_stft_run(const int16_t *x, const int32_t *g, int frames, int32_t *z)
{
    if (!pl_stft_init()) return -1;
    double t0 = now_s();
    for (int f = 0; f < frames; ++f) {
        const int16_t *xf = x + (size_t)f * NSAMP;
        const int32_t *gf = g + (size_t)f * NBIN;
        int32_t *zf = z + (size_t)f * NSAMP;
        for (uint32_t i = 0; i < NSAMP; ++i) g_in[i] = (uint32_t)(int32_t)xf[i];
        for (uint32_t i = 0; i < NBIN; ++i) g_in[NSAMP + i] = (uint32_t)gf[i];

        wr(R_S2MM_CR, CR_RS);
        wr(R_S2MM_DA, (uint32_t)g_out_phys);
        wr(R_S2MM_LEN, NSAMP * 4u);
        wr(R_MM2S_CR, CR_RS);
        wr(R_MM2S_SA, (uint32_t)g_in_phys);
        wr(R_MM2S_LEN, FRAME_WORDS * 4u);
        double start = now_s();
        for (;;) {
            uint32_t mm = rd(R_MM2S_SR), sm = rd(R_S2MM_SR);
            if (mm & SR_ERR) { fprintf(stderr, "pl_stft: MM2S err 0x%08x\n", mm); return -2; }
            if (sm & SR_ERR) { fprintf(stderr, "pl_stft: S2MM err 0x%08x\n", sm); return -2; }
            if ((mm & SR_IDLE) && (sm & SR_IDLE)) break;
            if (now_s() - start > 0.5) {
                fprintf(stderr, "pl_stft: DMA timeout frame %d MM2S=0x%08x S2MM=0x%08x\n",
                        f, mm, sm);
                return -3;
            }
        }
        wr(R_MM2S_SR, rd(R_MM2S_SR));
        wr(R_S2MM_SR, rd(R_S2MM_SR));
        for (uint32_t i = 0; i < NSAMP; ++i) zf[i] = (int32_t)g_out[i];
    }
    g_last_s = now_s() - t0;
    return 0;
}

double pl_stft_last_seconds() { return g_last_s; }


