/* dmabuf.c - see dmabuf.h for the why. Build:
 *   arm-linux-gnueabihf-gcc -static -O2 -o dma_roundtrip dma_roundtrip.c dmabuf.c
 */
#define _GNU_SOURCE
#include "dmabuf.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>

#ifndef __ARM_NR_cacheflush
#define __ARM_NR_cacheflush 0x0f0002
#endif

/* 2 MiB = 4 x PL310 L2 on this part; enough to flush the whole L2 by eviction. */
#define L2_SWEEP_BYTES (2u * 1024u * 1024u)

static int map_devmem(int fd, uint64_t phys, size_t len, void **out)
{
    void *p = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)phys);
    if (p == MAP_FAILED) {
        fprintf(stderr, "dmabuf: mmap /dev/mem phys=0x%llx len=%zu failed: %s\n",
                (unsigned long long)phys, len, strerror(errno));
        return -1;
    }
    *out = p;
    return 0;
}

static int page_phys(void *addr, uint64_t *out)
{
    int fd = open("/proc/self/pagemap", O_RDONLY);
    uint64_t entry = 0;
    off_t off = (off_t)(((uintptr_t)addr / DMABUF_PAGE) * 8);
    if (fd < 0) {
        fprintf(stderr, "dmabuf: open /proc/self/pagemap failed: %s "
                        "(need root, and CONFIG_PROC_PAGE_MONITOR)\n", strerror(errno));
        return -1;
    }
    if (pread(fd, &entry, 8, off) != 8) {
        fprintf(stderr, "dmabuf: pread pagemap failed: %s\n", strerror(errno));
        close(fd);
        return -1;
    }
    close(fd);
    if (!(entry & (1ULL << 63))) {
        fprintf(stderr, "dmabuf: page not present for %p (not faulted in?)\n", addr);
        return -1;
    }
    if (!(entry & (1ULL << 55))) {   /* soft-dirty is bit 55; PFN is 0..54 */
        /* no-op, kept for readers of the bit layout */
    }
    *out = (entry & ((1ULL << 55) - 1)) * DMABUF_PAGE;
    return 0;
}

int dma_cacheflush_range(void *addr, size_t bytes)
{
    /* ARM private cacheflush(addr, addr+bytes, flags): flags=0 -> data+unified.
     * Cleans and invalidates the *L1* D-cache for the range.  It does NOT touch
     * the PL310 L2 -- see dma_l2_scrub(). */
    return (int)syscall(__ARM_NR_cacheflush, (char *)addr, (char *)addr + bytes, 0);
}

int dma_l2_scrub(size_t sweep_bytes)
{
    /* Dirty lines already in L2 are written back only when evicted.  Touching a
     * buffer several times the L2 size forces those writebacks to happen NOW,
     * before the DMA engine starts, instead of racing it later.
     *
     * Volatile stores are used on purpose: the compiler must not remove the
     * sweep, and each store must actually reach the cache. */
    size_t i;
    volatile unsigned char *p = (volatile unsigned char *)mmap(
        NULL, sweep_bytes, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) {
        fprintf(stderr, "dmabuf: scrub mmap failed: %s\n", strerror(errno));
        return -1;
    }
    for (i = 0; i < sweep_bytes; i += 32)
        p[i] = (unsigned char)(0x5a ^ (i & 0xff));
    __sync_synchronize();
    usleep(20000);             /* let the writebacks drain before DMA starts */
    munmap((void *)p, sweep_bytes);
    return 0;
}

int dma_buf_alloc(dma_buf *b, size_t bytes, dma_coherent_mode mode)
{
    size_t i;
    memset(b, 0, sizeof(*b));
    b->mode = mode;
    b->memfd = -1;
    if (bytes == 0 || bytes > DMABUF_MAX_PAGES * DMABUF_PAGE) {
        fprintf(stderr, "dmabuf: bad size %zu (max %u)\n", bytes,
                (unsigned)(DMABUF_MAX_PAGES * DMABUF_PAGE));
        return -1;
    }
    b->bytes = (bytes + DMABUF_PAGE - 1) & ~(size_t)(DMABUF_PAGE - 1);
    b->pages = b->bytes / DMABUF_PAGE;

    b->anon = mmap(NULL, b->bytes, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (b->anon == MAP_FAILED) {
        fprintf(stderr, "dmabuf: anon mmap failed: %s\n", strerror(errno));
        return -1;
    }
    /* populate the pages now: pagemap cannot report a PFN for an unfaulted page */
    memset(b->anon, 0, b->bytes);
    if (mlock(b->anon, b->bytes) == 0)
        b->locked = 1;

    for (i = 0; i < b->pages; i++) {
        if (page_phys((char *)b->anon + i * DMABUF_PAGE, &b->phys[i]) != 0)
            goto fail;
    }

    if (mode == DMA_COHERENT_UNCACHED) {
        b->memfd = open("/dev/mem", O_RDWR | O_SYNC);
        if (b->memfd < 0) {
            fprintf(stderr, "dmabuf: open /dev/mem failed: %s "
                            "(fall back to DMA_COHERENT_FLUSH at your own risk)\n",
                    strerror(errno));
            goto fail;
        }
        for (i = 0; i < b->pages; i++) {
            if (map_devmem(b->memfd, b->phys[i], DMABUF_PAGE, &b->page[i]) != 0)
                goto fail;
        }
        /* Aliasing the same DRAM twice leaves stale lines in L1/L2 from the
         * memset above; they can be written back over DMA data later.  Clean them
         * and force the L2 writebacks before the first transfer. */
        (void)dma_cacheflush_range(b->anon, b->bytes);
        (void)dma_l2_scrub(L2_SWEEP_BYTES);
    } else {
        for (i = 0; i < b->pages; i++)
            b->page[i] = (char *)b->anon + i * DMABUF_PAGE;
    }
    return 0;

fail:
    dma_buf_free(b);
    return -1;
}

void dma_buf_free(dma_buf *b)
{
    size_t i;
    if (b->mode == DMA_COHERENT_UNCACHED && b->memfd >= 0) {
        for (i = 0; i < b->pages; i++) {
            if (b->page[i])
                munmap(b->page[i], DMABUF_PAGE);
        }
        close(b->memfd);
        b->memfd = -1;
    }
    if (b->anon && b->anon != MAP_FAILED)
        munmap(b->anon, b->bytes);
    memset(b, 0, sizeof(*b));
    b->memfd = -1;
}

void *dma_buf_cpu(const dma_buf *b, size_t off)
{
    size_t p = off / DMABUF_PAGE;
    if (p >= b->pages)
        return NULL;
    if (b->mode == DMA_COHERENT_FLUSH)
        return (char *)b->page[0] + off;   /* cached mapping is contiguous */
    return (char *)b->page[p] + (off % DMABUF_PAGE);
}

uint64_t dma_buf_phys(const dma_buf *b, size_t off)
{
    size_t p = off / DMABUF_PAGE;
    if (p >= b->pages)
        return 0;
    return b->phys[p] + (off % DMABUF_PAGE);
}

void dma_sync_for_device(dma_buf *b)
{
    if (b->mode == DMA_COHERENT_UNCACHED) {
        __sync_synchronize();          /* stores are already in DRAM via the alias */
        return;
    }
    (void)dma_cacheflush_range(b->anon, b->bytes);
    (void)dma_l2_scrub(L2_SWEEP_BYTES);
    __sync_synchronize();
}

void dma_sync_for_cpu(dma_buf *b)
{
    if (b->mode == DMA_COHERENT_UNCACHED) {
        __sync_synchronize();
        return;
    }
    /* clean+invalidate so the CPU re-reads whatever the DMA engine wrote */
    (void)dma_cacheflush_range(b->anon, b->bytes);
    __sync_synchronize();
}

int dma_describe(FILE *f, const dma_buf *b)
{
    return fprintf(f,
                   "{\"mode\":\"%s\",\"bytes\":%zu,\"pages\":%zu,"
                   "\"phys0\":\"0x%llx\",\"locked\":%d}",
                   b->mode == DMA_COHERENT_UNCACHED ? "uncached-alias" : "flush+scrub",
                   b->bytes, b->pages, (unsigned long long)b->phys[0], b->locked);
}
