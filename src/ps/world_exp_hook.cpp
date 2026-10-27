#include "world_exp_hook.h"
#include "../kernel/world_exp_ioctl.h"
#include "world_exp_tables.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdint.h>
#include <time.h>
#ifdef __linux__
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#endif
namespace {
struct Backend {
  int mode = 0, fd = -1;
  unsigned long calls = 0, fallback = 0;
  double elapsed = 0;
  double prepare_s = 0, dma_s = 0, unpack_s = 0;
  world_exp_packet packet;
  Backend() {
    const char *m = std::getenv("WORLD_EXP");
    if (!m || !std::strcmp(m, "cpu")) return;
    if (!std::strcmp(m, "model")) { mode = 1; return; }
    if (std::strcmp(m, "pl")) { std::fprintf(stderr,"Invalid WORLD_EXP\n"); std::abort(); }
    mode = 2;
#ifdef __linux__
    fd = open("/dev/world_exp", O_RDWR | O_CLOEXEC);
#endif
    if (fd < 0) { std::perror("open /dev/world_exp"); std::abort(); }
  }
  ~Backend() {
    if (mode) std::fprintf(stderr,"{\"kind\":\"world_exp_backend\",\"mode\":%d,\"calls\":%lu,\"fallback\":%lu,\"seconds\":%.9f,\"prepare_s\":%.9f,\"dma_s\":%.9f,\"unpack_s\":%.9f}\n",mode,calls,fallback,elapsed,prepare_s,dma_s,unpack_s);
#ifdef __linux__
    if (fd >= 0) close(fd);
#endif
  }
};
static Backend backend; // Construct before runtime worker threads; render is sole caller.
static double Now() {
  timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9;
}
static int64_t Model(int a, int b, bool imaginary) {
  if (b < 0) b += 1647099;
  int k = (int64_t(a)*94548)>>34;
  int r = a-k*181704;
  if (r<0) {r+=181704; --k;}
  if (r>=181704) {r-=181704; ++k;}
  int64_t u=int64_t(r)*94548;
  int idx=std::min(255,int(u>>26)), f=(u&0x3ffffff)>>10;
  int lo=exp_table[idx], hi=idx==255?131072:exp_table[idx+1];
  int64_t e=lo+((int64_t(hi-lo)*f)>>16);
  int sh=-(k+1); e=sh>=0 ? e>>sh : e<<(-sh);
  int64_t v=int64_t(b)*41722;
  int j=std::min(1023,int(v>>26)), g=(v&0x3ffffff)>>10;
  const int *table=imaginary?sin_table:cos_table;
  int c=table[j]+((int64_t(table[(j+1)&1023]-table[j])*g)>>16);
  return std::max<int64_t>(-524288,std::min<int64_t>(524287,(e*c+131072)>>17));
}
static int Signed20(uint64_t x) { return int((x&0xfffff)^0x80000)-0x80000; }
}
bool WorldExpOffload(double (*sp)[2], int n) {
  if (!backend.mode) return false;
  if (n!=1024) {++backend.fallback; return false;}
  const double start=Now(), inv=1.0/n;
  // Normalize each frame to peak exp(a)=1, recovering low-energy precision.
  double peak=-1e300;
  for (int i=0;i<513;++i) {
    if (!std::isfinite(sp[i][0]) || !std::isfinite(sp[i][1])) {++backend.fallback; return false;}
    peak=std::max(peak,sp[i][0]*inv);
  }
  for (int i=0;i<513;++i) {
    const double a=sp[i][0]*inv-peak;
    // 24-bit input and 6-bit shift contract. Entire frame uses CPU if exceeded.
    if (a < -20.0 || peak > 600 || peak < -600) {++backend.fallback; return false;}
    double b=sp[i][1]*inv;
    // WORLD phase usually lies inside this interval. General remainder is rare.
    if (b > 3.14159265358979323846 || b < -3.14159265358979323846)
      b=std::remainder(b,6.2831853071795864769);
    // Truncation plus one correction implements floor(x+.5) exactly.
    double af=a*262144.0+0.5, bf=b*262144.0+0.5;
    int aq=int(af), bq=int(bf);
    aq-=af<aq; bq-=bf<bq;
    backend.packet.input[i]=(uint64_t(uint32_t(bq)&0xffffff)<<24)|(uint32_t(aq)&0xffffff);
    if (backend.mode==1) backend.packet.output[i]=
      (uint64_t(Model(aq,bq,true)&0xfffff)<<20)|(Model(aq,bq,false)&0xfffff);
  }
  const double prepared=Now();
#ifdef __linux__
  if (backend.mode==2 && ioctl(backend.fd,WORLD_EXP_PROCESS,&backend.packet)<0) {
    std::perror("WORLD PL DMA; refusing silent CPU fallback"); std::abort();
  }
#endif
  const double transferred=Now();
  double scale=std::exp(peak)/131072.0;
  for (int i=0;i<513;++i) {
    uint64_t y=backend.packet.output[i];
    sp[i][0]=Signed20(y)*scale; sp[i][1]=Signed20(y>>20)*scale;
  }
  const double finished=Now();
  ++backend.calls; backend.elapsed+=finished-start;
  backend.prepare_s+=prepared-start; backend.dma_s+=transferred-prepared;
  backend.unpack_s+=finished-transferred;
  return true;
}
