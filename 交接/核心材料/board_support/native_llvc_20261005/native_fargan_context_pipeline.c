/* Two-core bounded pipeline. Own mapper + unchanged Xiph int8 FARGAN.
 * Feature mapping and synthesis states are separately owned by their threads.
 * At most two pending feature frames; no source/reference waveform bypass. */
#define _GNU_SOURCE
#include "fargan_mapper_context.h"
#include "lpcnet.h"
#include "fargan.h"
#include <pthread.h>
#include <time.h>
#include <signal.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#include <fcntl.h>
#else
#include <sched.h>
#include <unistd.h>
#endif
static double now_ms(void){
#ifdef _WIN32
 LARGE_INTEGER c,f;QueryPerformanceCounter(&c);QueryPerformanceFrequency(&f);return 1000.*c.QuadPart/f.QuadPart;
#else
 struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return 1000.*t.tv_sec+t.tv_nsec/1e6;
#endif
}
static volatile sig_atomic_t running=1;
static void interrupted(int s){(void)s;running=0;}
typedef struct {
 pthread_mutex_t queue_lock,meter_lock;pthread_cond_t not_empty,not_full;
 float queue[2][20];int head,tail,pending,eof,failed;
 unsigned produced,consumed,output,producer_missed,consumer_missed;
 double producer_total,consumer_total,producer_max,consumer_max,begin,input_sum,output_sum;
 unsigned input_n,output_n,input_clips,output_clips;float input_peak,output_peak;
 const char *status_path;
} Pipeline;
static void pin_core(int core){
#ifndef _WIN32
 cpu_set_t cpus;CPU_ZERO(&cpus);CPU_SET(core,&cpus);int ret=pthread_setaffinity_np(pthread_self(),sizeof(cpus),&cpus);if(ret)fprintf(stderr,"CPU_AFFINITY_FAILED core=%d code=%d\n",core,ret);
#else
 (void)core;
#endif
}
static void write_status(Pipeline *p,int finished){
 char tmp[1024];snprintf(tmp,sizeof(tmp),"%s.tmp",p->status_path);FILE *f=fopen(tmp,"w");if(!f)return;
 pthread_mutex_lock(&p->meter_lock);double a=p->producer_total/(p->produced?p->produced:1),b=p->consumer_total/(p->consumed?p->consumed:1);
 fprintf(f,"{\"frames\":%u,\"producer_frames\":%u,\"input_samples\":%u,\"output_samples\":%u,\"mean_compute_ms\":%.6f,\"max_compute_ms\":%.6f,\"analysis_mapper_mean_ms\":%.6f,\"vocoder_mean_ms\":%.6f,\"serial_compute_sum_mean_ms\":%.6f,\"compute_deadlines_missed\":%u,\"producer_deadlines_missed\":%u,\"vocoder_deadlines_missed\":%u,\"wall_elapsed_ms\":%.6f,\"frame_audio_ms\":10,\"pipeline_threads\":2,\"max_pending_frames\":2,\"finished\":%s,\"raw_waveform_mix\":false,\"source_enrollment\":false,\"target_quality_accepted\":false,\"acoustic_latency_measured\":false,\"meter_window_input\":{\"rms\":%.6f,\"peak\":%.6f,\"samples\":%u,\"clips\":%u},\"meter_window_output\":{\"rms\":%.6f,\"peak\":%.6f,\"samples\":%u,\"clips\":%u}}\n",p->consumed,p->produced,p->produced*160,p->output,fmax(a,b),fmax(p->producer_max,p->consumer_max),a,b,a+b,p->producer_missed>p->consumer_missed?p->producer_missed:p->consumer_missed,p->producer_missed,p->consumer_missed,now_ms()-p->begin,finished?"true":"false",sqrt(p->input_sum/(p->input_n?p->input_n:1)),p->input_peak,p->input_n,p->input_clips,sqrt(p->output_sum/(p->output_n?p->output_n:1)),p->output_peak,p->output_n,p->output_clips);
 p->input_sum=p->output_sum=0;p->input_peak=p->output_peak=0;p->input_n=p->output_n=p->input_clips=p->output_clips=0;pthread_mutex_unlock(&p->meter_lock);fclose(f);
#ifdef _WIN32
 remove(p->status_path);
#endif
 rename(tmp,p->status_path);
}
static int write_pcm(Pipeline *p,float *pcm,int at,int count){
 short block[160];double sum=0;float peak=0;unsigned clips=0;
 for(int i=0;i<count;i++){float v=pcm[at+i];if(!isfinite(v))return 0;block[i]=(short)floorf(.5f+fminf(32767,fmaxf(-32767,32768*v)));float q=block[i]/32768.f;sum+=q*q;peak=fmaxf(peak,fabsf(q));if(fabsf(v)>=32767/32768.f)clips++;}
 if(fwrite(block,2,count,stdout)!=(size_t)count||fflush(stdout))return 0;
 pthread_mutex_lock(&p->meter_lock);p->output+=count;p->output_n+=count;p->output_sum+=sum;p->output_peak=fmaxf(p->output_peak,peak);p->output_clips+=clips;pthread_mutex_unlock(&p->meter_lock);return 1;
}
static void *synthesize(void *argument){
 Pipeline *p=argument;pin_core(1);FARGANState synth;fargan_init(&synth);float features[20],startup[100],zero[320]={0},pcm[160];int first=1,skip=80;
 while(1){
  pthread_mutex_lock(&p->queue_lock);while(!p->pending&&!p->eof)pthread_cond_wait(&p->not_empty,&p->queue_lock);
  if(!p->pending&&p->eof){pthread_mutex_unlock(&p->queue_lock);break;}
  memcpy(features,p->queue[p->head],80);p->head=(p->head+1)%2;p->pending--;pthread_cond_signal(&p->not_full);pthread_mutex_unlock(&p->queue_lock);
  double start=now_ms();if(first){for(int i=0;i<5;i++)memcpy(startup+i*20,features,80);fargan_cont(&synth,zero,startup);first=0;}else fargan_synthesize(&synth,pcm,features);
  double took=now_ms()-start;pthread_mutex_lock(&p->meter_lock);p->consumed++;p->consumer_total+=took;if(took>p->consumer_max)p->consumer_max=took;if(took>10)p->consumer_missed++;unsigned done=p->consumed;pthread_mutex_unlock(&p->meter_lock);
  if(done>1){if(!write_pcm(p,pcm,skip,160-skip)){pthread_mutex_lock(&p->queue_lock);p->failed=1;pthread_cond_broadcast(&p->not_full);pthread_mutex_unlock(&p->queue_lock);return NULL;}skip=0;}
  if(done%100==0)write_status(p,0);
 }
 if(running&&!p->failed&&!first){fargan_synthesize(&synth,pcm,features);int ok=write_pcm(p,pcm,skip,160-skip);fargan_synthesize(&synth,pcm,features);if(ok)ok=write_pcm(p,pcm,80,80);if(!ok)p->failed=1;}
 return NULL;
}
int main(int argc,char **argv){
 if(argc!=3)return 2;OwnMapperContext *mapper=malloc(sizeof(*mapper));if(!mapper||!fm9_load(mapper,argv[1]))return 3;
#ifdef _WIN32
 _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
 signal(SIGTERM,interrupted);signal(SIGINT,interrupted);setvbuf(stdout,NULL,_IONBF,0);pin_core(0);
 Pipeline p;memset(&p,0,sizeof(p));p.status_path=argv[2];p.begin=now_ms();pthread_mutex_init(&p.queue_lock,NULL);pthread_mutex_init(&p.meter_lock,NULL);pthread_cond_init(&p.not_empty,NULL);pthread_cond_init(&p.not_full,NULL);
 pthread_t worker;if(pthread_create(&worker,NULL,synthesize,&p))return 4;
 LPCNetEncState *enc=lpcnet_encoder_create();short input[160];float features[NB_TOTAL_FEATURES],converted[20];
 while(running&&fread(input,2,160,stdin)==160){
  double start=now_ms();lpcnet_compute_single_frame_features(enc,input,features,0);fm9_frame(mapper,features,converted);double took=now_ms()-start;
  double sum=0;float peak=0;unsigned clips=0;for(int i=0;i<160;i++){float v=input[i]/32768.f;sum+=v*v;peak=fmaxf(peak,fabsf(v));if(abs(input[i])>=32767)clips++;}
  for(int i=0;i<20;i++)if(!isfinite(converted[i])){p.failed=1;running=0;break;}
  pthread_mutex_lock(&p.meter_lock);p.produced++;p.producer_total+=took;if(took>p.producer_max)p.producer_max=took;if(took>10)p.producer_missed++;p.input_sum+=sum;p.input_peak=fmaxf(p.input_peak,peak);p.input_n+=160;p.input_clips+=clips;pthread_mutex_unlock(&p.meter_lock);
  pthread_mutex_lock(&p.queue_lock);while(p.pending==2&&!p.failed)pthread_cond_wait(&p.not_full,&p.queue_lock);
  if(p.failed){pthread_mutex_unlock(&p.queue_lock);break;}
  memcpy(p.queue[p.tail],converted,80);p.tail=(p.tail+1)%2;p.pending++;pthread_cond_signal(&p.not_empty);pthread_mutex_unlock(&p.queue_lock);
 }
 pthread_mutex_lock(&p.queue_lock);p.eof=1;pthread_cond_broadcast(&p.not_empty);pthread_mutex_unlock(&p.queue_lock);pthread_join(worker,NULL);
 write_status(&p,1);lpcnet_encoder_destroy(enc);free(mapper);return p.failed?5:0;
}
