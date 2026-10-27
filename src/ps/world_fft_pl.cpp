// Explicit PL FFT backend; unsupported sizes retain the original double FFT.
#include "world/fft.h"
#include "../kernel/world_fft_ioctl.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <stdint.h>
#include <time.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
namespace {
static_assert(sizeof(float)==4 && sizeof(world_fft_request)==24,"FFT DMA ABI");
double Now() { timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9; }
struct Backend {
  int size=0, fd=-1;
  uint64_t input[2048], output[2048];
  std::mutex mutex;
  unsigned long calls=0;
  double prepare_s=0, dma_s=0, unpack_s=0, wait_s=0;
  Backend() {
    const char* s=std::getenv("WORLD_FFT");
    if (!s || !std::strcmp(s,"cpu")) return;
    if (!std::strcmp(s,"pl")) size=-1;
    else if (!std::strcmp(s,"pl2048")) size=2048;
    else if (!std::strcmp(s,"pl1024")) size=1024;
    else std::abort();
    fd=open("/dev/world_fft",O_RDWR|O_CLOEXEC);
    if(fd<0) {std::perror("open /dev/world_fft");std::abort();}
  }
  ~Backend() {
    if(size) std::fprintf(stderr,"{\"kind\":\"world_fft_pl\",\"size\":%d,\"calls\":%lu,\"prepare_s\":%.9f,\"dma_s\":%.9f,\"unpack_s\":%.9f,\"wait_s\":%.9f}\n",
      size,calls,prepare_s,dma_s,unpack_s,wait_s);
    if(fd>=0) close(fd);
  }
} backend;
}
extern "C" {
void __real_fft_execute(fft_plan);
void __wrap_fft_execute(fft_plan p) {
  if(!backend.size || (p.n!=1024 && p.n!=2048) || (backend.size>0 && p.n!=backend.size)) {
    __real_fft_execute(p);return;
  }
  double t=Now();
  std::lock_guard<std::mutex> lock(backend.mutex);
  double begin=Now(); backend.wait_s+=begin-t;
  const bool real_in=p.c_in==NULL, real_out=p.c_out==NULL;
  for(int i=0;i<p.n;++i) {
    float pair[2];
    if(real_in) {pair[0]=p.in[i];pair[1]=0;}
    else if(real_out && i>p.n/2) {pair[0]=p.c_in[p.n-i][0];pair[1]=-p.c_in[p.n-i][1];}
    else {pair[0]=p.c_in[i][0];pair[1]=p.c_in[i][1];}
    // WORLD's Ooura c2c wrapper transforms the conjugated complex input.
    if(!real_in && !real_out) pair[1]=-pair[1];
    if(real_out && (i==0 || i==p.n/2)) pair[1]=0;
    if(!std::isfinite(pair[0]) || !std::isfinite(pair[1])) std::abort();
    std::memcpy(&backend.input[i],pair,sizeof(pair));
  }
  world_fft_request request={uint64_t(uintptr_t(backend.input)),uint64_t(uintptr_t(backend.output)),
                             unsigned(p.n),unsigned(p.sign==FFT_FORWARD)};
  t=Now();backend.prepare_s+=t-begin;
  if(ioctl(backend.fd,WORLD_FFT_PROCESS,&request)) {std::perror("WORLD_FFT_PROCESS");std::abort();}
  begin=Now();backend.dma_s+=begin-t;
  for(int i=0;i<(real_in?p.n/2+1:p.n);++i) {
    float pair[2];std::memcpy(pair,&backend.output[i],sizeof(pair));
    if(!std::isfinite(pair[0]) || !std::isfinite(pair[1])) std::abort();
    if(real_out) p.out[i]=pair[0];
    else {p.c_out[i][0]=pair[0];p.c_out[i][1]=pair[1];}
  }
  if(real_in) p.c_out[0][1]=p.c_out[p.n/2][1]=0;
  backend.unpack_s+=Now()-begin;++backend.calls;
}
}
