#ifndef WORLD_FFT_IOCTL_H
#define WORLD_FFT_IOCTL_H
#include <linux/ioctl.h>
#include <linux/types.h>
// Fixed-width user addresses keep this ioctl identical on ARM32 and host64.
struct world_fft_request {
    __u64 input;
    __u64 output;
    __u32 n;
    __u32 forward; // bit0 forward; bit1 compact real input (forward only)
};
#define WORLD_FFT_PROCESS _IOWR('W', 0x32, struct world_fft_request)
#endif
