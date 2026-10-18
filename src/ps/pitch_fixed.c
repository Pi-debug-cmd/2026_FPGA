/* PS-only PCM16 reference with the exact RTL arithmetic contract. */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define Q 65536u
#define PHASE_MASK (1024u * Q - 1u)
#define DEPTH 2048u

static int16_t memory[DEPTH];
static uint32_t write_index, phase;

static int16_t floor_q16(int64_t value)
{
    return (int16_t)(value >= 0 ? value / Q : -((-value + Q - 1u) / Q));
}

static int16_t tap(uint32_t tap_phase)
{
    uint32_t recent = (write_index - 2u - (tap_phase >> 16)) & (DEPTH - 1u);
    uint32_t fraction = tap_phase & (Q - 1u);
    return floor_q16((int64_t)memory[recent] * (Q - fraction)
                     + (int64_t)memory[(recent - 1u) & (DEPTH - 1u)] * fraction);
}

static int16_t process_sample(int16_t input, uint32_t ratio)
{
    int16_t output;
    memory[write_index] = input;
    if (ratio == Q) {
        output = input;
    } else {
        uint32_t weight = phase < 512u * Q ? phase >> 9 : 2u * Q - (phase >> 9);
        output = floor_q16((int64_t)tap(phase) * weight
                          + (int64_t)tap(phase ^ (512u * Q)) * (Q - weight));
        phase = (phase + Q - ratio) & PHASE_MASK;
    }
    write_index = (write_index + 1u) & (DEPTH - 1u);
    return output;
}

int main(int argc, char **argv)
{
    char *end;
    unsigned long ratio;
    int16_t samples[256];
    uint32_t native_input[512], native_output[512];
    int native_mode;
    size_t bytes, count, i;
    if (argc < 2 || argc > 3 || (argc == 3 && strcmp(argv[2], "native_s24"))) {
        fprintf(stderr, "usage: pitch_fixed ratio_q16 [native_s24] < input.raw > output.raw\n");
        return 2;
    }
    errno = 0;
    ratio = strtoul(argv[1], &end, 10);
    if (errno || *end || ratio < Q / 2u || ratio > 2u * Q) {
        fprintf(stderr, "ratio_q16 must be 32768..131072\n");
        return 2;
    }
    native_mode = argc == 3;
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    if (native_mode) {
        while ((bytes = fread(native_input, 1, sizeof(native_input), stdin)) != 0) {
            if (bytes % 8u) {
                fprintf(stderr, "incomplete S24_LE stereo frame\n");
                return 3;
            }
            count = bytes / 8u;
            for (i = 0; i < count; ++i) {
                uint32_t word = native_input[2u * i] & 0xffffffu;
                int32_t signed24 = (int32_t)(word ^ 0x800000u) - 0x800000;
                int16_t pcm = (int16_t)(signed24 >= 0 ? signed24 / 256
                                                      : -((-signed24 + 255) / 256));
                int16_t result = process_sample(pcm, (uint32_t)ratio);
                uint32_t packed = (uint32_t)((int32_t)result * 256) & 0xffffffu;
                native_output[2u * i] = packed;
                native_output[2u * i + 1u] = packed;
            }
            if (fwrite(native_output, 8u, count, stdout) != count)
                return 4;
        }
        return ferror(stdin) || fflush(stdout) ? 4 : 0;
    }
    while ((bytes = fread(samples, 1, sizeof(samples), stdin)) != 0) {
        if (bytes % sizeof(int16_t)) {
            fprintf(stderr, "incomplete PCM16 sample\n");
            return 3;
        }
        count = bytes / sizeof(int16_t);
        for (i = 0; i < count; ++i)
            samples[i] = process_sample(samples[i], (uint32_t)ratio);
        if (fwrite(samples, sizeof(int16_t), count, stdout) != count)
            return 4;
    }
    return ferror(stdin) || fflush(stdout) ? 4 : 0;
}
