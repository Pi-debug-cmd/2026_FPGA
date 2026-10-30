// Host-only bit-accurate AMD FFT IP model, before committing to PL integration.
// The vendor SDK is generated locally by Vivado and is not checked into Git.
#include "world/fft.h"
#include "world/dio.h"
#include "world/stonemask.h"
#include "world/cheaptrick.h"
#include "world/d4c.h"
#include "xfft_v9_1_bitacc_cmodel.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>

namespace {
thread_local int stage = 0;
struct Scope { int old; explicit Scope(int s):old(stage) {stage=s;} ~Scope() {stage=old;} };
int Mode() {
  static const int mode = [] {
    const char* s = std::getenv("WORLD_FFT_MODEL");
    if (!s || !std::strcmp(s,"cpu")) return 0;
    if (!std::strcmp(s,"analysis")) return 1;
    if (!std::strcmp(s,"render")) return 2;
    if (!std::strcmp(s,"all")) return 3;
    if (!std::strcmp(s,"d4c")) return 4;
    std::abort();
  }();
  return mode;
}
struct Model {
  std::mutex mutex;
  xilinx_ip_xfft_v9_1_state* state;
  double re[2048], im[2048], out_re[2048], out_im[2048];
  unsigned long calls = 0;
  Model() {
    xilinx_ip_xfft_v9_1_generics g = {11,3,1,1,32,25,1,0,0,1,0};
    state = xilinx_ip_xfft_v9_1_create_state(g);
    if (!state) std::abort();
  }
  ~Model() {
    std::fprintf(stderr,"{\"kind\":\"world_fft_ip_model\",\"calls\":%lu,\"mode\":%d}\n",calls,Mode());
    xilinx_ip_xfft_v9_1_destroy_state(state);
  }
};
}
extern "C" {
void __real_fft_execute(fft_plan);
void __wrap_fft_execute(fft_plan p) {
  const int mode = Mode();
  if (!mode || (p.n != 1024 && p.n != 2048) ||
      (mode == 1 && !stage) || (mode == 2 && stage) || (mode == 4 && stage != 4)) {
    __real_fft_execute(p); return;
  }
  static Model m;
  std::lock_guard<std::mutex> lock(m.mutex);
  const bool real_in = p.c_in == NULL, real_out = p.c_out == NULL;
  for (int i=0;i<p.n;++i) {
    if (real_in) { m.re[i]=float(p.in[i]); m.im[i]=0; }
    else if (real_out && i>p.n/2) {
      m.re[i]=float(p.c_in[p.n-i][0]); m.im[i]=float(-p.c_in[p.n-i][1]);
    } else { m.re[i]=float(p.c_in[i][0]); m.im[i]=float(p.c_in[i][1]); }
    if (!real_in && !real_out) m.im[i]=-m.im[i];
  }
  // WORLD real transforms ignore the imaginary parts of DC and Nyquist.
  if (real_out) m.im[0]=m.im[p.n/2]=0;
  int scaling[6]={0};
  xilinx_ip_xfft_v9_1_inputs in = {p.n==1024?10:11,m.re,p.n,m.im,p.n,scaling,6,p.sign==FFT_FORWARD?1:0};
  xilinx_ip_xfft_v9_1_outputs out = {m.out_re,p.n,m.out_im,p.n,0,0};
  if (xilinx_ip_xfft_v9_1_bitacc_simulate(m.state,in,&out)) std::abort();
  ++m.calls;
  if (real_out) for(int i=0;i<p.n;++i) p.out[i]=m.out_re[i];
  else for(int i=0;i<(real_in?p.n/2+1:p.n);++i) {
    p.c_out[i][0]=m.out_re[i]; p.c_out[i][1]=m.out_im[i];
  }
  if (real_in) p.c_out[0][1]=p.c_out[p.n/2][1]=0;
}
void __real_Dio(const double*,int,int,const DioOption*,double*,double*);
void __wrap_Dio(const double*x,int n,int fs,const DioOption*o,double*t,double*f) {
  Scope s(1); __real_Dio(x,n,fs,o,t,f);
}
void __real_StoneMask(const double*,int,int,const double*,const double*,int,double*);
void __wrap_StoneMask(const double*x,int n,int fs,const double*t,const double*f,int count,double*r) {
  Scope s(2); __real_StoneMask(x,n,fs,t,f,count,r);
}
void __real_CheapTrick(const double*,int,int,const double*,const double*,int,const CheapTrickOption*,double**);
void __wrap_CheapTrick(const double*x,int n,int fs,const double*t,const double*f,int count,const CheapTrickOption*o,double**r) {
  Scope s(3); __real_CheapTrick(x,n,fs,t,f,count,o,r);
}
void __real_D4C(const double*,int,int,const double*,const double*,int,int,const D4COption*,double**);
void __wrap_D4C(const double*x,int n,int fs,const double*t,const double*f,int count,int fft,const D4COption*o,double**r) {
  Scope s(4); __real_D4C(x,n,fs,t,f,count,fft,o,r);
}
}
