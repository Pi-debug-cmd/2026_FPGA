/* Two-core streaming inference: encoder and decoder work on adjacent chunks. */
#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L
#include "llvc_runtime.h"
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum { CAPACITY=4, NEED=224, BLOCK=240, FRONT=32 };
typedef struct { llvc_features_t features; size_t take; } slot_t;
typedef struct {
    llvc_t decoder;
    slot_t *slots;
    pthread_mutex_t lock;
    pthread_cond_t available,free_slot;
    unsigned head,tail,count;
    int done,error;
    size_t output_samples;
    double front_seconds,back_seconds,front_max,back_max;
    size_t front_calls,back_calls;
    int pin_mode;
} pipeline_t;

static double now_seconds(void){struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);
    return (double)ts.tv_sec+(double)ts.tv_nsec*1e-9;}
static void pin_this_thread(int cpu){
    cpu_set_t mask;CPU_ZERO(&mask);CPU_SET(cpu,&mask);
    if(pthread_setaffinity_np(pthread_self(),sizeof(mask),&mask))
        fprintf(stderr,"warning: CPU affinity %d failed\n",cpu);
}

static void *decoder_thread(void *opaque){
    pipeline_t *p=(pipeline_t*)opaque;
    if(p->pin_mode)pin_this_thread(p->pin_mode==1?1:0);
    float output[208];
    for(;;){
        pthread_mutex_lock(&p->lock);
        while(!p->count&&!p->done)pthread_cond_wait(&p->available,&p->lock);
        if(!p->count){pthread_mutex_unlock(&p->lock);break;}
        slot_t *slot=&p->slots[p->head];
        pthread_mutex_unlock(&p->lock);
        double begin=now_seconds();
        llvc_process_back(&p->decoder,&slot->features,output);
        double duration=now_seconds()-begin;
        p->back_seconds+=duration;p->back_calls++;
        if(duration>p->back_max)p->back_max=duration;
        size_t written=fwrite(output,sizeof(float),slot->take,stdout);
        fflush(stdout);
        pthread_mutex_lock(&p->lock);
        p->output_samples+=written;
        if(written!=slot->take)p->error=1;
        p->head=(p->head+1)%CAPACITY;
        p->count--;
        pthread_cond_signal(&p->free_slot);
        int error=p->error;
        pthread_mutex_unlock(&p->lock);
        if(error)break;
    }
    return NULL;
}

static int encode_and_queue(pipeline_t *p,llvc_t *encoder,
                            const float *block,size_t take){
    pthread_mutex_lock(&p->lock);
    while(p->count==CAPACITY&&!p->error)
        pthread_cond_wait(&p->free_slot,&p->lock);
    if(p->error){pthread_mutex_unlock(&p->lock);return 1;}
    slot_t *slot=&p->slots[p->tail];
    pthread_mutex_unlock(&p->lock);
    double begin=now_seconds();
    llvc_process_front(encoder,block,&slot->features);
    double duration=now_seconds()-begin;
    p->front_seconds+=duration;p->front_calls++;
    if(duration>p->front_max)p->front_max=duration;
    slot->take=take;
    pthread_mutex_lock(&p->lock);
    p->tail=(p->tail+1)%CAPACITY;
    p->count++;
    pthread_cond_signal(&p->available);
    pthread_mutex_unlock(&p->lock);
    return 0;
}

int main(int argc,char **argv){
    if(argc!=2){fprintf(stderr,"usage: %s model.bin\n",argv[0]);return 2;}
    llvc_t encoder;
    if(llvc_load(&encoder,argv[1]))return 3;
    pipeline_t p={0};
    const char *pin=getenv("LLVC_PIN");
    p.pin_mode=pin?atoi(pin):0;
    p.decoder=encoder; /* immutable weights shared; encoder/decoder scratch are disjoint. */
    p.slots=calloc(CAPACITY,sizeof(slot_t));
    if(!p.slots)return 4;
    pthread_mutex_init(&p.lock,NULL);
    pthread_cond_init(&p.available,NULL);
    pthread_cond_init(&p.free_slot,NULL);
    setvbuf(stdout,NULL,_IONBF,0);
    pthread_t worker;
    if(pthread_create(&worker,NULL,decoder_thread,&p)){perror("pthread_create");return 5;}
    if(p.pin_mode)pin_this_thread(p.pin_mode==1?0:1);

    float pending[NEED]={0},front[FRONT]={0},block[BLOCK];
    size_t plen=0,total_in=0,total_out=0;
    int eof=0,failed=0;
    double started=now_seconds();
    for(;;){
        while(!eof&&plen<NEED){
            size_t want=NEED-plen;
            size_t got=fread(pending+plen,sizeof(float),want,stdin);
            plen+=got;total_in+=got;
            if(got<want){
                if(ferror(stdin)){perror("stdin");failed=1;}
                eof=1;
            }
        }
        if(!eof&&plen>=NEED){
            memcpy(block,front,FRONT*sizeof(float));
            memcpy(block+FRONT,pending+16,208*sizeof(float));
            if(encode_and_queue(&p,&encoder,block,208)){failed=1;break;}
            total_out+=208;
            memcpy(front,block+FRONT+176,FRONT*sizeof(float));
            memmove(pending,pending+208,(plen-208)*sizeof(float));
            plen-=208;
        }else if(eof&&total_out<total_in){
            memset(pending+plen,0,(NEED-plen)*sizeof(float));
            plen=NEED;
            memcpy(block,front,FRONT*sizeof(float));
            memcpy(block+FRONT,pending+16,208*sizeof(float));
            size_t take=total_in-total_out;
            if(take>208)take=208;
            if(encode_and_queue(&p,&encoder,block,take)){failed=1;break;}
            total_out+=take;
            memcpy(front,block+FRONT+176,FRONT*sizeof(float));
            memmove(pending,pending+208,(plen-208)*sizeof(float));
            plen-=208;
        }else break;
    }
    pthread_mutex_lock(&p.lock);
    p.done=1;
    pthread_cond_signal(&p.available);
    pthread_mutex_unlock(&p.lock);
    pthread_join(worker,NULL);
    double elapsed=now_seconds()-started;
    fprintf(stderr,"pipeline input_samples=%zu output_samples=%zu wall_s=%.3f audio_s=%.3f realtime_factor=%.3f\n",
            total_in,p.output_samples,elapsed,total_in/16000.0,
            total_in?elapsed/(total_in/16000.0):0.0);
    fprintf(stderr,"pipeline front_ms=%.3f front_max_ms=%.3f back_ms=%.3f back_max_ms=%.3f pin_mode=%d\n",
            p.front_calls?1000*p.front_seconds/p.front_calls:0.0,1000*p.front_max,
            p.back_calls?1000*p.back_seconds/p.back_calls:0.0,1000*p.back_max,p.pin_mode);
    return failed||p.error||total_in!=p.output_samples?1:0;
}
