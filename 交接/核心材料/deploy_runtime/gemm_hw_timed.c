// gemm_hw.c - Xilinx HLS gemm_s8 AXI-lite backend, with timing counters.
#include "gemm_backend.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

static double now_s(){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return ts.tv_sec+ts.tv_nsec*1e-9; }
// timing counters (ms totals)
double g_t_quant=0, g_t_inmcpy=0, g_t_busy=0, g_t_outmcpy=0, g_t_calls=0;

#define GEMM_MAGIC 'G'
#define IOCTL_GET_PHYS _IOR(GEMM_MAGIC,1,uint64_t)
#define IOCTL_GET_SIZE _IOR(GEMM_MAGIC,2,uint64_t)

static volatile uint32_t *gemm;
static int dma_fd=-1;
static uint8_t *dma_usr=NULL;
static uint32_t dma_phys=0,dma_size=0;

#define W_STRIDE 262144

int gemm_setup(const void *llvc){
    dma_fd=open("/dev/gemm_dma",O_RDWR);
    if(dma_fd<0){perror("open gemm");return 1;}
    if(ioctl(dma_fd,IOCTL_GET_PHYS,&dma_phys)||ioctl(dma_fd,IOCTL_GET_SIZE,&dma_size)){
        perror("ioctl");return 1;}
    dma_usr=mmap(NULL,dma_size,PROT_READ|PROT_WRITE,MAP_SHARED,dma_fd,0);
    if(dma_usr==MAP_FAILED){perror("mmap dma");return 1;}
    int gfd=open("/dev/mem",O_RDWR|O_SYNC);
    if(gfd<0){perror("open mem");return 1;}
    gemm=mmap(NULL,0x1000,PROT_READ|PROT_WRITE,MAP_SHARED,gfd,0x43D00000);
    if(gemm==MAP_FAILED){perror("mmap gemm");return 1;}
    close(gfd);
    uint32_t need=18*W_STRIDE+26*512+26*512*4;
    if(need>dma_size){fprintf(stderr,"dma too small: %u < %u\n",dma_size,need);return 1;}
    return 0;
}

float gemm_quantize_input(const float *in, uint8_t *dst, unsigned frames, unsigned in_c){
    double t0=now_s();
    float amax=0;
    for(unsigned i=0;i<frames*in_c;++i){float a=fabsf(in[i]);if(a>amax)amax=a;}
    float scale=amax/127.0f; if(scale<1e-8f)scale=1e-8f;
    float inv=1.0f/scale;
    for(unsigned t=0;t<frames;++t){
        const float*r=in+(size_t)t*512; uint8_t*d=dst+t*512;
        for(unsigned i=0;i<in_c;++i){
            int v=(int)(r[i]*inv); if(v>127)v=127; if(v<-128)v=-128; d[i]=(int8_t)v;}
        for(unsigned i=in_c;i<512;++i)d[i]=0;
    }
    g_t_quant+=now_s()-t0;
    return scale;
}

int gemm_run_mi(unsigned mi, const uint8_t *w, const uint8_t *xin, int32_t *yout,
                 unsigned frames, unsigned in_c, unsigned out_c){
    g_t_calls++;
    uint8_t *w_usr=dma_usr+(size_t)mi*W_STRIDE;
    uint8_t *in_usr=dma_usr+(size_t)18*W_STRIDE;
    int32_t *out_usr=(int32_t*)(dma_usr+(size_t)18*W_STRIDE+26*512);
    uint32_t w_phys=dma_phys+(uint32_t)mi*W_STRIDE;
    uint32_t in_phys=dma_phys+18*W_STRIDE;
    uint32_t out_phys=in_phys+26*512;

    double t0=now_s();
    memcpy(in_usr,xin,frames*512);
    g_t_inmcpy+=now_s()-t0;

    gemm[0x18/4]=w_phys; gemm[0x20/4]=in_phys; gemm[0x28/4]=out_phys;
    gemm[0x30/4]=frames; gemm[0x38/4]=in_c; gemm[0x40/4]=out_c;
    gemm[0]=0x1;

    t0=now_s();
    uint32_t ctrl;
    do { ctrl=gemm[0]; } while(!(ctrl&0x2));
    g_t_busy+=now_s()-t0;

    t0=now_s();
    memcpy(yout,out_usr,frames*512*sizeof(int32_t));
    g_t_outmcpy+=now_s()-t0;
    return 0;
}
