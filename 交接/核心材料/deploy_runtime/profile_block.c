// Profiling wrapper: times each stage of llvc_process_block over many chunks.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include "llvc_runtime.h"

static double now_s(){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return ts.tv_sec+ts.tv_nsec*1e-9; }

// Stage timing accumulators (indexed), implemented inside the runtime via hooks.
// We instead time the whole block and separately call a gemm timing probe.
int main(int argc,char**argv){
    if(argc<2){fprintf(stderr,"usage: %s model.bin\n",argv[0]);return 1;}
    llvc_t m;
    if(llvc_load(&m,argv[1]))return 1;
    // read input.bin floats
    FILE*f=fopen(argc>2?argv[2]:"input.bin","rb");
    fseek(f,0,SEEK_END); long sz=ftell(f); fseek(f,0,SEEK_SET);
    float*in=malloc(sz); fread(in,1,sz,f); fclose(f);
    long nframes=sz/4;
    printf("input %ld samples\n",nframes);

    // streaming front
    float front[32]={0}; size_t cap=1<<20,plen=0; float*pend=malloc(cap);
    float block[240],out[208];
    long nchunks=0; double ttotal=0;
    size_t pi=0;
    while(pi+224<=nframes){
        // gather 224 samples
        if(plen<224){
            size_t want=224;
            if(plen+want>cap){cap*=2;pend=realloc(pend,cap);}
            memcpy(pend+plen,in+pi,want*4); pi+=want; plen+=want;
        }
        float*shifted=pend+16;
        memcpy(block,front,32*4);
        memcpy(block+32,shifted,208*4);
        double t0=now_s();
        llvc_process_block(&m,block,out);
        ttotal+=now_s()-t0;
        nchunks++;
        memcpy(front,shifted+208-32,32*4);
        memmove(pend,pend+208,(plen-208)*4); plen-=208;
    }
    printf("chunks=%ld  avg block=%.3f ms  total=%.3f s\n",
           nchunks,ttotal/nchunks*1000,ttotal);
    printf("audio duration=%.3f s -> factor %.2fx real-time\n",
           nchunks*0.013,ttotal/(nchunks*0.013));
    return 0;
}
