#define main original_entry
#include "native_llvc_wide192_diag120.cpp"
#undef main
int main(){
 for(size_t at=0;at<DIAG_KEEP+208;at+=208){
   int16_t x[208],y[208];for(size_t i=0;i<208;i++){x[i]=int16_t((at+i)%30000);y[i]=int16_t(-((at+i)%30000));}
   diag_read(x,208);diag_write(y,208);
 }
 int16_t look[16];for(size_t i=0;i<16;i++)look[i]=int16_t((diag_produced+i)%30000);diag_read(look,16);
 diag_dump();return 0;
}
