// stft_dma_mem.c - user-space AXI DMA driver for the PL STFT/gain/ISTFT core.
//
// One frame on the wire is 1537 32-bit words:
//     [1024 x int16 sample (sign-extended)] [513 x Q4.19 gain]
// and the core returns 1024 words, value = z * 256 with z in int16 units.
//
// Buffer strategy: three INDEPENDENT 4 KiB pages (samples, gains, output) and
// two back-to-back MM2S transfers per frame instead of one 6148-byte transfer.
// This removes any need for physically contiguous memory: after a day of
// uptime the board's buddy allocator hands out scattered order-0 pages, so a
// contiguous run is not something a userspace driver can rely on.  The core
// only counts words, so the gap between the two MM2S transfers is harmless.
//
// Build: arm-linux-gnueabihf-gcc -static -O2 -o stft_dma_mem stft_dma_mem.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#define DMA_BASE    0x40400000UL
#define GPIO_BASE   0x41200000UL
#define PAGE_SIZE   4096u
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

static volatile uint32_t *dma;
static volatile uint32_t *inp;
static volatile uint32_t *ginp;
static volatile uint32_t *outp;
static uint64_t in_phys, gin_phys, out_phys;

static inline uint32_t reg_rd(uint32_t off) { return *(volatile uint32_t *)((char *)dma + off); }
static inline void reg_wr(uint32_t off, uint32_t v) { *(volatile uint32_t *)((char *)dma + off) = v; }

static double now_s(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void *map_devmem(int fd, uint64_t phys, size_t len)
{
    void *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)phys);
    if (p == MAP_FAILED) {
        fprintf(stderr, "mmap /dev/mem phys=0x%" PRIx64 " failed: %s\n", phys, strerror(errno));
        exit(4);
    }
    return p;
}

static uint64_t page_phys(void *addr)
{
    int fd = open("/proc/self/pagemap", O_RDONLY);
    uint64_t entry = 0;
    if (fd < 0) { perror("open pagemap"); exit(4); }
    if (pread(fd, &entry, 8, (off_t)(((uintptr_t)addr / PAGE_SIZE) * 8)) != 8) {
        perror("pread pagemap"); exit(4);
    }
    close(fd);
    if (!(entry & (1ULL << 63))) {
        fprintf(stderr, "pagemap: page not present for %p\n", addr);
        exit(4);
    }
    return (entry & ((1ULL << 55) - 1)) * PAGE_SIZE;
}

static void dma_hw_reset(void)
{
    int i;
    reg_wr(R_MM2S_CR, CR_RESET);
    reg_wr(R_S2MM_CR, CR_RESET);
    for (i = 0; i < 10000; ++i) {
        if (!(reg_rd(R_MM2S_CR) & CR_RESET) && !(reg_rd(R_S2MM_CR) & CR_RESET)) break;
        usleep(10);
    }
    if (i == 10000) { fprintf(stderr, "DMA reset timeout\n"); exit(5); }
    reg_wr(R_MM2S_SR, 0x00007000u);
    reg_wr(R_S2MM_SR, 0x00007000u);
    reg_wr(R_MM2S_CR, CR_RS);
    reg_wr(R_S2MM_CR, CR_RS);
}

static int wait_mm2s(double budget)
{
    double start = now_s();
    for (;;) {
        uint32_t sr = reg_rd(R_MM2S_SR);
        if (sr & SR_ERR) { fprintf(stderr, "MM2S error SR=0x%08x\n", sr); return -1; }
        if (sr & SR_IDLE) { reg_wr(R_MM2S_SR, sr); return 0; }
        if (now_s() - start > budget) { fprintf(stderr, "MM2S timeout SR=0x%08x\n", sr); return -1; }
    }
}

static int wait_s2mm(double budget)
{
    double start = now_s();
    for (;;) {
        uint32_t sr = reg_rd(R_S2MM_SR);
        if (sr & SR_ERR) { fprintf(stderr, "S2MM error SR=0x%08x\n", sr); return -1; }
        if (sr & SR_IDLE) { reg_wr(R_S2MM_SR, sr); return 0; }
        if (now_s() - start > budget) { fprintf(stderr, "S2MM timeout SR=0x%08x\n", sr); return -1; }
    }
}

// samples (4096 B) then gains (2052 B) into the core, 4096 B back out
static int dma_frame(double budget)
{
    reg_wr(R_S2MM_CR, CR_RS);
    reg_wr(R_S2MM_DA, (uint32_t)out_phys);
    reg_wr(R_S2MM_LEN, NSAMP * 4u);

    reg_wr(R_MM2S_CR, CR_RS);
    reg_wr(R_MM2S_SA, (uint32_t)in_phys);
    reg_wr(R_MM2S_LEN, NSAMP * 4u);
    if (wait_mm2s(budget)) return -1;

    reg_wr(R_MM2S_CR, CR_RS);
    reg_wr(R_MM2S_SA, (uint32_t)gin_phys);
    reg_wr(R_MM2S_LEN, NBIN * 4u);
    if (wait_mm2s(budget)) return -1;
    if (wait_s2mm(budget)) return -1;
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s stim_x.bin stim_g.bin out_z.bin\n", argv[0]);
        return 2;
    }
    int memfd = open("/dev/mem", O_RDWR | O_SYNC);
    if (memfd < 0) { perror("open /dev/mem"); return 3; }
    dma = map_devmem(memfd, DMA_BASE, 0x10000);
    (void)map_devmem(memfd, GPIO_BASE, 0x1000);

    FILE *fx = fopen(argv[1], "rb");
    FILE *fg = fopen(argv[2], "rb");
    if (!fx || !fg) { perror("stim"); return 3; }
    FILE *fo = fopen(argv[3], "wb");
    if (!fo) { perror(argv[3]); return 3; }

    // three independent pages: no physical contiguity required
    unsigned char *p_s = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    unsigned char *p_g = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    unsigned char *p_o = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p_s == MAP_FAILED || p_g == MAP_FAILED || p_o == MAP_FAILED) { perror("mmap anon"); return 4; }
    memset(p_s, 0, PAGE_SIZE); memset(p_g, 0, PAGE_SIZE); memset(p_o, 0, PAGE_SIZE);
    in_phys  = page_phys(p_s);
    gin_phys = page_phys(p_g);
    out_phys = page_phys(p_o);
    fprintf(stderr, "phys samp=0x%" PRIx64 " gain=0x%" PRIx64 " out=0x%" PRIx64 "\n",
            in_phys, gin_phys, out_phys);
    if (syscall(__ARM_NR_cacheflush, p_s, p_s + PAGE_SIZE, 0) ||
        syscall(__ARM_NR_cacheflush, p_g, p_g + PAGE_SIZE, 0) ||
        syscall(__ARM_NR_cacheflush, p_o, p_o + PAGE_SIZE, 0)) {
        perror("cacheflush"); return 4;
    }
    inp  = (volatile uint32_t *)map_devmem(memfd, in_phys, PAGE_SIZE);
    ginp = (volatile uint32_t *)map_devmem(memfd, gin_phys, PAGE_SIZE);
    outp = (volatile uint32_t *)map_devmem(memfd, out_phys, PAGE_SIZE);

    // evict dirty L2 lines (see pl_build_20261025.md 5.4)
    size_t sweep = 2u * 1024u * 1024u;
    unsigned char *scrub = mmap(NULL, sweep, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (scrub != MAP_FAILED) { memset(scrub, 0x5a, sweep); usleep(20000); }

    dma_hw_reset();
    usleep(100);

    int16_t xs[NSAMP];
    int32_t gs[NBIN], zs[NSAMP];
    uint64_t frames = 0, errors = 0;
    double t0 = now_s(), t_dma = 0.0;
    for (;;) {
        size_t nx = fread(xs, 2, NSAMP, fx);
        size_t ng = fread(gs, 4, NBIN, fg);
        if (nx == 0 && ng == 0) break;
        if (nx != NSAMP || ng != NBIN) { fprintf(stderr, "short read at frame %" PRIu64 "\n", frames); break; }
        for (uint32_t i = 0; i < NSAMP; ++i) inp[i] = (uint32_t)(int32_t)xs[i];
        for (uint32_t i = 0; i < NBIN; ++i) ginp[i] = (uint32_t)gs[i];
        double d0 = now_s();
        if (dma_frame(0.5) != 0) { errors++; break; }
        t_dma += now_s() - d0;
        for (uint32_t i = 0; i < NSAMP; ++i) zs[i] = (int32_t)outp[i];
        if (fwrite(zs, 4, NSAMP, fo) != NSAMP) { perror("fwrite"); return 6; }
        frames++;
    }
    double total = now_s() - t0;
    fflush(fo); fclose(fx); fclose(fg); fclose(fo);
    fprintf(stderr, "frames=%" PRIu64 " errors=%" PRIu64 "\n", frames, errors);
    fprintf(stderr, "total_s=%.6f dma_s=%.6f frames_per_s=%.1f\n",
            total, t_dma, total > 0 ? (double)frames / total : 0.0);
    return errors ? 5 : 0;
}
