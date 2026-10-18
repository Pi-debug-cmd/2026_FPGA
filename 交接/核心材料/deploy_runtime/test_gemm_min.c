// Minimal GEMM hardware timing + correctness probe.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>

#define GEMM_REGS_PHYS 0x43D00000u
#define GEMM_DMA_DEV "/dev/gemm_dma"
#define MAGIC 'G'
#define GET_PHYS _IOR(MAGIC,1,unsigned long long)
#define GET_SIZE _IOR(MAGIC,2,unsigned long long)
#define W_STRIDE 262144u

static double now_s(){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return ts.tv_sec+ts.tv_nsec*1e-9; }

int main(){
    int fd=open(GEMM_DMA_DEV,O_RDWR|O_SYNC);
    if(fd<0){perror("dma");return 1;}
    unsigned long long phys=0,size=0;
    ioctl(fd,GET_PHYS,&phys); ioctl(fd,GET_SIZE,&size);
    printf("dma phys=0x%llx size=%llu\n",phys,size);
    uint8_t*dma=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
    if(dma==MAP_FAILED){perror("mmap dma");return 1;}
    int mf=open("/dev/mem",O_RDWR|O_SYNC);
    volatile uint32_t*regs=mmap(NULL,0x10000,PROT_READ|PROT_WRITE,MAP_SHARED,mf,GEMM_REGS_PHYS);
    if(regs==MAP_FAILED){perror("mmap regs");return 1;}

    uint32_t w_phys=(uint32_t)phys;
    uint32_t in_phys=(uint32_t)phys+18*W_STRIDE;
    uint32_t out_phys=in_phys+26*512;

    // Fill a weight matrix: identity-ish. W[j][k] with j=output, k=input.
    // packed layout is [k][512], byte = W[j,k].
    uint8_t*w=dma;
    memset(w,0,512*512);
    for(unsigned k=0;k<512;k++) w[k*512+k]=1;   // W[k,k]=1 -> output = input
    // Input: 13 frames, frame t channel c = (t*7+c*3) small signed values
    uint8_t*in=dma+(in_phys-(uint32_t)phys);
    memset(in,0,13*512);
    for(unsigned t=0;t<13;t++)for(unsigned c=0;c<512;c++){
        int v=((t*7+c*3)%15)-7;
        in[t*512+c]=(uint8_t)(int8_t)v;
    }
    // expected out[t,c] = in[t,c] (identity)
    // clear output
    int32_t*out=(int32_t*)(dma+(out_phys-(uint32_t)phys));
    memset(out,0,13*512*sizeof(int32_t));

    regs[0x18/4]=w_phys; regs[0x20/4]=in_phys; regs[0x28/4]=out_phys;
    regs[0x30/4]=13; regs[0x38/4]=512; regs[0x40/4]=512;
    double t0=now_s();
    regs[0x00/4]=1;
    while(!(regs[0x00/4]&0x2)){}
    double t1=now_s();
    printf("GEMM 512x512 x13 frames: %.3f ms\n",(t1-t0)*1000);

    int errs=0; int32_t maxdiff=0;
    for(unsigned t=0;t<13;t++)for(unsigned c=0;c<512;c++){
        int exp=((t*7+c*3)%15)-7;
        int32_t got=out[t*512+c];
        int32_t d=got-exp; if(d<0)d=-d;
        if(d>maxdiff)maxdiff=d;
        if(d!=0)errs++;
    }
    printf("correctness: errs=%d maxabsdiff=%d\n",errs,maxdiff);
    return 0;
}
