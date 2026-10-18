#define main llvc_program_main
#include "native_llvc_small128_vmath.cpp"
#undef main
int main(){double er=0,ta=0,sa=0;for(int i=0;i<=200000;i++){float x=-80.f+160.f*i/200000;float ref=std::exp(x);er=std::max(er,double(std::fabs((exp_approx(x)-ref)/ref)));float f=x/8;ta=std::max(ta,double(std::fabs(tanh_approx(f)-std::tanh(f))));sa=std::max(sa,double(std::fabs(1.f/(1.f+exp_approx(-f))-1.f/(1.f+std::exp(-f)))));}std::cout<<"{\"exp_max_relative_error\":"<<er<<",\"tanh_max_absolute_error\":"<<ta<<",\"sigmoid_max_absolute_error\":"<<sa<<"}\n";return er<2e-6 && ta<5e-7 && sa<5e-7?0:1;}
