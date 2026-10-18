#include "fargan_mapper_v8.h"
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#endif
static double now_ms(void){
#ifdef _WIN32
 LARGE_INTEGER c,f;QueryPerformanceCounter(&c);QueryPerformanceFrequency(&f);return 1000.*c.QuadPart/f.QuadPart;
#else
 struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return 1000.*t.tv_sec+t.tv_nsec/1e6;
#endif
}
int main(int argc,char **argv){
 if(argc!=5)return 2;OwnMapperV8 model;if(!fm8_load(&model,argv[1]))return 3;
 FILE *f=fopen(argv[2],"rb"),*o=fopen(argv[3],"wb");if(!f||!o)return 4;
 float input[20],output[20];unsigned frames=0;double total=0,max=0;
 while(fread(input,4,20,f)==20){for(int j=0;j<20;j++)if(!isfinite(input[j]))return 5;double start=now_ms();fm8_frame(&model,input,output);double t=now_ms()-start;total+=t;if(t>max)max=t;for(int j=0;j<20;j++)if(!isfinite(output[j]))return 6;fwrite(output,4,20,o);frames++;}
 fclose(f);fclose(o);FILE *r=fopen(argv[4],"w");if(!r)return 7;
 fprintf(r,"{\"frames\":%u,\"mean_frame_ms\":%.6f,\"max_frame_ms\":%.6f,\"causal\":true,\"source_enrollment\":false,\"quality_accepted\":false}\n",frames,total/(frames?frames:1),max);fclose(r);return 0;
}
