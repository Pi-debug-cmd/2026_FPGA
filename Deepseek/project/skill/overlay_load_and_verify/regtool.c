/* regtool.c - register acceptance check for a PL overlay, static, no python needed.
 *
 * Why this file exists: the PetaLinux image we used on the Zynq-7020 ships a
 * python3 WITHOUT the `mmap` module, so the Python register tool cannot run on
 * the board at all.  This is the fallback that always works: one static binary,
 * /dev/mem, ~700 lines less than pulling in a toolchain on the target.
 *
 * Build (host, Vivado 2018.3 SDK cross compiler):
 *   arm-linux-gnueabihf-gcc -static -O2 -o regtool regtool.c
 *
 * Usage:
 *   regtool --base 0x41200000 \
 *           --check 0x00:18:86856,65536,131072,32768,86856 \
 *           --check 0x08:1:0,1
 *
 *   --base   block base address
 *   --check  <offset>:<width_bits>:<comma separated values to write+read back>
 *            the first value is also compared against the *initial* read, which
 *            is how a reset-value / C_DOUT_DEFAULT check is expressed here.
 *
 * Prints one JSON object, exit 0 only if every write/readback matched.
 */
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define MAX_CHECKS 16
#define MAX_VALS 16

struct check {
    unsigned long off;
    int width;
    unsigned long vals[MAX_VALS];
    int n;
};

static unsigned long mask_of(int width)
{
    if (width >= 32)
        return 0xffffffffUL;
    return (1UL << width) - 1UL;
}

int main(int argc, char **argv)
{
    unsigned long base = 0;
    struct check checks[MAX_CHECKS];
    int nchecks = 0, i, j, all_ok = 1, fd, span = 0x10000;
    volatile uint32_t *regs;

    for (i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--base") && i + 1 < argc) {
            base = strtoul(argv[++i], NULL, 0);
        } else if (!strcmp(argv[i], "--check") && i + 1 < argc && nchecks < MAX_CHECKS) {
            char *spec = strdup(argv[++i]);
            char *p1 = strchr(spec, ':');
            char *p2, *tok;
            if (!p1) { fprintf(stderr, "bad --check %s\n", spec); return 2; }
            *p1 = 0;
            p2 = strchr(p1 + 1, ':');
            if (!p2) { fprintf(stderr, "bad --check %s\n", spec); return 2; }
            *p2 = 0;
            checks[nchecks].off = strtoul(spec, NULL, 0);
            checks[nchecks].width = atoi(p1 + 1);
            checks[nchecks].n = 0;
            for (tok = strtok(p2 + 1, ","); tok && checks[nchecks].n < MAX_VALS;
                 tok = strtok(NULL, ","))
                checks[nchecks].vals[checks[nchecks].n++] =
                    strtoul(tok, NULL, 0) & mask_of(checks[nchecks].width);
            if (checks[nchecks].off + 4 > (unsigned long)span)
                span = (int)(checks[nchecks].off + 0x1000);
            nchecks++;
            free(spec);
        } else {
            fprintf(stderr, "usage: %s --base 0xADDR --check off:width:v1,v2,...\n", argv[0]);
            return 2;
        }
    }
    if (!nchecks) {
        fprintf(stderr, "no --check given\n");
        return 2;
    }

    fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd < 0) { perror("open /dev/mem"); return 3; }
    regs = mmap(NULL, (size_t)span, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)base);
    if (regs == MAP_FAILED) { perror("mmap"); return 3; }

    printf("{\"base\":\"0x%lx\",\"checks\":[", base);
    for (i = 0; i < nchecks; ++i) {
        unsigned long msk = mask_of(checks[i].width);
        volatile uint32_t *r = (volatile uint32_t *)((char *)regs + checks[i].off);
        unsigned long initial = *r & msk;
        int ok = 1;
        printf("%s{\"offset\":\"0x%lx\",\"width\":%d,\"initial\":%lu,\"cases\":[",
               i ? "," : "", checks[i].off, checks[i].width, initial);
        for (j = 0; j < checks[i].n; ++j) {
            unsigned long got;
            *r = (uint32_t)checks[i].vals[j];
            got = *r & msk;
            printf("%s{\"wrote\":%lu,\"read\":%lu,\"ok\":%s}", j ? "," : "",
                   checks[i].vals[j], got, got == checks[i].vals[j] ? "true" : "false");
            if (got != checks[i].vals[j]) ok = 0;
        }
        /* restore the documented reset value (== first value of the list) */
        *r = (uint32_t)checks[i].vals[0];
        printf("],\"restored\":%lu,\"reset_ok\":%s,\"rw_ok\":%s}",
               (unsigned long)(*r & msk), initial == checks[i].vals[0] ? "true" : "false",
               ok ? "true" : "false");
        if (!ok || initial != checks[i].vals[0]) all_ok = 0;
    }
    printf("],\"all_ok\":%s}\n", all_ok ? "true" : "false");
    return all_ok ? 0 : 1;
}
