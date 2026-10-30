#ifndef WORLD_MINPHASE_IOCTL_H
#define WORLD_MINPHASE_IOCTL_H
#ifdef __linux__
#include <linux/ioctl.h>
#else
#include <sys/ioctl.h>
#endif

#define WORLD_MINPHASE_BINS 513
struct world_minphase_packet {
    float input[WORLD_MINPHASE_BINS];
    float output_re[WORLD_MINPHASE_BINS];
    float output_im[WORLD_MINPHASE_BINS];
};
#define WORLD_MINPHASE_PROCESS _IOWR('W', 0x33, struct world_minphase_packet)
#endif
