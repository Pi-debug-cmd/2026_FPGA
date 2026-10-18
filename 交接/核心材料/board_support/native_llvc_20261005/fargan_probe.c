/* Minimal analysis/synthesis probe around unchanged Xiph FARGAN APIs.
 * Core sources and notices retained in Opus_FARGAN_reference/opus-main.
 * No target conversion or live deployment is claimed by this probe. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#endif
#include "lpcnet.h"
#include "fargan.h"
static double now_ms(void){
#ifdef _WIN32
 LARGE_INTEGER c,f;QueryPerformanceCounter(&c);QueryPerformanceFrequency(&f);return 1000.*c.QuadPart/f.QuadPart;
#else
 struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return 1000.*t.tv_sec+t.tv_nsec/1e6;
#endif
}
int main(int argc,char **argv){
 if(argc!=5)return 2;FILE *in=fopen(argv[2],"rb"),*out=fopen(argv[3],"wb");if(!in||!out)return 2;
 size_t frames=0;double total=0,max=0;int synthesis=!strcmp(argv[1],"--synthesis");
 if(!strcmp(argv[1],"--features")){
  LPCNetEncState *enc=lpcnet_encoder_create();opus_int16 pcm[160];float feats[NB_TOTAL_FEATURES];
  while(fread(pcm,2,160,in)==160){double t=now_ms();lpcnet_compute_single_frame_features(enc,pcm,feats,0);t=now_ms()-t;total+=t;if(t>max)max=t;for(int i=0;i<20;i++)if(!isfinite(feats[i]))return 3;fwrite(feats,4,20,out);frames++;}
  lpcnet_encoder_destroy(enc);
 }else if(synthesis){
  FARGANState state;float startup[5*NB_FEATURES],zero[320]={0},features[NB_FEATURES],pcm[160];opus_int16 output[160];
  fargan_init(&state);if(fread(features,4,20,in)!=20)return 3;
  for(int i=0;i<5;i++)memcpy(startup+i*20,features,80);fargan_cont(&state,zero,startup);
  int skip=80,stop=0;
  while(1){float next[20];if(fread(next,4,20,in)!=20)stop++;else memcpy(features,next,80);double t=now_ms();fargan_synthesize(&state,pcm,features);t=now_ms()-t;total+=t;if(t>max)max=t;
   for(int i=0;i<160;i++){if(!isfinite(pcm[i]))return 3;output[i]=(opus_int16)floorf(.5f+fminf(32767,fmaxf(-32767,32768*pcm[i])));}
   if(stop==2){fwrite(output+80,2,80,out);break;}fwrite(output+skip,2,160-skip,out);skip=0;frames++;
  }
 }else return 2;
 fclose(in);fclose(out);FILE *report=fopen(argv[4],"w");if(!report)return 3;
 fprintf(report,"{\"frames\":%lu,\"audio_seconds\":%.3f,\"mean_frame_ms\":%.6f,\"max_frame_ms\":%.6f,\"total_compute_ms\":%.6f,\"frame_audio_ms\":10,\"synthesis\":%s,\"target_voice_conversion\":false,\"live_verified\":false}\n",(unsigned long)frames,frames*.01,total/(frames?frames:1),max,total,synthesis?"true":"false");fclose(report);return 0;
}
