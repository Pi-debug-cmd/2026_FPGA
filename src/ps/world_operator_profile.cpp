// Diagnostic linker wrappers. No arithmetic or scheduling changes to WORLD.
#include "world/fft.h"
#include "world/dio.h"
#include "world/stonemask.h"
#include "world/cheaptrick.h"
#include "world/d4c.h"
#include <cstdio>
#include <time.h>

namespace {
double Now() { timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9; }
struct Count { unsigned long calls=0; double seconds=0; };
struct Stats {
  int stage=0;
  Count fft[5][15][3][2]; // stage, log2(size), r2c/c2r/c2c, plan/execute
  Count top[5];
  ~Stats() {
    for(int s=0;s<5;++s) {
      if(top[s].calls) std::fprintf(stderr,"{\"kind\":\"world_operator_top\",\"stage\":%d,\"calls\":%lu,\"seconds\":%.9f}\n",s,top[s].calls,top[s].seconds);
      for(int n=0;n<15;++n) for(int type=0;type<3;++type) for(int op=0;op<2;++op) {
        const Count &c=fft[s][n][type][op];
        if(c.calls) std::fprintf(stderr,"{\"kind\":\"world_fft_profile\",\"stage\":%d,\"size\":%d,\"type\":%d,\"op\":%d,\"calls\":%lu,\"seconds\":%.9f}\n",s,1<<n,type,op,c.calls,c.seconds);
      }
    }
  }
};
thread_local Stats stats;
int Log2(int n) { int p=0; while(n>1) {n>>=1;++p;} return p<15?p:14; }
void Add(const fft_plan &p,int op,double begin) {
  const double seconds=Now()-begin;
  int type=p.c_in==NULL?0:(p.c_out==NULL?1:2);
  Count &c=stats.fft[stats.stage][Log2(p.n)][type][op]; ++c.calls;c.seconds+=seconds;
}
struct Scope {
  int stage, previous; double begin;
  explicit Scope(int s):stage(s),previous(stats.stage),begin(Now()) {stats.stage=s;}
  ~Scope() {++stats.top[stage].calls; stats.top[stage].seconds+=Now()-begin;stats.stage=previous;}
};
}
extern "C" {
void __real_fft_execute(fft_plan);
fft_plan __real_fft_plan_dft_1d(int,fft_complex*,fft_complex*,int,unsigned);
fft_plan __real_fft_plan_dft_r2c_1d(int,double*,fft_complex*,unsigned);
fft_plan __real_fft_plan_dft_c2r_1d(int,fft_complex*,double*,unsigned);
void __wrap_fft_execute(fft_plan p) {double t=Now(); __real_fft_execute(p);Add(p,1,t);}
fft_plan __wrap_fft_plan_dft_1d(int n,fft_complex*in,fft_complex*out,int sign,unsigned flags) {
  double t=Now();fft_plan p=__real_fft_plan_dft_1d(n,in,out,sign,flags);Add(p,0,t);return p;
}
fft_plan __wrap_fft_plan_dft_r2c_1d(int n,double*in,fft_complex*out,unsigned flags) {
  double t=Now();fft_plan p=__real_fft_plan_dft_r2c_1d(n,in,out,flags);Add(p,0,t);return p;
}
fft_plan __wrap_fft_plan_dft_c2r_1d(int n,fft_complex*in,double*out,unsigned flags) {
  double t=Now();fft_plan p=__real_fft_plan_dft_c2r_1d(n,in,out,flags);Add(p,0,t);return p;
}
void __real_Dio(const double*,int,int,const DioOption*,double*,double*);
void __wrap_Dio(const double*x,int n,int fs,const DioOption*o,double*t,double*f) {
  Scope scope(1);__real_Dio(x,n,fs,o,t,f);
}
void __real_StoneMask(const double*,int,int,const double*,const double*,int,double*);
void __wrap_StoneMask(const double*x,int n,int fs,const double*t,const double*f,int count,double*r) {
  Scope scope(2);__real_StoneMask(x,n,fs,t,f,count,r);
}
void __real_CheapTrick(const double*,int,int,const double*,const double*,int,const CheapTrickOption*,double**);
void __wrap_CheapTrick(const double*x,int n,int fs,const double*t,const double*f,int count,const CheapTrickOption*o,double**r) {
  Scope scope(3);__real_CheapTrick(x,n,fs,t,f,count,o,r);
}
void __real_D4C(const double*,int,int,const double*,const double*,int,int,const D4COption*,double**);
void __wrap_D4C(const double*x,int n,int fs,const double*t,const double*f,int count,int fft,const D4COption*o,double**r) {
  Scope scope(4);__real_D4C(x,n,fs,t,f,count,fft,o,r);
}
}
