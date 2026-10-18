// deploy_llvc.c - streaming voice conversion front end.
// Mirrors LLVCAudioStream: keeps a pending buffer and a 32-sample front;
// when pending >= 224, builds block = cat(front, shifted(pending[16:224])),
// processes 240 -> 208, updates front = shifted[176:208], drops 208 from pending.
// Reads raw float32 mono 16k from stdin; writes converted float32 to stdout.
#include "llvc_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

#define CHUNK_SAMPLES 208
#define FRONT 32
#define NEED (CHUNK_SAMPLES+16)

int main(int argc, char **argv) {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    if (argc < 2) { fprintf(stderr, "usage: %s model.bin\n", argv[0]); return 1; }
    llvc_t m;
    if (llvc_load(&m, argv[1])) return 1;

    float front[FRONT] = {0};
    size_t cap = 1 << 20, plen = 0;
    float *pend = malloc(cap*sizeof(float));
    float block[240], out[208];
    float ib[4096];

    int eof = 0;
    size_t total_in = 0, total_out = 0;
    for (;;) {
        while (!eof && plen < NEED) {
            size_t got = fread(ib, sizeof(float), 4096, stdin);
            if (got == 0) { eof = 1; break; }
            total_in += got;
            if (plen+got > cap) {
                while (plen+got > cap) cap *= 2;
                pend = realloc(pend, cap*sizeof(float));
            }
            memcpy(pend+plen, ib, got*sizeof(float)); plen += got;
        }
        if (!eof && plen >= NEED) {
            float *shifted = pend+16;
            memcpy(block, front, FRONT*sizeof(float));
            memcpy(block+FRONT, shifted, CHUNK_SAMPLES*sizeof(float));
            llvc_process_block(&m, block, out);
            if (fwrite(out, sizeof(float), CHUNK_SAMPLES, stdout) != CHUNK_SAMPLES) break;
            total_out += CHUNK_SAMPLES;
            memcpy(front, shifted+CHUNK_SAMPLES-FRONT, FRONT*sizeof(float));
            memmove(pend, pend+CHUNK_SAMPLES, (plen-CHUNK_SAMPLES)*sizeof(float));
            plen -= CHUNK_SAMPLES;
        } else if (eof) {
            // flush: pad pending so blocks cover the remaining input
            if (total_out >= total_in) break;
            size_t want = NEED;
            if (plen < want) {
                memset(pend+plen, 0, (want-plen)*sizeof(float)); plen = want;
            }
            float *shifted = pend+16;
            memcpy(block, front, FRONT*sizeof(float));
            memcpy(block+FRONT, shifted, CHUNK_SAMPLES*sizeof(float));
            llvc_process_block(&m, block, out);
            size_t take = CHUNK_SAMPLES;
            if (total_out+take > total_in) take = total_in-total_out;
            fwrite(out, sizeof(float), take, stdout);
            total_out += take;
            memcpy(front, shifted+CHUNK_SAMPLES-FRONT, FRONT*sizeof(float));
            memmove(pend, pend+CHUNK_SAMPLES, (plen-CHUNK_SAMPLES)*sizeof(float));
            plen -= CHUNK_SAMPLES;
        }
        fflush(stdout);
    }
    return 0;
}
