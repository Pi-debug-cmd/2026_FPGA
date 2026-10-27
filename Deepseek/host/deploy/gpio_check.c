/* gpio_check.c - AXI GPIO 0x41200000 ratio_q16 write/readback (M2 proof).
 *
 * Build: arm-linux-gnueabihf-gcc -static -O2 -o gpio_check gpio_check.c
 */
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define BASE 0x41200000UL

int main(void)
{
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    volatile uint32_t *g;
    int i, ok = 1;
    const uint32_t cases[] = {0x15348u, 0x10000u, 0x20000u, 0x08000u, 86856u};
    if (fd < 0) { perror("open /dev/mem"); return 3; }
    g = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE, MAP_SHARED, fd, (off_t)BASE);
    if (g == MAP_FAILED) { perror("mmap"); return 3; }
    printf("{\"base\":\"0x41200000\",\"initial\":%u,\"cases\":[", g[0]);
    for (i = 0; i < 5; ++i) {
        g[0] = cases[i];
        uint32_t got = g[0];
        printf("%s{\"wrote\":%u,\"read\":%u,\"ok\":%s}", i ? "," : "",
               cases[i], got, got == cases[i] ? "true" : "false");
        if (got != cases[i]) ok = 0;
    }
    g[2] = 0;
    uint32_t r0 = g[2];
    g[2] = 1;
    uint32_t r1 = g[2];
    g[0] = 0x15348u;
    printf("],\"ch2\":{\"reset_read\":%u,\"run_read\":%u},\"restored\":%u,"
           "\"all_ok\":%s}\n", r0, r1, g[0],
           (ok && r0 == 0 && r1 == 1) ? "true" : "false");
    return (ok && r0 == 0 && r1 == 1) ? 0 : 1;
}
