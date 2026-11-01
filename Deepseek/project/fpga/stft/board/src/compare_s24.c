// compare_s24.c - correlation / max-diff of two S24_LE stereo files, on board.
// Usage: compare_s24 a.raw b.raw [channels]
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

static int32_t *load(const char *p, long *n, int ch)
{
    FILE *f = fopen(p, "rb");
    if (!f) { perror(p); exit(2); }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    long fr = sz / (4 * ch);
    unsigned char *buf = malloc((size_t)fr * 4 * ch);
    if (fread(buf, 4 * ch, fr, f) != (size_t)fr) { fprintf(stderr, "short %s\n", p); exit(2); }
    fclose(f);
    int32_t *out = malloc(sizeof(int32_t) * fr);
    for (long i = 0; i < fr; i++) {
        const unsigned char *b = buf + (size_t)i * 4 * ch;   // left channel
        // 24 valid bits left-justified in a 32-bit little-endian container:
        // the sample is the int32 word shifted right by 8, not the low 3 bytes.
        uint32_t w = (uint32_t)b[0] | ((uint32_t)b[1] << 8) |
                     ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);
        int32_t v = (int32_t)w >> 8;
        out[i] = (int32_t)lrint(v / 256.0);
    }
    free(buf);
    *n = fr;
    return out;
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: %s a.raw b.raw [ch]\n", argv[0]); return 2; }
    int ch = (argc > 3) ? atoi(argv[3]) : 2;
    long na, nb;
    int32_t *a = load(argv[1], &na, ch);
    int32_t *b = load(argv[2], &nb, ch);
    long n = (na < nb) ? na : nb;
    double sa = 0, sb = 0, sab = 0, se = 0;
    long maxd = 0, gt1 = 0, gt2 = 0;
    for (long i = 0; i < n; i++) {
        double x = a[i], y = b[i], d = y - x;
        sa += x * x; sb += y * y; sab += x * y; se += d * d;
        long ad = labs((long)d);
        if (ad > maxd) maxd = ad;
        if (ad > 1) gt1++;
        if (ad > 2) gt2++;
    }
    double corr = sab / sqrt(sa * sb + 1e-30);
    { int shown = 0;
      for (long i = 0; i < n && shown < 8; i++) {
        long ad = labs((long)(b[i] - a[i]));
        if (ad > 1000) { printf("big@%ld a=%d b=%d d=%ld\n", i, a[i], b[i], ad); shown++; }
      }
    }
    printf("samples=%ld corr=%.8f max_abs_diff=%ld rms_diff=%.4f gt1=%ld gt2=%ld\n",
           n, corr, maxd, sqrt(se / (double)n), gt1, gt2);
    printf("peak_a=%.0f peak_b=%.0f\n", sqrt(sa / n), sqrt(sb / n));
    return 0;
}


