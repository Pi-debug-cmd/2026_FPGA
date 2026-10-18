/* Causal160-sample pipeline. Native int8 FARGAN + own float GRU mapper.
 * Copyright/licenses of Xiph core remain in the bundled reference sources.
 * No source waveform mix, text synthesis, enrollment or PC inference. */
#include "fargan_mapper.h"
#include "lpcnet.h"
#include "fargan.h"
#include <time.h>
#include <signal.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#include <fcntl.h>
#endif
static volatile sig_atomic_t running=1;
static double meter_input_sum=0,meter_output_sum=0;
static float meter_input_peak=0,meter_output_peak=0;
static unsigned meter_input_n=0,meter_output_n=0,meter_input_clips=0,meter_output_clips=0;
static void stopped(int s){(void)s;running=0;}
static double now_ms(void){
#ifdef _WIN32
 LARGE_INTEGER c,f;QueryPerformanceCounter(&c);QueryPerformanceFrequency(&f);return 1000.*c.QuadPart/f.QuadPart;
#else
 struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return 1000.*t.tv_sec+t.tv_nsec/1e6;
#endif
}
static void stats(const char *path,unsigned frames,unsigned output,double total,double max,unsigned missed,int finished){
 char tmp[1024];snprintf(tmp,sizeof(tmp),"%s.tmp",path);FILE *f=fopen(tmp,"w");if(!f)return;
 fprintf(f,"{\"frames\":%u,\"input_samples\":%u,\"output_samples\":%u,\"mean_compute_ms\":%.6f,\"max_compute_ms\":%.6f,\"compute_deadlines_missed\":%u,\"frame_audio_ms\":10,\"format\":\"S16_LE_mono_16000\",\"finished\":%s,\"raw_waveform_mix\":false,\"source_enrollment\":false,\"target_quality_accepted\":false,\"acoustic_latency_measured\":false,\"meter_window_input\":{\"rms\":%.6f,\"peak\":%.6f,\"samples\":%u,\"clips\":%u},\"meter_window_output\":{\"rms\":%.6f,\"peak\":%.6f,\"samples\":%u,\"clips\":%u}}\n",frames,frames*160,output,total/(frames?frames:1),max,missed,finished?"true":"false",sqrt(meter_input_sum/(meter_input_n?meter_input_n:1)),meter_input_peak,meter_input_n,meter_input_clips,sqrt(meter_output_sum/(meter_output_n?meter_output_n:1)),meter_output_peak,meter_output_n,meter_output_clips);fclose(f);
#ifdef _WIN32
 remove(path);
#endif
 rename(tmp,path);
 meter_input_sum=meter_output_sum=0;meter_input_peak=meter_output_peak=0;meter_input_n=meter_output_n=meter_input_clips=meter_output_clips=0;
}
static int write_pcm(float *pcm,int at,int count,unsigned *output){
 short block[160];for(int i=0;i<count;i++){float v=pcm[at+i];if(!isfinite(v))return 0;block[i]=(short)floorf(.5f+fminf(32767,fmaxf(-32767,32768*v)));float quant=block[i]/32768.f;meter_output_sum+=quant*quant;meter_output_peak=fmaxf(meter_output_peak,fabsf(quant));meter_output_n++;if(fabsf(v)>=32767/32768.f)meter_output_clips++;}
 if(fwrite(block,2,count,stdout)!=(size_t)count||fflush(stdout))return 0;*output+=count;return 1;
}
int main(int argc,char **argv){
 if(argc!=3)return 2;OwnMapper mapper;if(!fm_load(&mapper,argv[1]))return 3;
#ifdef _WIN32
 _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
 signal(SIGTERM,stopped);signal(SIGINT,stopped);setvbuf(stdout,NULL,_IONBF,0);
 LPCNetEncState *enc=lpcnet_encoder_create();FARGANState synth;fargan_init(&synth);
 short input[160];float features[NB_TOTAL_FEATURES],converted[20],startup[100],zero[320]={0},pcm[160];
 unsigned frames=0,output=0,missed=0;double total=0,max=0;int first=1,skip=80,ok=1;
 while(running&&fread(input,2,160,stdin)==160){
  for(int i=0;i<160;i++){float v=input[i]/32768.f;meter_input_sum+=v*v;meter_input_peak=fmaxf(meter_input_peak,fabsf(v));meter_input_n++;if(abs(input[i])>=32767)meter_input_clips++;}
  double start=now_ms();lpcnet_compute_single_frame_features(enc,input,features,0);fm_frame(&mapper,features,converted);
  if(first){for(int i=0;i<5;i++)memcpy(startup+i*20,converted,80);fargan_cont(&synth,zero,startup);first=0;}
  else fargan_synthesize(&synth,pcm,converted);
  double took=now_ms()-start;total+=took;if(took>max)max=took;if(took>10)missed++;frames++;
  if(frames>1){if(!write_pcm(pcm,skip,160-skip,&output)){ok=0;break;}skip=0;}
  if(frames%100==0)stats(argv[2],frames,output,total,max,missed,0);
 }
 if(running&&ok&&!first){fargan_synthesize(&synth,pcm,converted);ok=write_pcm(pcm,skip,160-skip,&output);fargan_synthesize(&synth,pcm,converted);if(ok)ok=write_pcm(pcm,80,80,&output);}
 stats(argv[2],frames,output,total,max,missed,1);lpcnet_encoder_destroy(enc);return ok?0:4;
}
