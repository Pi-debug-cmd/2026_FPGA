// ARM32 stream; optional fourth argument configures ratio and resets v2 DSP.
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include "../kernel/pitch_dma_ioctl.h"

int main(int argc, char **argv)
{
    int fd;
    int32_t samples[PITCH_DMA_MAX_FRAMES];
    uint32_t native[2 * PITCH_DMA_MAX_FRAMES];
    unsigned long frames = 256;
    uint64_t total = 0, input_energy = 0, output_energy = 0;
    int32_t input_peak = 0, output_peak = 0;
    size_t bytes;
    char *end;
    int native_mode = argc >= 3 && !strcmp(argv[2], "native_s24");
    unsigned long ratio = 0;
    if (argc > 4 || (argc >= 3 && !native_mode && strcmp(argv[2], "pcm32"))) return 2;
    if (argc >= 2) {
        errno = 0;
        frames = strtoul(argv[1], &end, 10);
        if (errno || *end || !frames || frames > PITCH_DMA_MAX_FRAMES) return 2;
    }
    if (argc == 4) {
        errno = 0;
        ratio = strtoul(argv[3], &end, 10);
        if (errno || end == argv[3] || *end || ratio < 32768 || ratio > 131072) return 2;
    }
    if (sizeof(uintptr_t) != 4) {
        fprintf(stderr, "ARM32 userspace ABI required\n");
        return 2;
    }
    fd = open("/dev/pitch_dma", O_RDWR | O_CLOEXEC);
    if (fd < 0) { perror("open pitch_dma"); return 3; }
    if (ratio) {
        struct pitch_dma_config config = { (uint32_t)ratio, 0 };
        if (ioctl(fd, PITCH_DMA_CONFIGURE, &config) < 0) {
            perror("pitch DMA configure"); close(fd); return 5;
        }
    }
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    while ((bytes = fread(native_mode ? (void *)native : (void *)samples,
                         1, frames * (native_mode ? 8u : 4u), stdin)) != 0) {
        size_t i, count = bytes / (native_mode ? 8u : 4u);
        struct pitch_dma_request request;
        if (bytes % (native_mode ? 8u : 4u)) { close(fd); return 4; }
        if (native_mode) {
            for (i = 0; i < count; ++i) {
                uint32_t word = native[2u * i] & 0xffffffu;
                int32_t signed24 = (int32_t)(word ^ 0x800000u) - 0x800000;
                samples[i] = signed24 >= 0 ? signed24 / 256 : -((-signed24 + 255) / 256);
            }
        }
        for (i = 0; i < count; ++i) {
            if (samples[i] < -32768 || samples[i] > 32767) { close(fd); return 4; }
            int32_t magnitude = samples[i] < 0 ? -samples[i] : samples[i];
            if (magnitude > input_peak) input_peak = magnitude;
            input_energy += (uint64_t)((int64_t)samples[i] * samples[i]);
        }
        request.frames = (uint32_t)count;
        request.samples_user_address = (uint32_t)(uintptr_t)samples;
        if (ioctl(fd, PITCH_DMA_PROCESS, &request) < 0) {
            perror("pitch DMA transfer"); close(fd); return 5;
        }
        for (i = 0; i < count; ++i) {
            if (samples[i] < -32768 || samples[i] > 32767) { close(fd); return 6; }
            int32_t magnitude = samples[i] < 0 ? -samples[i] : samples[i];
            if (magnitude > output_peak) output_peak = magnitude;
            output_energy += (uint64_t)((int64_t)samples[i] * samples[i]);
            if (native_mode) {
                uint32_t packed = (uint32_t)(samples[i] * 256) & 0xffffffu;
                native[2u * i] = native[2u * i + 1u] = packed;
            }
        }
        total += count;
        if (fwrite(native_mode ? (void *)native : (void *)samples, 1, bytes, stdout) != bytes) {
            close(fd); return 6;
        }
    }
    close(fd);
    fprintf(stderr, "frames=%" PRIu64 " input_peak=%d output_peak=%d input_mean_square=%.3f output_mean_square=%.3f\n",
            total, input_peak, output_peak, total ? (double)input_energy / total : 0,
            total ? (double)output_energy / total : 0);
    return ferror(stdin) || fflush(stdout) ? 6 : 0;
}
