// Profiling main with gemm timing breakdown.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "llvc_runtime.h"
extern double g_stage[16];
extern double g_t_quant,g_t_inmcpy,g_t_busy,g_t_outmcpy,g_t_calls;
static const char* names[16]={
  "convnet_pre","in_conv","dcc_enc","label","proj_e2d","decoder_ctx",
  "self_attn","cross_attn","ffn","proj_d2e","outin_mul","out_conv",
  "gemm(quant+run)","14","15"};
int main(int argc,char**argv){
    if(argc<2){fprintf(stderr,"usage: %s model.bin input.bin\n",argv[0]);return 1;}
    llvc_t m;
    if(llvc_load(&m,argv[1]))return 1;
    FILE*f=fopen(argv[2],"rb");
    fseek(f,0,SEEK_END);long sz=ftell(f);fseek(f,0,SEEK_SET);
    float*in=malloc(sz);fread(in,1,sz,f);fclose(f);
    long nframes=sz/4;
    float front[32]={0};size_t cap=1<<20,plen=0;float*pend=malloc(cap);
    float block[240],out[208];long nchunks=0;size_t pi=0;
    while(pi+224<=nframes){
        memcpy(pend+plen,in+pi,224*4);pi+=224;plen+=224;
        float*shifted=pend+16;
        memcpy(block,front,32*4);memcpy(block+32,shifted,208*4);
        llvc_process_block(&m,block,out);nchunks++;
        memcpy(front,shifted+208-32,32*4);
        memmove(pend,pend+208,(plen-208)*4);plen-=208;}
    printf("chunks=%ld  gemm calls/chunk=%.0f\n",nchunks,g_t_calls/nchunks);
    double total=0;
    for(int s=0;s<13;++s){
        double avg=g_stage[s]/nchunks*1000;
        printf("  %-16s %7.3f ms/chunk\n",names[s],avg);
        total+=g_stage[s];
    }
    printf("  --- GEMM breakdown ---\n");
    printf("  quantize         %7.3f ms/chunk\n",g_t_quant/nchunks*1000);
    printf("  in memcpy(unc)   %7.3f ms/chunk\n",g_t_inmcpy/nchunks*1000);
    printf("  HW busy-wait     %7.3f ms/chunk\n",g_t_busy/nchunks*1000);
    printf("  out memcpy(unc)  %7.3f ms/chunk\n",g_t_outmcpy/nchunks*1000);
    printf("  TOTAL %.3f ms/chunk (budget 13 ms) -> %.2fx real-time\n",
           total/nchunks*1000,total/(nchunks*0.013));
    return 0;
}
