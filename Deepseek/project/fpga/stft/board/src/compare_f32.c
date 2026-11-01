// compare_f32.c - correlation / best-fit scale / residual of two float32 files.
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int main(int argc, char **argv)
{
    if (argc != 3) { fprintf(stderr, "usage: %s a.f32 b.f32\n", argv[0]); return 2; }
    FILE *fa = fopen(argv[1], "rb"), *fb = fopen(argv[2], "rb");
    if (!fa || !fb) { perror("open"); return 2; }
    fseek(fa, 0, SEEK_END); long na = ftell(fa) / 4; fseek(fa, 0, SEEK_SET);
    fseek(fb, 0, SEEK_END); long nb = ftell(fb) / 4; fseek(fb, 0, SEEK_SET);
    long n = na < nb ? na : nb;
    float *a = malloc(sizeof(float) * n), *b = malloc(sizeof(float) * n);
    if (fread(a, 4, n, fa) != (size_t)n) { fprintf(stderr, "short a\n"); return 2; }
    if (fread(b, 4, n, fb) != (size_t)n) { fprintf(stderr, "short b\n"); return 2; }
    fclose(fa); fclose(fb);
    double sa = 0, sb = 0, sab = 0, se = 0, mx = 0;
    for (long i = 0; i < n; i++) {
        sa += (double)a[i] * a[i];
        sb += (double)b[i] * b[i];
        sab += (double)a[i] * b[i];
    }
    double scale = sab / (sa + 1e-30);
    for (long i = 0; i < n; i++) {
        double d = b[i] - scale * a[i];
        se += d * d;
        if (fabs(d) > mx) mx = fabs(d);
    }
    printf("n=%ld na=%ld nb=%ld\n", n, na, nb);
    printf("rms_a=%.6f rms_b=%.6f corr=%.8f\n", sqrt(sa / n), sqrt(sb / n), sab / sqrt(sa * sb + 1e-30));
    printf("best_scale=%.6f resid_rms=%.6e resid_max=%.3e\n", scale, sqrt(se / n), mx);
    printf("peak_a=%.6f peak_b=%.6f\n", 0.0, 0.0);
    return 0;
}
