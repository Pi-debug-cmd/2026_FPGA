/* dmabuf.h - DMA-coherent buffers for user space on 32-bit ARM (Zynq-7000 A9).
 *
 * The problem this solves
 * -----------------------
 * On Cortex-A9 with the PL310 L2, a user-space buffer that the CPU has touched is
 * NOT coherent with a DMA master.  Two failure modes we hit in practice:
 *
 *   (a) DMA reads stale DRAM because the CPU's stores are still in L1/L2.
 *   (b) DMA writes land in DRAM, then a dirty line is written back over them
 *       minutes later  ->  the DMA output silently reverts to zeros for exactly
 *       one cache line (32 B = 8 16-bit samples on A9).
 *
 * The ARM private `cacheflush` syscall only cleans L1; it does not touch the
 * PL310 L2.  That is why "I did cacheflush()" is not a fix.
 *
 * The strategy here
 * -----------------
 * Primary: allocate anonymous pages, resolve their physical addresses through
 * /proc/self/pagemap, and give the CPU an *uncached alias* of the same DRAM
 * through /dev/mem (O_SYNC + MAP_SHARED).  The CPU only ever touches the alias,
 * so there is nothing to flush and no writeback can race the DMA.  This is the
 * only scheme that survived our test without timing assumptions.
 *
 * Secondary (DMA_COHERENT_FLUSH): cached buffer + explicit sync + an L2 scrub
 * sweep.  Kept because some kernels forbid /dev/mem; it is correct only if the
 * scrub really evicts enough of L2, so it is *documented as best-effort*.
 *
 * Constraints (enforced at runtime, not assumed)
 * ----------------------------------------------
 *  - one DMA chunk must not cross a 4 KiB page (chunk <= page, 4-byte aligned)
 *  - the process needs read access to /proc/self/pagemap (root on PetaLinux)
 *  - /dev/mem must exist and allow mapping the resolved physical pages
 *  - 32-bit physical addresses (Zynq-7000 has <= 1 GB DDR)
 */
#ifndef DMABUF_H
#define DMABUF_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#define DMABUF_MAX_PAGES 64
#define DMABUF_PAGE 4096u

typedef enum {
    DMA_COHERENT_UNCACHED = 0, /* default, recommended */
    DMA_COHERENT_FLUSH = 1     /* cached + sync + L2 scrub, best-effort */
} dma_coherent_mode;

typedef struct {
    dma_coherent_mode mode;
    size_t bytes;                 /* rounded up to whole pages */
    size_t pages;
    void *anon;                   /* original (cached) mapping              */
    void *page[DMABUF_MAX_PAGES]; /* per-page CPU view (alias or anon+off)  */
    uint64_t phys[DMABUF_MAX_PAGES];
    int memfd;
    int locked;
} dma_buf;

/* Returns 0 on success, negative errno-ish code on failure; on failure the
 * reason is printed to stderr with the exact syscall that failed. */
int dma_buf_alloc(dma_buf *b, size_t bytes, dma_coherent_mode mode);
void dma_buf_free(dma_buf *b);

/* CPU pointer / DMA address for an offset inside the buffer.
 * The returned pointer is valid for [off, page_boundary(off)). */
void *dma_buf_cpu(const dma_buf *b, size_t off);
uint64_t dma_buf_phys(const dma_buf *b, size_t off);

/* Ownership transfers.  For UNCACHED these are barriers only; for FLUSH they do
 * clean/invalidate plus an L2 scrub sweep.  Call sync_for_device after the CPU
 * wrote the buffer, sync_for_cpu after the DMA engine signalled completion. */
void dma_sync_for_device(dma_buf *b);
void dma_sync_for_cpu(dma_buf *b);

/* Diagnostics used by dma_roundtrip.c and by the on-board checklist. */
int dma_cacheflush_range(void *addr, size_t bytes);  /* ARM __NR_cacheflush     */
int dma_l2_scrub(size_t sweep_bytes);                /* evict dirty L2 lines    */
int dma_describe(FILE *f, const dma_buf *b);         /* JSON one-liner          */

#endif /* DMABUF_H */
