/* Native128x2 causal GRU mapper. Own code, compatible FMAP008 tensors. */
#ifndef OWN_FARGAN_MAPPER_V8_H
#define OWN_FARGAN_MAPPER_V8_H
#include "fargan_mapper.h"
typedef struct {
 float mean[21],std[21],pre_w[2688],pre_b[128],wi[2][49152],wh[2][49152],bi[2][384],bh[2][384],head_w[2432],head_b[19],hidden[2][128];
 float history[151],correction;int count,slot,quiet;
} OwnMapperV8;
static int fm8_load(OwnMapperV8 *m,const char *path){
 FILE *f=fopen(path,"rb");if(!f)return 0;memset(m,0,sizeof(*m));char magic[8];unsigned count;
 if(!fm_read(f,magic,8)||memcmp(magic,"FMAP008\0",8)||!fm_read(f,&count,4)||count!=14){fclose(f);return 0;}
 const char *names[]={"mean","std","pre.weight","pre.bias","gru.weight_ih_l0","gru.weight_hh_l0","gru.bias_ih_l0","gru.bias_hh_l0","gru.weight_ih_l1","gru.weight_hh_l1","gru.bias_ih_l1","gru.bias_hh_l1","head.weight","head.bias"};
 float *dest[]={m->mean,m->std,m->pre_w,m->pre_b,m->wi[0],m->wh[0],m->bi[0],m->bh[0],m->wi[1],m->wh[1],m->bi[1],m->bh[1],m->head_w,m->head_b};
 unsigned sizes[]={21,21,2688,128,49152,49152,384,384,49152,49152,384,384,2432,19};unsigned seen=0;
 for(unsigned i=0;i<count;i++){
  unsigned len,ndim,n,shape[2];char name[96];
  if(!fm_read(f,&len,4)||len>=96||!fm_read(f,name,len)||!fm_read(f,&ndim,4)||!fm_read(f,&n,4)||ndim<1||ndim>2||!fm_read(f,shape,4*ndim)){fclose(f);return 0;}name[len]=0;
  int k;for(k=0;k<14;k++)if(!strcmp(name,names[k]))break;
  if(k==14||n!=sizes[k]||(seen&(1u<<k))||!fm_read(f,dest[k],n*4)){fclose(f);return 0;}seen|=1u<<k;
  for(unsigned j=0;j<n;j++)if(!isfinite(dest[k][j])){fclose(f);return 0;}
 }
 int ok=seen==16383&&fgetc(f)==EOF;fclose(f);for(int i=0;i<21;i++)if(m->std[i]<.09999f)ok=0;return ok;
}
static void fm8_frame(OwnMapperV8 *m,const float *input,float *output){
 float x[21],norm[21],layer_input[128],next[128],ih[384],hh[384],delta[19];memcpy(x,input,80);x[20]=input[18];
 if(input[19]>.1f&&input[0]>-7){m->quiet=0;if(m->count<151)m->history[m->count++]=input[18];else{m->history[m->slot]=input[18];m->slot=(m->slot+1)%151;}}
 else if(input[19]<-.2f||input[0]<-9){if(++m->quiet>80){m->count=0;m->slot=0;}}
 float center=(float)(log2(193.13304493/62.5)-1.5),desired=0;
 if(m->count>=8){float v[151];memcpy(v,m->history,m->count*4);qsort(v,m->count,4,fm_cmp);float median=v[m->count/2];if(!(m->count%2))median=.5f*(median+v[m->count/2-1]);desired=fminf(log2f(2.2f),fmaxf(log2f(.65f),center-median));}
 m->correction+=.055f*(desired-m->correction);x[18]=fminf(1.5f,fmaxf(-1.49f,input[18]+m->correction));
 for(int i=0;i<21;i++)norm[i]=(x[i]-m->mean[i])/m->std[i];for(int i=0;i<128;i++)layer_input[i]=tanhf(fm_dot(m->pre_w+i*21,norm,21)+m->pre_b[i]);
 for(int layer=0;layer<2;layer++){
  for(int i=0;i<384;i++){ih[i]=fm_dot(m->wi[layer]+i*128,layer_input,128)+m->bi[layer][i];hh[i]=fm_dot(m->wh[layer]+i*128,m->hidden[layer],128)+m->bh[layer][i];}
  for(int i=0;i<128;i++){float r=fm_sigmoid(ih[i]+hh[i]),z=fm_sigmoid(ih[i+128]+hh[i+128]);float n=tanhf(ih[i+256]+r*hh[i+256]);next[i]=(1-z)*n+z*m->hidden[layer][i];}
  memcpy(m->hidden[layer],next,512);memcpy(layer_input,next,512);
 }
 for(int i=0;i<19;i++)delta[i]=fm_dot(m->head_w+i*128,next,128)+m->head_b[i];memcpy(output,input,80);
 for(int i=0;i<17;i++)output[i+1]=input[i+1]+m->std[i+1]*3*tanhf(delta[i]/3);
 output[18]=fminf(1.5f,fmaxf(-1.49f,center+1.2f*tanhf(delta[17])));output[19]=fminf(.5f,fmaxf(-.5f,input[19]+.5f*tanhf(delta[18])));
}
#endif
