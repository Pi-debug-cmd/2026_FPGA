// Probe GEMM register interface: read default, write+readback.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#define GEMM_REGS_PHYS 0x43D00000u
int main(){
    int mf=open("/dev/mem",O_RDWR|O_SYNC);
    if(mf<0){perror("/dev/mem");return 1;}
    volatile uint32_t*r=mmap(NULL,0x10000,PROT_READ|PROT_WRITE,MAP_SHARED,mf,GEMM_REGS_PHYS);
    if(r==MAP_FAILED){perror("mmap");return 1;}
    printf("GEMM regs @0x%x defaults:\n",GEMM_REGS_PHYS);
    for(unsigned off=0;off<=0x40;off+=0x8)
        printf("  [0x%02x] = 0x%08x\n",off,r[off/4]);
    // write a distinctive value to a scratch-ish register (0x30 frames) and read back
    r[0x30/4]=0xDEADBEEF;
    uint32_t rb=r[0x30/4];
    printf("wrote 0xDEADBEEF to 0x30, readback 0x%08x -> %s\n",rb,rb==0xDEADBEEF?"OK":"MISMATCH");
    r[0x38/4]=0x12345678;
    printf("0x38 readback 0x%08x -> %s\n",r[0x38/4],r[0x38/4]==0x12345678?"OK":"MISMATCH");
    // restore
    r[0x30/4]=0; r[0x38/4]=0;
    return 0;
}
