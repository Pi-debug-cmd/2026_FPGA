/* Own causal mapper, float weights exported from PyTorch. No enrollment. */
#ifndef OWN_FARGAN_MAPPER_H
#define OWN_FARGAN_MAPPER_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#ifdef __ARM_NEON
#include <arm_neon.h>
#endif
typedef struct {
 float mean[21],std[21],pre_w[1344],pre_b[64],wi[12288],wh[12288],bi[192],bh[192],head_w[1152],head_b[18];
 float hidden[64],pitch_history[151],pitch_correction;
 int pitch_count,pitch_slot,quiet,input_dim;
} OwnMapper;
static int fm_read(FILE *f,void *p,size_t n){return fread(p,1,n,f)==n;}
static int fm_load(OwnMapper *m,const char *path){
 FILE *f=fopen(path,"rb");if(!f)return 0;memset(m,0,sizeof(*m));char magic[8];unsigned count;
 if(!fm_read(f,magic,8)||(!(!memcmp(magic,"FMAP006\0",8)||!memcmp(magic,"FMAP007\0",8)))||!fm_read(f,&count,4)||count!=10){fclose(f);return 0;}
 m->input_dim=magic[6]=='7'?21:20;
 const char *names[]={"mean","std","pre.weight","pre.bias","gru.weight_ih_l0","gru.weight_hh_l0","gru.bias_ih_l0","gru.bias_hh_l0","head.weight","head.bias"};
 float *dest[]={m->mean,m->std,m->pre_w,m->pre_b,m->wi,m->wh,m->bi,m->bh,m->head_w,m->head_b};
 unsigned sizes[]={20,20,1280,64,12288,12288,192,192,1152,18};sizes[0]=sizes[1]=m->input_dim;sizes[2]=m->input_dim*64;unsigned seen=0;
 for(unsigned i=0;i<count;i++){
  unsigned len,ndim,n,shape[2];char name[96];
  if(!fm_read(f,&len,4)||len>=96||!fm_read(f,name,len)||!fm_read(f,&ndim,4)||!fm_read(f,&n,4)||ndim<1||ndim>2||!fm_read(f,shape,4*ndim)){fclose(f);return 0;}name[len]=0;
  int k;for(k=0;k<10;k++)if(!strcmp(name,names[k]))break;
  if(k==10||n!=sizes[k]||(seen&(1u<<k))||!fm_read(f,dest[k],n*4)){fclose(f);return 0;}seen|=1u<<k;
  for(unsigned j=0;j<n;j++)if(!isfinite(dest[k][j])){fclose(f);return 0;}
 }
 int ok=seen==1023&&fgetc(f)==EOF;fclose(f);
 for(int j=0;j<m->input_dim;j++)if(m->std[j]<.09999f)ok=0;
 return ok;
}
static float fm_dot(const float *a,const float *b,int n){
#ifdef __ARM_NEON
 float32x4_t sum=vdupq_n_f32(0);int i=0;for(;i+4<=n;i+=4)sum=vmlaq_f32(sum,vld1q_f32(a+i),vld1q_f32(b+i));
 float32x2_t s=vadd_f32(vget_low_f32(sum),vget_high_f32(sum));float total=vget_lane_f32(vpadd_f32(s,s),0);for(;i<n;i++)total+=a[i]*b[i];return total;
#else
 float s=0;for(int i=0;i<n;i++)s+=a[i]*b[i];return s;
#endif
}
static float fm_sigmoid(float x){return 1/(1+expf(-x));}
static int fm_cmp(const void *a,const void *b){float x=*(const float*)a,y=*(const float*)b;return (x>y)-(x<y);}
static void fm_frame(OwnMapper *m,const float *input,float *output){
 float x[20],z[64],ih[192],hh[192],next[64],delta[18];memcpy(x,input,80);
 if(input[19]>.1f&&input[0]>-7){m->quiet=0;if(m->pitch_count<151)m->pitch_history[m->pitch_count++]=input[18];else{m->pitch_history[m->pitch_slot]=input[18];m->pitch_slot=(m->pitch_slot+1)%151;}}
 else if(input[19]<-.2f||input[0]<-9){if(++m->quiet>80){m->pitch_count=0;m->pitch_slot=0;}}
 float desired=0;
 if(m->pitch_count>=8){float v[151];memcpy(v,m->pitch_history,m->pitch_count*4);qsort(v,m->pitch_count,4,fm_cmp);float median=v[m->pitch_count/2];if(!(m->pitch_count%2))median=.5f*(median+v[m->pitch_count/2-1]);
  desired=fminf(log2f(2.2f),fmaxf(log2f(.65f),(float)(log2(193.13304493/62.5)-1.5)-median));}
 m->pitch_correction+=.055f*(desired-m->pitch_correction);x[18]=fminf(1.5f,fmaxf(-1.49f,input[18]+m->pitch_correction));
 float norm[21];for(int j=0;j<20;j++)norm[j]=(x[j]-m->mean[j])/m->std[j];if(m->input_dim==21)norm[20]=(input[18]-m->mean[20])/m->std[20];
 for(int j=0;j<64;j++)z[j]=tanhf(fm_dot(m->pre_w+j*m->input_dim,norm,m->input_dim)+m->pre_b[j]);
 for(int j=0;j<192;j++){ih[j]=fm_dot(m->wi+j*64,z,64)+m->bi[j];hh[j]=fm_dot(m->wh+j*64,m->hidden,64)+m->bh[j];}
 for(int j=0;j<64;j++){float r=fm_sigmoid(ih[j]+hh[j]),gate=fm_sigmoid(ih[j+64]+hh[j+64]);float n=tanhf(ih[j+128]+r*hh[j+128]);next[j]=(1-gate)*n+gate*m->hidden[j];}
 memcpy(m->hidden,next,256);for(int j=0;j<18;j++)delta[j]=fm_dot(m->head_w+j*64,next,64)+m->head_b[j];
 memcpy(output,x,80);for(int j=0;j<17;j++)output[j+1]=x[j+1]+m->std[j+1]*3*tanhf(delta[j]/3);
 output[18]=fminf(1.5f,fmaxf(-1.49f,x[18]+.4f*tanhf(delta[17])));
}
#endif
