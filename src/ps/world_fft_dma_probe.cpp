// Silent FFT DMA check against unchanged Ooura double FFT and ioctl timing.
#include "world/fft.h"
#include "../kernel/world_fft_ioctl.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
#include <stdint.h>
#include <time.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
static double Now() {timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main() {
  int fd=open("/dev/world_fft",O_RDWR|O_CLOEXEC);
  if(fd<0) {std::perror("open world_fft");return 1;}
  uint64_t input[2048], output[2048];
  fft_complex x[2048], reference[2048];
  double real_input[2048];
  std::vector<double> timings[2];
  double worst_relative=0;
  uint32_t random=20261027;
  for(int run=0;run<32;++run) for(int slot=0;slot<2;++slot) for(int kind=0;kind<3;++kind) {
    const int n=slot?2048:1024;
    const bool compact=kind==2, inverse=kind==1;
    for(int i=0;i<n;++i) {
      float pair[2];
      for(int j=0;j<2;++j) {
        random=random*1664525+1013904223;
        pair[j]=run%4==0?0.f:run%4==1?(i==0?0.5f:0.f):float(int32_t(random))/2147483648.f;
        x[i][j]=pair[j];
      }
      if(compact) {
        real_input[i]=pair[0];
        std::memcpy(reinterpret_cast<unsigned char*>(input)+i*sizeof(float),pair,sizeof(float));
      } else {
        // Match WORLD c2c convention while the PL engine implements standard DFT.
        pair[1]=-pair[1];
        std::memcpy(&input[i],pair,sizeof(pair));
      }
    }
    fft_plan p=compact ? fft_plan_dft_r2c_1d(n,real_input,reference,FFT_ESTIMATE) :
                        fft_plan_dft_1d(n,x,reference,inverse?FFT_BACKWARD:FFT_FORWARD,FFT_ESTIMATE);
    fft_execute(p);fft_destroy_plan(p);
    world_fft_request request={uint64_t(uintptr_t(input)),uint64_t(uintptr_t(output)),unsigned(n),unsigned(!inverse) | (compact?2u:0u)};
    double t=Now();
    if(ioctl(fd,WORLD_FFT_PROCESS,&request)) {std::perror("WORLD_FFT_PROCESS");return 2;}
    timings[slot].push_back((Now()-t)*1e6);
    double energy=0,error=0;
    for(int i=0;i<(compact?n/2+1:n);++i) {
      float pair[2];std::memcpy(pair,&output[i],sizeof(pair));
      for(int j=0;j<2;++j) {
        if(!std::isfinite(pair[j])) return 3;
        double diff=pair[j]-reference[i][j];error+=diff*diff;
        energy+=reference[i][j]*reference[i][j];
      }
    }
    double relative=std::sqrt(error/std::max(energy,1e-30));
    worst_relative=std::max(worst_relative,relative);
    if(relative>1e-5) {std::fprintf(stderr,"FFT mismatch n=%d relative=%.9g\n",n,relative);return 4;}
  }
  close(fd);
  for(int slot=0;slot<2;++slot) {
    std::vector<double>& t=timings[slot];std::sort(t.begin(),t.end());
    std::printf("{\"kind\":\"world_fft_dma_probe\",\"n\":%d,\"calls\":%zu,\"p50_us\":%.6f,\"p95_us\":%.6f,\"max_us\":%.6f,\"worst_relative_l2\":%.9g}\n",
      slot?2048:1024,t.size(),t[t.size()/2],t[(t.size()*95+99)/100-1],t.back(),worst_relative);
  }
  return 0;
}
