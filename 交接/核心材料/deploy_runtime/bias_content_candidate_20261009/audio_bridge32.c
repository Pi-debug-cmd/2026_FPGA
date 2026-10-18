/* Lightweight diagnostic bridge between the board's native 32 kHz S24_LE
 * stereo stream and the model's 16 kHz float mono stream. No boot changes. */
#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#ifdef AUDIO_BRIDGE_PROGRESS
static double clock_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}
#endif

static int write_all(const void *data, size_t count) {
    const unsigned char *p = data;
    while (count) {
        ssize_t n = write(STDOUT_FILENO, p, count);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        p += n;
        count -= (size_t)n;
    }
    return 0;
}

static int32_t unpack_s24(const unsigned char *p) {
    uint32_t u;
    memcpy(&u, p, sizeof(u));
    return ((int32_t)(u << 8)) >> 8;
}

static uint32_t pack_s24(float x) {
    if (x > 1.0f) x = 1.0f;
    if (x < -1.0f) x = -1.0f;
    int32_t v = (int32_t)lrintf(x * 8388607.0f);
    return (uint32_t)v & 0x00ffffffu;
}

static int downsample(void) {
    unsigned char in[32768 + 15];
    float out[2048];
    size_t remain = 0;
#ifdef AUDIO_BRIDGE_PROGRESS
    size_t total = 0;
    double started = clock_seconds();
#endif
#ifdef AUDIO_BRIDGE_LEVELS
    double energy = 0;
    float peak = 0;
    size_t level_count = 0;
#endif
    for (;;) {
        ssize_t n = read(STDIN_FILENO, in + remain, sizeof(in) - remain);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) { perror("read capture"); return 1; }
        size_t bytes = remain + (size_t)n;
        size_t pairs = bytes / 16;
        for (size_t i = 0; i < pairs; ++i) {
            int32_t a = unpack_s24(in + 16*i);
            int32_t b = unpack_s24(in + 16*i + 8);
            out[i] = (float)((double)a + b) * (0.5f / 8388608.0f);
#ifdef AUDIO_BRIDGE_LEVELS
            float magnitude = fabsf(out[i]);
            energy += (double)out[i] * out[i];
            if (magnitude > peak) peak = magnitude;
            ++level_count;
#endif
        }
        if (write_all(out, pairs * sizeof(float))) { perror("write downsample"); return 1; }
#ifdef AUDIO_BRIDGE_PROGRESS
        size_t prior = total;
        total += pairs;
        if (total / 16000 > prior / 16000) {
#ifdef AUDIO_BRIDGE_LEVELS
            fprintf(stderr, "bridge_down_t=%.3f samples=%zu peak=%.5f rms=%.5f\n",
                    clock_seconds()-started, total, peak, sqrt(energy/level_count));
            energy=0;peak=0;level_count=0;
#else
            fprintf(stderr, "bridge_down_t=%.3f samples=%zu\n", clock_seconds()-started, total);
#endif
        }
#endif
        remain = bytes - pairs * 16;
        memmove(in, in + pairs*16, remain);
        if (n == 0) return remain ? 2 : 0;
    }
}

static int upsample(void) {
    unsigned char in[8192 + 3];
    uint32_t out[8192];
    size_t remain = 0;
    float previous = 0.0f;
#ifdef AUDIO_BRIDGE_PROGRESS
    size_t total = 0;
    double started = clock_seconds();
#endif
#ifdef AUDIO_BRIDGE_LEVELS
    double energy = 0;
    float peak = 0;
    size_t level_count = 0;
#endif
    for (;;) {
        ssize_t n = read(STDIN_FILENO, in + remain, sizeof(in) - remain);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) { perror("read model"); return 1; }
        size_t bytes = remain + (size_t)n;
        size_t count = bytes / 4;
        for (size_t i = 0; i < count; ++i) {
            float current;
            memcpy(&current, in + 4*i, sizeof(current));
#ifdef AUDIO_BRIDGE_LEVELS
            float magnitude = fabsf(current);
            energy += (double)current * current;
            if (magnitude > peak) peak = magnitude;
            ++level_count;
#endif
            uint32_t middle = pack_s24(0.5f * (previous + current));
            uint32_t final = pack_s24(current);
            out[4*i] = middle;
            out[4*i+1] = middle;
            out[4*i+2] = final;
            out[4*i+3] = final;
            previous = current;
        }
        if (write_all(out, count * 4 * sizeof(uint32_t))) { perror("write playback"); return 1; }
#ifdef AUDIO_BRIDGE_PROGRESS
        size_t prior = total;
        total += count;
        if (total / 16000 > prior / 16000) {
#ifdef AUDIO_BRIDGE_LEVELS
            fprintf(stderr, "bridge_up_t=%.3f samples=%zu peak=%.5f rms=%.5f\n",
                    clock_seconds()-started, total, peak, sqrt(energy/level_count));
            energy=0;peak=0;level_count=0;
#else
            fprintf(stderr, "bridge_up_t=%.3f samples=%zu\n", clock_seconds()-started, total);
#endif
        }
#endif
        remain = bytes - count * 4;
        memmove(in, in + count*4, remain);
        if (n == 0) return remain ? 2 : 0;
    }
}

int main(int argc, char **argv) {
    if (argc != 2) { fputs("usage: audio_bridge32 down|up\n", stderr); return 2; }
    if (!strcmp(argv[1], "down")) return downsample();
    if (!strcmp(argv[1], "up")) return upsample();
    fputs("unknown direction\n", stderr);
    return 2;
}
