/* Decisive GEMM test: separate dimension (256) from address-group (group1). */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/ioctl.h>

#define GEMM_REGS_PHYS 0x43D00000u
#define GEMM_DMA_DEV "/dev/gemm_dma"
#define MAGIC 'G'
#define GET_PHYS _IOR(MAGIC,1,unsigned long long)
#define GET_SIZE _IOR(MAGIC,2,unsigned long long)

#define W_STRIDE 262144u
#define IN0 (16u*W_STRIDE)
#define OUT0 (IN0+26u*512u)
#define GIO  (26u*512u+26u*512u*4u)
#define IN1  (16u*W_STRIDE+GIO)
#define OUT1 (IN1+26u*512u)

static volatile uint32_t *regs;
static uint8_t *dma;
static uint32_t dma_phys;

static int8_t w384[384*512], w256[256*512];
static int8_t xin[26*512];

static void fill_mat(int8_t *w, int K, int N, int seed){
    memset(w,0,512*K);
    for(int k=0;k<K;k++)for(int j=0;j<N;j++)
        w[k*512+j]=(int8_t)(((k*13+j*7+seed)%255)-127);
}
static void fill_in(int K, int frames, int seed){
    memset(xin,0,26*512);
    for(int t=0;t<frames;t++)for(int k=0;k<K;k++)
        xin[t*512+k]=(int8_t)(((t*17+k*11+seed)%255)-127);
}
static unsigned run_case(const char*name, uint32_t woff, uint32_t inoff, uint32_t outoff,
                         int frames, int K, int N, const int8_t *w){
    /* weights already placed; place input */
    memcpy(dma+inoff, xin, (size_t)frames*512);
    regs[0x18/4]=dma_phys+woff;
    regs[0x20/4]=dma_phys+inoff;
    regs[0x28/4]=dma_phys+outoff;
    regs[0x30/4]=frames;
    regs[0x38/4]=K;
    regs[0x40/4]=N;
    regs[0x00/4]=1;
    while(!(regs[0x00/4]&0x2)){}
    int32_t *out=(int32_t*)(dma+outoff);
    unsigned err=0; int32_t maxd=0, fe=0, fa=0;
    for(int t=0;t<frames;t++)for(int j=0;j<N;j++){
        int32_t want=0;
        for(int k=0;k<K;k++) want+=(int32_t)xin[t*512+k]*(int32_t)w[k*512+j];
        int32_t got=out[t*512+j];
        int32_t d=got>want?got-want:want-got;
        if(d){ if(!err){fe=want;fa=got;} err++; if(d>maxd)maxd=d; }
    }
    printf("%-22s K=%d N=%d frames=%d errors=%u maxdiff=%d want=%d got=%d -> %s\n",
           name,K,N,frames,err,maxd,fe,fa,err?"FAIL":"PASS");
    fflush(stdout);
    return err;
}

int main(){
    int fd=open(GEMM_DMA_DEV,O_RDWR|O_SYNC);
    if(fd<0){perror("dma");return 1;}
    unsigned long long phys=0,size=0;
    if(ioctl(fd,GET_PHYS,&phys)<0||ioctl(fd,GET_SIZE,&size)<0){perror("ioctl");return 1;}
    dma_phys=(uint32_t)phys;
    dma=mmap(NULL,(size_t)size,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
    if(dma==MAP_FAILED){perror("mmap dma");return 1;}
    int mf=open("/dev/mem",O_RDWR|O_SYNC);
    regs=mmap(NULL,0x10000,PROT_READ|PROT_WRITE,MAP_SHARED,mf,GEMM_REGS_PHYS);
    if(regs==MAP_FAILED){perror("mmap regs");return 1;}

    int frames=4;
    /* build weights */
    fill_mat(w384,384,384,3);
    fill_mat(w256,256,256,5);
    /* place weights: w384 -> slot0 (off 0); w256 -> slot1 (off W_STRIDE) */
    memcpy(dma+0, w384, (size_t)384*512);
    memcpy(dma+W_STRIDE, w256, (size_t)256*512);

    unsigned tot=0;
    /* 384 on group0 */
    fill_in(384,frames,1); tot+=run_case("384_group0",0,IN0,OUT0,frames,384,384,w384);
    /* 384 on group1 */
    fill_in(384,frames,1); tot+=run_case("384_group1",0,IN1,OUT1,frames,384,384,w384);
    /* 256 on group0 */
    fill_in(256,frames,2); tot+=run_case("256_group0",W_STRIDE,IN0,OUT0,frames,256,256,w256);
    /* 256 on group1 */
    fill_in(256,frames,2); tot+=run_case("256_group1",W_STRIDE,IN1,OUT1,frames,256,256,w256);

    /* frames=13, full 256 weights, group1 (isolate frame count) */
    fill_in(256,13,2); tot+=run_case("256_g1_f13",W_STRIDE,IN1,OUT1,13,256,256,w256);

    /* exact matrix6 conditions: 192 real rows/outputs, zero padded to 256, f=13 */
    memset(w256,0,512*256);
    for(int k=0;k<192;k++)for(int j=0;j<192;j++)
        w256[k*512+j]=(int8_t)(((k*13+j*7+5)%255)-127);  /* rows 192-255 already 0 */
    memcpy(dma+W_STRIDE,w256,(size_t)256*512);
    /* build 192-wide input into a host buffer then place (cols 192-511 zero) */
    memset(xin,0,26*512);
    for(int t=0;t<13;t++)for(int k=0;k<192;k++)
        xin[t*512+k]=(int8_t)(((t*17+k*11+2)%255)-127);
    memcpy(dma+IN1,xin,(size_t)13*512);
    regs[0x18/4]=dma_phys+W_STRIDE;
    regs[0x20/4]=dma_phys+IN1;
    regs[0x28/4]=dma_phys+OUT1;
    regs[0x30/4]=13; regs[0x38/4]=256; regs[0x40/4]=256; regs[0x0]=1;
    while(!(regs[0x0]&0x2)){}
    { int32_t *out=(int32_t*)(dma+OUT1); unsigned err=0; int32_t maxd=0,fe=0,fa=0;
      for(int t=0;t<13;t++)for(int j=0;j<192;j++){
        int32_t want=0;
        for(int k=0;k<192;k++) want+=(int32_t)xin[t*512+k]*(int32_t)w256[k*512+j];
        int32_t got=out[t*512+j]; int32_t d=got>want?got-want:want-got;
        if(d){if(!err){fe=want;fa=got;}err++;if(d>maxd)maxd=d;}
      }
      printf("%-22s K=256 N=256 frames=13 errors=%u maxdiff=%d want=%d got=%d -> %s\n",
             "192pad_g1_f13",err,maxd,fe,fa,err?"FAIL":"PASS"); fflush(stdout); tot+=err;
    }

    printf("TOTAL_ERRORS=%u\n",tot);
    return tot?1:0;
}
