#ifndef WORLD_EXP_IOCTL_H
#define WORLD_EXP_IOCTL_H
#ifdef __linux__
#include <linux/ioctl.h>
#include <linux/types.h>
#else
#include <stdint.h>
typedef uint64_t __u64;
#endif
#define WORLD_EXP_BINS 513
struct world_exp_packet { __u64 input[WORLD_EXP_BINS]; __u64 output[WORLD_EXP_BINS]; };
#define WORLD_EXP_PROCESS _IOWR('W', 0x31, struct world_exp_packet)
#endif
