// Profiling runtime: same as llvc_runtime.c but accumulates per-stage time.
#include "llvc_runtime.h"
#include "gemm_backend.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

static double now_s(){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return ts.tv_sec+ts.tv_nsec*1e-9; }
double g_stage[16];   // accumulators
static int stage_prev;
static double stage_t;
static void TICK(int s){ double t=now_s(); g_stage[s-1]+=t-stage_t; stage_t=t; }
static const char* stage_names[16]={
  "convnet_pre","in_conv","dcc_enc","label","proj_e2d","decoder_ctx",
  "self_attn","cross_attn","ffn","proj_d2e","outin_mul","out_conv",
  "gemm_total","","",""};

const float *fa(const llvc_t *m, uint32_t idx){return m->floats+(m->hdr->float_arr_off[idx]/4);}
const uint8_t *mw(const llvc_t *m, uint32_t mi){return m->packed+m->hdr->mat_packed_off[mi];}
const float *ms(const llvc_t *m, uint32_t mi){return m->scales+(m->hdr->mat_scale_off[mi]/4);}

static void layernorm(float*x,const float*g,const float*b,unsigned frames,unsigned c){
    for(unsigned t=0;t<frames;++t){float*row=x+(size_t)t*512;float mu=0;
        for(unsigned i=0;i<c;++i)mu+=row[i];mu/=c;float var=0;
        for(unsigned i=0;i<c;++i){float d=row[i]-mu;var+=d*d;}var/=c;
        float s=1.0f/sqrtf(var+1e-5f);
        for(unsigned i=0;i<c;++i)row[i]=g[i]*(row[i]-mu)*s+b[i];}}
static void relu(float*x,unsigned frames,unsigned c){
    for(unsigned t=0;t<frames;++t){float*row=x+(size_t)t*512;
        for(unsigned i=0;i<c;++i)if(row[i]<0)row[i]=0;}}
static void depthwise(const float*in,float*out,const float*w,const float*bias,
                      unsigned frames,unsigned c,unsigned d){
    for(unsigned t=0;t<frames;++t){const float*r0=in+(size_t)t*512;
        const float*r1=in+(size_t)(t+d)*512;const float*r2=in+(size_t)(t+2*d)*512;
        float*o=out+(size_t)t*512;
        for(unsigned ch=0;ch<c;++ch)
            o[ch]=w[ch*3]*r0[ch]+w[ch*3+1]*r1[ch]+w[ch*3+2]*r2[ch]+bias[ch];}}
static void dense(llvc_t*m,unsigned mi,const float*in,float*out,
                  unsigned frames,unsigned in_c,unsigned out_c,
                  const float*sw,const float*bias){
    double t0=now_s();
    float sx=gemm_quantize_input(in,m->xin,frames,in_c);
    gemm_run_mi(mi,mw(m,mi),m->xin,m->yout,frames,in_c,out_c);
    g_stage[12]+=now_s()-t0;
    for(unsigned t=0;t<frames;++t){const int32_t*yr=m->yout+(size_t)t*512;
        float*o=out+(size_t)t*512;
        for(unsigned j=0;j<out_c;++j)o[j]=(float)yr[j]*sx*sw[j]+bias[j];}}
static void add_posenc(float*x,unsigned frames,unsigned c){
    for(unsigned t=0;t<frames;++t){float*row=x+(size_t)t*512;
        for(unsigned i=0;i<c;i+=2){float arg=(float)t*expf(logf(10000.0f)*-(float)i/(float)c);
            row[i]+=sinf(arg);if(i+1<c)row[i+1]+=cosf(arg);}}}
static void attention(llvc_t*m,unsigned qmi,unsigned kvmi,unsigned omi,
                      const float*qin,const float*kvin,unsigned qf,unsigned kf,
                      const float*qbias,const float*kbias,const float*vbias,
                      const float*obias,float*out,
                      float*q,float*k,float*v,float*attn){
    dense(m,qmi,qin,q,qf,256,256,ms(m,qmi),qbias);
    dense(m,kvmi,kvin,k,kf,256,256,ms(m,kvmi),kbias);
    dense(m,kvmi+1,kvin,v,kf,256,256,ms(m,kvmi+1),vbias);
    const unsigned HD=8,D=32;
    for(unsigned h=0;h<HD;++h){float scores[26];
        for(unsigned i=0;i<qf;++i){const float*qr=q+(size_t)i*512+h*D;
            for(unsigned j=0;j<kf;++j){const float*kr=k+(size_t)j*512+h*D;float s=0;
                for(unsigned d=0;d<D;++d)s+=qr[d]*kr[d];scores[j]=s/sqrtf((float)D);}
            float mx=scores[0];for(unsigned j=1;j<kf;++j)if(scores[j]>mx)mx=scores[j];
            float sum=0;for(unsigned j=0;j<kf;++j){scores[j]=expf(scores[j]-mx);sum+=scores[j];}
            float*ar=attn+(size_t)i*512+h*D;
            for(unsigned d=0;d<D;++d){float val=0;
                for(unsigned j=0;j<kf;++j)val+=(scores[j]/sum)*v[(size_t)j*512+h*D+d];
                ar[d]=val;}}}
    dense(m,omi,attn,out,qf,256,256,ms(m,omi),obias);}
static float*newf(size_t frames){float*p=malloc(frames*512*sizeof(float));
    memset(p,0,frames*512*sizeof(float));return p;}
int llvc_load(llvc_t*m,const char*path){
    FILE*f=fopen(path,"rb");if(!f){perror("open");return 1;}
    fseek(f,0,SEEK_END);long fsize=ftell(f);fseek(f,0,SEEK_SET);
    uint8_t*p=malloc(fsize);if(fread(p,1,fsize,f)!=(size_t)fsize){perror("read");return 1;}
    fclose(f);m->file=p;m->hdr=(model_header_t*)p;
    m->floats=(const float*)(m->file+m->hdr->float_off);
    m->scales=(const float*)(m->file+m->hdr->scale_off);
    m->packed=m->file+m->hdr->packed_off;
    m->xin=malloc(26*512);m->yout=malloc(26*512*4);
    m->e=newf(13);m->base=newf(13);m->dccw=newf(269);m->dccout=newf(13);
    m->pwout=newf(13);m->l=newf(13);m->mem=newf(26);m->tgt=newf(26);
    m->q=newf(26);m->cq=newf(26);m->kv=newf(26);m->vv=newf(26);
    m->attn=newf(13);m->decout=newf(13);m->mout=newf(13);m->outin=newf(17);
    m->cn_ctx=calloc(24,sizeof(float));m->enc_buf=calloc(512*510,4);
    m->mem_ctx=calloc(13*256,4);m->tgt_ctx=calloc(13*256,4);m->out_buf=calloc(512*4,4);
    if(gemm_setup(m)){fputs("gemm_setup failed\n",stderr);return 1;}
    llvc_reset_state(m);return 0;}
void llvc_reset_state(llvc_t*m){
    memset(m->cn_ctx,0,24*4);memset(m->enc_buf,0,512*510*4);
    memset(m->mem_ctx,0,13*256*4);memset(m->tgt_ctx,0,13*256*4);memset(m->out_buf,0,512*4);}

void llvc_process_block(llvc_t*m,const float*block240,float*out208){
    stage_t=now_s();
    float cn[240];memcpy(cn,block240,sizeof(cn));
    for(unsigned i=0;i<12;++i){const float*fw=fa(m,4*i),*fb=fa(m,4*i+1);
        const float*gw=fa(m,4*i+2),*gb=fa(m,4*i+3);float*ctx=m->cn_ctx+2*i;
        float cin[242];cin[0]=ctx[0];cin[1]=ctx[1];memcpy(cin+2,cn,240*4);
        ctx[0]=cin[240];ctx[1]=cin[241];
        for(unsigned t=0;t<240;++t){
            float f=fw[0]*cin[t]+fw[1]*cin[t+1]+fw[2]*cin[t+2]+fb[0];
            float g=gw[0]*cin[t]+gw[1]*cin[t+1]+gw[2]*cin[t+2]+gb[0];
            float r=tanhf(f)*(1.0f/(1.0f+expf(-g)));cn[t]=cin[t+2]+r;}}
    for(unsigned i=0;i<240;++i)cn[i]=block240[i]+cn[i];
    TICK(1);
    const float*iw=fa(m,FA_IN_CONV_W);
    for(unsigned t=0;t<13;++t){float*o=m->e+(size_t)t*512;
        for(unsigned c=0;c<512;++c){float s=0;
            for(unsigned k=0;k<48;++k)s+=iw[c*48+k]*cn[t*16+k];
            o[c]=s>0?s:0;}}
    TICK(2);
    memcpy(m->base,m->e,13*512*4);
    for(unsigned i=0;i<8;++i){unsigned d=1u<<i,bl=2*d,bs=dcc_buf_start(i);
        unsigned base=FA_DCC_BASE+7*i;
        const float*dw=fa(m,base),*db=fa(m,base+1);
        const float*ln1w=fa(m,base+2),*ln1b=fa(m,base+3);
        const float*pb=fa(m,base+4);
        const float*ln2w=fa(m,base+5),*ln2b=fa(m,base+6);
        float*din=m->dccw;float*cbuf=m->enc_buf+(size_t)bs*512;
        memcpy(din,cbuf,bl*512*4);memcpy(din+(size_t)bl*512,m->e,13*512*4);
        memcpy(cbuf,din+(size_t)13*512,bl*512*4);
        depthwise(din,m->dccout,dw,db,13,512,d);
        layernorm(m->dccout,ln1w,ln1b,13,512);relu(m->dccout,13,512);
        dense(m,M_ENC0+i,m->dccout,m->pwout,13,512,512,ms(m,M_ENC0+i),pb);
        layernorm(m->pwout,ln2w,ln2b,13,512);relu(m->pwout,13,512);
        for(unsigned t=0;t<13;++t)for(unsigned c=0;c<512;++c)
            m->e[(size_t)t*512+c]+=m->pwout[(size_t)t*512+c];}
    TICK(3);
    const float*lconst=fa(m,FA_LABEL);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<512;++c)
        m->l[(size_t)t*512+c]=lconst[c]*m->e[(size_t)t*512+c];
    TICK(4);
    const float*pew=fa(m,FA_PROJ_BASE),*peb=fa(m,FA_PROJ_BASE+1);
    const float*plw=fa(m,FA_PROJ_BASE+2),*plb=fa(m,FA_PROJ_BASE+3);
    for(unsigned t=0;t<13;++t){float*mr=m->mem+(size_t)t*512;float*tr=m->tgt+(size_t)t*512;
        const float*er=m->e+(size_t)t*512;const float*lr=m->l+(size_t)t*512;
        for(unsigned c=0;c<256;++c){mr[c]=pew[c*2]*er[2*c]+pew[c*2+1]*er[2*c+1];
            tr[c]=plw[c*2]*lr[2*c]+plw[c*2+1]*lr[2*c+1];}}
    for(unsigned t=0;t<13;++t){float*mr=m->mem+(size_t)t*512;float*tr=m->tgt+(size_t)t*512;
        for(unsigned c=0;c<256;++c){float v=mr[c]+peb[c];mr[c]=v>0?v:0;
            v=tr[c]+plb[c];tr[c]=v>0?v:0;}}
    TICK(5);
    memmove(m->mem+13*512,m->mem,13*512*4);
    for(unsigned t=0;t<13;++t){memcpy(m->mem+(size_t)t*512,m->mem_ctx+(size_t)t*256,256*4);
        memcpy(m->mem_ctx+(size_t)t*256,m->mem+(size_t)(13+t)*512,256*4);}
    memmove(m->tgt+13*512,m->tgt,13*512*4);
    for(unsigned t=0;t<13;++t){memcpy(m->tgt+(size_t)t*512,m->tgt_ctx+(size_t)t*256,256*4);
        memcpy(m->tgt_ctx+(size_t)t*256,m->tgt+(size_t)(13+t)*512,256*4);}
    add_posenc(m->mem,26,256);add_posenc(m->tgt,26,256);
    const float*sipb=fa(m,FA_TF_BASE),*sob=fa(m,FA_TF_BASE+1);
    attention(m,M_SELF_Q,M_SELF_K,M_SELF_O,m->tgt+13*512,m->tgt,13,26,
              sipb,sipb+256,sipb+512,sob,m->decout,m->q,m->kv,m->vv,m->attn);
    TICK(7);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<256;++c)
        m->q[(size_t)t*512+c]=m->tgt[(size_t)(t+13)*512+c]+m->decout[(size_t)t*512+c];
    layernorm(m->q,fa(m,FA_TF_BASE+6),fa(m,FA_TF_BASE+7),13,256);
    const float*cipb=fa(m,FA_TF_BASE+2),*cob=fa(m,FA_TF_BASE+3);
    attention(m,M_CROSS_Q,M_CROSS_K,M_CROSS_O,m->q,m->mem,13,26,
              cipb,cipb+256,cipb+512,cob,m->decout,m->cq,m->kv,m->vv,m->attn);
    TICK(8);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<256;++c)
        m->kv[(size_t)t*512+c]=m->q[(size_t)t*512+c]+m->decout[(size_t)t*512+c];
    layernorm(m->kv,fa(m,FA_TF_BASE+8),fa(m,FA_TF_BASE+9),13,256);
    dense(m,M_FFN1,m->kv,m->vv,13,256,512,ms(m,M_FFN1),fa(m,FA_TF_BASE+4));
    relu(m->vv,13,512);
    dense(m,M_FFN2,m->vv,m->decout,13,512,256,ms(m,M_FFN2),fa(m,FA_TF_BASE+5));
    TICK(9);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<256;++c)
        m->attn[(size_t)t*512+c]=m->kv[(size_t)t*512+c]+m->decout[(size_t)t*512+c];
    layernorm(m->attn,fa(m,FA_TF_BASE+10),fa(m,FA_TF_BASE+11),13,256);
    const float*pdw=fa(m,FA_PROJ_BASE+4),*pdb2=fa(m,FA_PROJ_BASE+5);
    for(unsigned t=0;t<13;++t){const float*ar=m->attn+(size_t)t*512;float*mr=m->mout+(size_t)t*512;
        for(unsigned c=0;c<256;++c){mr[2*c]=pdw[2*c]*ar[c];mr[2*c+1]=pdw[2*c+1]*ar[c];}}
    for(unsigned t=0;t<13;++t){float*mr=m->mout+(size_t)t*512;
        for(unsigned c=0;c<512;++c){float v=mr[c]+pdb2[c];mr[c]=v>0?v:0;}}
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<512;++c)
        m->mout[(size_t)t*512+c]+=m->l[(size_t)t*512+c];
    TICK(10);
    memcpy(m->outin,m->out_buf,4*512*4);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<512;++c)
        m->outin[(size_t)(t+4)*512+c]=m->base[(size_t)t*512+c]*m->mout[(size_t)t*512+c];
    memcpy(m->out_buf,m->outin+13*512,4*512*4);
    TICK(11);
    const float*ow=fa(m,FA_OUT_CONV_W);
    for(unsigned s=0;s<208;++s){float acc=0;
        for(unsigned t=0;t<17;++t){int k=(int)s+64-16*(int)t;
            if(k>=0&&k<80){const float*r=m->outin+(size_t)t*512;
                for(unsigned c=0;c<512;++c)acc+=ow[(size_t)c*80+k]*r[c];}}
        out208[s]=tanhf(acc);}
    TICK(12);
}
