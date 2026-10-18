#ifndef PITCH_DMA_IOCTL_H
#define PITCH_DMA_IOCTL_H
#include <linux/ioctl.h>
#include <linux/types.h>

/* ARM32 userspace address; samples are signed PCM16 extended into int32 words. */
struct pitch_dma_request {
    __u32 frames;
    __u32 samples_user_address;
};
#define PITCH_DMA_MAX_FRAMES 4096
#define PITCH_DMA_PROCESS _IOWR('P', 1, struct pitch_dma_request)
/* Reset RAM/phase and apply ratio while no block is in flight (v2 hardware). */
struct pitch_dma_config {
    __u32 ratio_q16;
    __u32 reserved;
};
#define PITCH_DMA_CONFIGURE _IOW('P', 2, struct pitch_dma_config)
#endif
