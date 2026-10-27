// pitch_dma_mem.c - user-space AXI DMA driver for the PL pitch core (no kernel module).
//
// M3 path: PCM16 mono -> sign-extended int32 words -> AXI DMA MM2S -> axis_pitch_shift
//          -> AXI DMA S2MM -> int16 words.  Simple mode, 1024 words (4 KiB) per transfer.
//
// Buffers are two anonymous pages whose PFNs are read from /proc/self/pagemap and
// aliased through /dev/mem, so the CPU only ever touches them uncached and the DMA
// sees DRAM.  The one-time dirty cache lines from page population are flushed with
// the ARM private cacheflush syscall before the first transfer.
//
// Build (host, Vivado 2018.3 SDK):
//   arm-linux-gnueabihf-gcc -static -O2 -o pitch_dma_mem pitch_dma_mem.c
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

#define DMA_BASE   0x40400000UL
#define GPIO_BASE  0x41200000UL
#define PAGE_SIZE  4096u
#define CHUNK_WORDS 1024u           /* 4 KiB per AXI DMA simple transfer */

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
#define SR_HALTED  0x00000001u
#define SR_IDLE    0x00000002u
#define SR_ERR     0x00000070u

#ifndef __ARM_NR_cacheflush
#define __ARM_NR_cacheflush 0x0f0002
#endif

static volatile uint32_t *dma;
static volatile uint32_t *gpio;

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
    off_t off = (off_t)(((uintptr_t)addr / PAGE_SIZE) * 8);
    if (fd < 0) { perror("open pagemap"); exit(4); }
    if (pread(fd, &entry, 8, off) != 8) { perror("pread pagemap"); exit(4); }
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
        if (!(reg_rd(R_MM2S_CR) & CR_RESET) && !(reg_rd(R_S2MM_CR) & CR_RESET))
            break;
        usleep(10);
    }
    if (i == 10000) { fprintf(stderr, "DMA reset timeout\n"); exit(5); }
    /* write-1-to-clear the sticky status bits */
    reg_wr(R_MM2S_SR, 0x00007000u);
    reg_wr(R_S2MM_SR, 0x00007000u);
    reg_wr(R_MM2S_CR, CR_RS);
    reg_wr(R_S2MM_CR, CR_RS);
}

static int dma_transfer(uint64_t in_phys, uint64_t out_phys, uint32_t bytes, double budget_s)
{
    double start = now_s();
    uint32_t mm, sm;
    reg_wr(R_S2MM_CR, CR_RS);
    reg_wr(R_S2MM_DA, (uint32_t)out_phys);
    reg_wr(R_S2MM_LEN, bytes);
    reg_wr(R_MM2S_CR, CR_RS);
    reg_wr(R_MM2S_SA, (uint32_t)in_phys);
    reg_wr(R_MM2S_LEN, bytes);
    for (;;) {
        mm = reg_rd(R_MM2S_SR);
        sm = reg_rd(R_S2MM_SR);
        if (mm & SR_ERR) { fprintf(stderr, "MM2S error SR=0x%08x\n", mm); return -1; }
        if (sm & SR_ERR) { fprintf(stderr, "S2MM error SR=0x%08x\n", sm); return -1; }
        if ((mm & SR_IDLE) && (sm & SR_IDLE))
            break;
        if (now_s() - start > budget_s) {
            fprintf(stderr, "DMA timeout MM2S_SR=0x%08x S2MM_SR=0x%08x\n", mm, sm);
            return -1;
        }
    }
    reg_wr(R_MM2S_SR, mm);
    reg_wr(R_S2MM_SR, sm);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 4 || argc > 5) {
        fprintf(stderr, "usage: %s input output ratio_q16 [s24]\n", argv[0]);
        return 2;
    }
    int s24_mode = argc == 5 && !strcmp(argv[4], "s24");
    long ratio = strtol(argv[3], NULL, 0);
    if (ratio < 32768 || ratio > 131072) { fprintf(stderr, "ratio out of range\n"); return 2; }

    int memfd = open("/dev/mem", O_RDWR | O_SYNC);
    if (memfd < 0) { perror("open /dev/mem"); return 3; }
    dma = map_devmem(memfd, DMA_BASE, 0x10000);
    gpio = map_devmem(memfd, GPIO_BASE, 0x1000);

    FILE *in = fopen(argv[1], "rb");
    if (!in) { perror(argv[1]); return 3; }
    FILE *out = fopen(argv[2], "wb");
    if (!out) { perror(argv[2]); return 3; }

    /* two pages: in (CPU-written), out (DMA-written) */
    unsigned char *anon = mmap(NULL, 2 * PAGE_SIZE, PROT_READ | PROT_WRITE,
                               MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (anon == MAP_FAILED) { perror("mmap anon"); return 4; }
    memset(anon, 0, 2 * PAGE_SIZE);
    if (mlock(anon, 2 * PAGE_SIZE) != 0) { perror("mlock"); return 4; }
    uint64_t in_phys = page_phys(anon);
    uint64_t out_phys = page_phys(anon + PAGE_SIZE);
    if (syscall(__ARM_NR_cacheflush, anon, anon + 2 * PAGE_SIZE, 0) != 0) {
        perror("cacheflush");
        fprintf(stderr, "cannot guarantee buffer coherency\n");
        return 4;
    }
    volatile uint32_t *in_alias = map_devmem(memfd, in_phys, PAGE_SIZE);
    volatile uint32_t *out_alias = map_devmem(memfd, out_phys, PAGE_SIZE);

    /* The ARM cacheflush syscall only cleans L1; dirty zero lines can still sit
     * in the PL310 L2 and be written back over DMA data minutes later (observed
     * as 32-byte zero runs).  Sweep 2 MiB (4x L2) so those lines are evicted to
     * DRAM before the first transfer, then wait for the writebacks to drain. */
    size_t sweep = 2u * 1024u * 1024u;
    unsigned char *scrub = mmap(NULL, sweep, PROT_READ | PROT_WRITE,
                                MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (scrub == MAP_FAILED) { perror("mmap scrub"); return 4; }
    memset(scrub, 0x5a, sweep);
    usleep(20000);

    dma_hw_reset();
    gpio[0] = (uint32_t)ratio;   /* ch1 = ratio_q16 */
    gpio[2] = 1;                 /* ch2 = DSP_RUN (scratch in this build) */
    usleep(100);

    double t0 = now_s();
    uint64_t words = 0, errors = 0;
    double min_chunk = 1e9, max_chunk = 0.0;
    int16_t buf[CHUNK_WORDS];
    unsigned char frames24[CHUNK_WORDS * 8];
    size_t got;
    for (;;) {
        uint32_t n, i;
        if (s24_mode) {
            got = fread(frames24, 8, CHUNK_WORDS, in);
            n = (uint32_t)got;
            for (i = 0; i < n; ++i) {
                uint32_t w = (uint32_t)frames24[8 * i] |
                             ((uint32_t)frames24[8 * i + 1] << 8) |
                             ((uint32_t)frames24[8 * i + 2] << 16);
                int32_t v = (int32_t)(w ^ 0x800000u) - 0x800000;
                buf[i] = (int16_t)(v >= 0 ? v / 256 : -((-v + 255) / 256));
            }
        } else {
            got = fread(buf, 2, CHUNK_WORDS, in);
            n = (uint32_t)got;
        }
        if (n == 0)
            break;
        for (i = 0; i < n; ++i)
            in_alias[i] = (uint32_t)(int32_t)buf[i];
        double c0 = now_s();
        if (dma_transfer(in_phys, out_phys, n * 4u, 0.05) != 0) { errors++; break; }
        double dt = now_s() - c0;
        if (dt < min_chunk) min_chunk = dt;
        if (dt > max_chunk) max_chunk = dt;
        for (i = 0; i < n; ++i) {
            int16_t s = (int16_t)(out_alias[i] & 0xffffu);
            buf[i] = s;
        }
        if (fwrite(buf, 2, n, out) != n) { perror("fwrite"); return 6; }
        words += n;
    }
    double total = now_s() - t0;
    fflush(out);
    fclose(in);
    fclose(out);
    fprintf(stderr, "words=%" PRIu64 " chunks=%" PRIu64 " errors=%" PRIu64 "\n",
            words, (words + CHUNK_WORDS - 1) / CHUNK_WORDS, errors);
    fprintf(stderr, "ratio_q16=%ld gpio_readback=0x%08x\n", ratio, gpio[0]);
    fprintf(stderr, "total_s=%.6f samples_per_s=%.1f min_chunk_us=%.1f max_chunk_us=%.1f avg_chunk_us=%.1f\n",
            total, total > 0 ? (double)words / total : 0.0,
            min_chunk * 1e6, max_chunk * 1e6,
            words ? total * 1e6 / (double)((words + CHUNK_WORDS - 1) / CHUNK_WORDS) : 0.0);
    fprintf(stderr, "in_phys=0x%" PRIx64 " out_phys=0x%" PRIx64 "\n", in_phys, out_phys);
    return errors ? 5 : 0;
}
