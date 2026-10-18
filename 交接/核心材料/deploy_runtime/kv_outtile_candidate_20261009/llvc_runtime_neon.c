// llvc_runtime_neon.c - NEON-optimized streaming LLVC inference (reduced model).
// enc 384 / 6 DCC blocks, dec 192 / 6 heads head-dim 32, chunk 13, hop 16.
#include "llvc_runtime.h"
#include "gemm_backend.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <arm_neon.h>
#ifdef LLVC_FAST_ACTIVATIONS
enum { ACT_GRID=256, ACT_SPAN=16, ACT_N=2*ACT_SPAN*ACT_GRID+1 };
static float act_tanh_table[ACT_N],act_sig_table[ACT_N];
static float act_expneg_table[ACT_SPAN*ACT_GRID+1];
static void init_activation_tables(void){
    for(unsigned i=0;i<ACT_N;++i){
        float x=(float)i/ACT_GRID-ACT_SPAN;
        act_tanh_table[i]=tanhf(x);
        act_sig_table[i]=1.0f/(1.0f+expf(-x));
        if(i<=ACT_SPAN*ACT_GRID)act_expneg_table[i]=expf(x);
    }
}
static inline float activation_lookup(const float*table,float x){
    float coordinate=(x+ACT_SPAN)*ACT_GRID;
    unsigned index=(unsigned)coordinate;
    float fraction=coordinate-index;
    return table[index]+fraction*(table[index+1]-table[index]);
}
static inline float fast_tanh(float x){
    if(x<=-ACT_SPAN)return -1.0f;
    if(x>=ACT_SPAN)return 1.0f;
    return activation_lookup(act_tanh_table,x);
}
static inline float fast_sigmoid(float x){
    if(x<=-ACT_SPAN)return 0.0f;
    if(x>=ACT_SPAN)return 1.0f;
    return activation_lookup(act_sig_table,x);
}
static inline float fast_expneg(float x){
    if(x<=-ACT_SPAN)return 0.0f;
    if(x>=0)return 1.0f;
    return activation_lookup(act_expneg_table,x);
}
#else
#define fast_tanh tanhf
static inline float fast_sigmoid(float x){return 1.0f/(1.0f+expf(-x));}
#define fast_expneg expf
#endif
#ifdef LLVC_PROFILE
#include <time.h>
double llvc_stage_seconds[8];
static double stage_now(void){struct timespec ts;clock_gettime(CLOCK_MONOTONIC,&ts);
    return (double)ts.tv_sec+(double)ts.tv_nsec*1e-9;}
#define PROFILE_BEGIN_AT(index) double stage_start=stage_now();unsigned stage_idx=(index)
#define PROFILE_TICK do{double stage_end=stage_now();llvc_stage_seconds[stage_idx++]+=stage_end-stage_start;stage_start=stage_end;}while(0)
#else
#define PROFILE_BEGIN_AT(index)
#define PROFILE_TICK do{}while(0)
#endif

const float *fa(const llvc_t *m, uint32_t idx){return m->floats+(m->hdr->float_arr_off[idx]/4);}
const uint8_t *mw(const llvc_t *m, uint32_t mi){return m->packed+m->hdr->mat_packed_off[mi];}
const float *ms(const llvc_t *m, uint32_t mi){return m->scales+(m->hdr->mat_scale_off[mi]/4);}

// ---------- layernorm (NEON), row stride = c ----------
static void layernorm(float * __restrict x,const float*g,const float*b,
                      unsigned frames,unsigned c){
    for(unsigned t=0;t<frames;++t){
        float*row=x+(size_t)t*c;
        float32x4_t vsum=vdupq_n_f32(0);
        for(unsigned i=0;i<c;i+=4) vsum=vaddq_f32(vsum,vld1q_f32(row+i));
        float mu=(vgetq_lane_f32(vsum,0)+vgetq_lane_f32(vsum,1)+
                  vgetq_lane_f32(vsum,2)+vgetq_lane_f32(vsum,3))/c;
        float32x4_t vmu=vdupq_n_f32(mu), vvar=vdupq_n_f32(0);
        for(unsigned i=0;i<c;i+=4){
            float32x4_t d=vsubq_f32(vld1q_f32(row+i),vmu);
            vvar=vmlaq_f32(vvar,d,d);
        }
        float var=(vgetq_lane_f32(vvar,0)+vgetq_lane_f32(vvar,1)+
                   vgetq_lane_f32(vvar,2)+vgetq_lane_f32(vvar,3))/c;
        float s=1.0f/sqrtf(var+1e-5f);
        float32x4_t vs=vdupq_n_f32(s);
        for(unsigned i=0;i<c;i+=4){
            float32x4_t d=vsubq_f32(vld1q_f32(row+i),vmu);
            float32x4_t y=vmlaq_f32(vld1q_f32(b+i),vmlaq_f32(vdupq_n_f32(0),d,vs),vld1q_f32(g+i));
            vst1q_f32(row+i,y);
        }
    }
}
// ---------- relu (NEON), row stride = c ----------
static void relu(float*x,unsigned frames,unsigned c){
    float32x4_t zero=vdupq_n_f32(0);
    for(unsigned t=0;t<frames;++t){float*row=x+(size_t)t*c;
        for(unsigned i=0;i<c;i+=4)vst1q_f32(row+i,vmaxq_f32(vld1q_f32(row+i),zero));}
}
// ---------- depthwise over a ring buffer (NEON), stride = c ----------
// ring has R frames; current 13 frames begin at head.
// reads current (head+t), d ago (head+t-d), 2d ago (head+t-2d) modulo R.
static void depthwise_ring(const float* __restrict ring,float* __restrict out,
                           const float*w0,const float*w1,const float*w2,const float*bias,
                           unsigned frames,unsigned c,unsigned d,
                           unsigned R,unsigned head){
    for(unsigned t=0;t<frames;++t){
        int ih=(int)head,it=(int)t,id=(int)d,iR=(int)R;
        int ic=(ih+it)%iR;
        int i1=(ih+it-id)%iR; if(i1<0)i1+=iR;
        int i2=(ih+it-2*id)%iR; if(i2<0)i2+=iR;
        const float*rc=ring+(size_t)ic*c,*r1=ring+(size_t)i1*c,*r2=ring+(size_t)i2*c;
        float*o=out+(size_t)t*c;
        for(unsigned ch=0;ch<c;ch+=4){
            float32x4_t v=vld1q_f32(bias+ch);
            // w2=current, w1=d ago, w0=2d ago
            v=vmlaq_f32(v,vld1q_f32(w2+ch),vld1q_f32(rc+ch));
            v=vmlaq_f32(v,vld1q_f32(w1+ch),vld1q_f32(r1+ch));
            v=vmlaq_f32(v,vld1q_f32(w0+ch),vld1q_f32(r2+ch));
            vst1q_f32(o+ch,v);
        }
    }
}
// per-block ring size: bl+13 = 2*2^i + 13
static inline unsigned ring_size(unsigned i){return 2u*(1u<<i)+13u;}
static unsigned ring_start_calc(unsigned i){
    unsigned s=0;for(unsigned j=0;j<i;++j)s+=ring_size(j);return s;}
static int s_ring_head[N_ENC_LAYERS];

// ---------- dense ----------
static void dense(llvc_t*m,unsigned mi,const float*in,float*out,
                  unsigned frames,unsigned in_c,unsigned out_c,
                  unsigned in_stride,unsigned out_stride,
                  const float*sw,const float*bias){
    gemm_dense_fused(mi,mw(m,mi),in,out,frames,in_c,out_c,
                     in_stride,out_stride,sw,bias);
}
// ---------- positional encoding ----------
static void add_posenc(float*x,const float*table,unsigned frames,unsigned c){
    for(unsigned i=0;i<frames*c;++i)x[i]+=table[i];
}
// ---------- attention (NEON dot products), dec stride = c ----------
static void attention(llvc_t*m,unsigned qmi,unsigned kvmi,unsigned omi,
                      const float*qin,const float*kvin,unsigned qf,unsigned kf,
                      const float*qbias,const float*kbias,const float*vbias,
                      const float*obias,float*out,
                      float*q,float*k,float*v,float*attn){
    const unsigned C=DEC_DIM, HD=NHEAD, D=HEAD_DIM;
    dense(m,qmi,qin,q,qf,C,C,C,C,ms(m,qmi),qbias);
    // yout is otherwise unused by this fused DMA backend. Its allocation is
    // large enough for 26 rows of [K,V] and belongs only to the decoder core.
    float *combined=(float*)m->yout;
    if(gemm_dense_kv_fused(kvmi,kvin,combined,kf,kbias,vbias))abort();
    for(unsigned j=0;j<kf;++j){
        memcpy(k+(size_t)j*C,combined+(size_t)j*2*C,C*sizeof(float));
        memcpy(v+(size_t)j*C,combined+(size_t)j*2*C+C,C*sizeof(float));
    }
    for(unsigned h=0;h<HD;++h){
        for(unsigned i=0;i<qf;++i){
            const float*qr=q+(size_t)i*C+h*D;
            float scores[26];
            for(unsigned j=0;j<kf;++j){
                const float*kr=k+(size_t)j*C+h*D;
                float32x4_t acc=vdupq_n_f32(0);
                for(unsigned dd=0;dd<D;dd+=4)
                    acc=vmlaq_f32(acc,vld1q_f32(qr+dd),vld1q_f32(kr+dd));
                float s=vgetq_lane_f32(acc,0)+vgetq_lane_f32(acc,1)+
                        vgetq_lane_f32(acc,2)+vgetq_lane_f32(acc,3);
                scores[j]=s/sqrtf((float)D);
            }
            float mx=scores[0];
            for(unsigned j=1;j<kf;++j)if(scores[j]>mx)mx=scores[j];
            float sum=0;
            for(unsigned j=0;j<kf;++j){scores[j]=fast_expneg(scores[j]-mx);sum+=scores[j];}
            float*ar=attn+(size_t)i*C+h*D;
            float32x4_t vacc[D/4];
            for(unsigned dd=0;dd<D;dd+=4)vacc[dd/4]=vdupq_n_f32(0);
            for(unsigned j=0;j<kf;++j){
                float32x4_t sc=vdupq_n_f32(scores[j]/sum);
                const float*vr=v+(size_t)j*C+h*D;
                for(unsigned dd=0;dd<D;dd+=4)
                    vacc[dd/4]=vmlaq_f32(vacc[dd/4],sc,vld1q_f32(vr+dd));
            }
            for(unsigned dd=0;dd<D;dd+=4)vst1q_f32(ar+dd,vacc[dd/4]);
        }
    }
    dense(m,omi,attn,out,qf,C,C,C,C,ms(m,omi),obias);
}
// ---------- load ----------
static float*newbuf(size_t frames,unsigned c){float*p=malloc(frames*c*sizeof(float));
    memset(p,0,frames*c*sizeof(float));return p;}
int llvc_load(llvc_t*m,const char*path){
#ifdef LLVC_FAST_ACTIVATIONS
    init_activation_tables();
#endif
    FILE*f=fopen(path,"rb");if(!f){perror("open");return 1;}
    fseek(f,0,SEEK_END);long fsize=ftell(f);fseek(f,0,SEEK_SET);
    uint8_t*p=malloc(fsize);if(fread(p,1,fsize,f)!=(size_t)fsize){perror("read");return 1;}
    fclose(f);m->file=p;m->hdr=(model_header_t*)p;
    if(fsize<HDR_SIZE||m->hdr->magic!=0x4C4C5643||m->hdr->version!=2||
       m->hdr->enc_dim!=ENC_DIM||m->hdr->dec_dim!=DEC_DIM||
       m->hdr->float_off>=(uint32_t)fsize||m->hdr->scale_off>=(uint32_t)fsize||
       m->hdr->packed_off>=(uint32_t)fsize){
        fputs("unsupported or corrupt reduced LLVC model\n",stderr);free(p);return 1;}
    m->floats=(const float*)(m->file+m->hdr->float_off);
    m->scales=(const float*)(m->file+m->hdr->scale_off);
    m->packed=m->file+m->hdr->packed_off;
    m->xin=malloc(26*384);m->yout=malloc(26*384*4);
    m->e=newbuf(13,ENC_DIM);m->base=newbuf(13,ENC_DIM);
    m->dccw=NULL;
    m->dccout=newbuf(13,ENC_DIM);m->pwout=newbuf(13,ENC_DIM);m->l=newbuf(13,ENC_DIM);
    m->mem=newbuf(26,DEC_DIM);m->tgt=newbuf(26,DEC_DIM);
    m->q=newbuf(26,DEC_DIM);m->cq=newbuf(26,DEC_DIM);
    m->kv=newbuf(26,DEC_DIM);m->vv=newbuf(26,ENC_DIM);
    m->attn=newbuf(13,DEC_DIM);m->decout=newbuf(13,DEC_DIM);
    m->mout=newbuf(13,ENC_DIM);m->outin=newbuf(17,ENC_DIM);
    m->cn_ctx=calloc(24,sizeof(float));
    m->enc_buf=calloc(204*ENC_DIM,4);
    m->mem_ctx=calloc(13*DEC_DIM,4);m->tgt_ctx=calloc(13*DEC_DIM,4);
    m->out_buf=calloc(4*ENC_DIM,4);
#ifdef LLVC_OUTCONV_TRANSPOSE
    m->out_w_by_tap=malloc(80*ENC_DIM*sizeof(float));
    if(!m->out_w_by_tap)return 1;
    const float*ow=fa(m,FA_OUT_CONV_W);
    for(unsigned k=0;k<80;++k)for(unsigned c=0;c<ENC_DIM;++c)
        m->out_w_by_tap[(size_t)k*ENC_DIM+c]=ow[(size_t)c*80+k];
#else
    m->out_w_by_tap=NULL;
#endif
    if(gemm_setup(m)){fputs("gemm_setup failed\n",stderr);return 1;}
    llvc_reset_state(m);return 0;}
void llvc_reset_state(llvc_t*m){
    memset(m->cn_ctx,0,24*4);memset(m->enc_buf,0,204*ENC_DIM*4);
    for(int i=0;i<N_ENC_LAYERS;++i)s_ring_head[i]=0;
    memset(m->mem_ctx,0,13*DEC_DIM*4);memset(m->tgt_ctx,0,13*DEC_DIM*4);
    memset(m->out_buf,0,4*ENC_DIM*4);}

void llvc_process_front(llvc_t*m,const float*block240,llvc_features_t*features){
    PROFILE_BEGIN_AT(0);
    float cn[240];memcpy(cn,block240,sizeof(cn));
    for(unsigned i=0;i<12;++i){const float*fw=fa(m,4*i),*fb=fa(m,4*i+1);
        const float*gw=fa(m,4*i+2),*gb=fa(m,4*i+3);float*ctx=m->cn_ctx+2*i;
        float cin[242];cin[0]=ctx[0];cin[1]=ctx[1];memcpy(cin+2,cn,240*4);
        ctx[0]=cin[240];ctx[1]=cin[241];
        for(unsigned t=0;t<240;++t){
            float f=fw[0]*cin[t]+fw[1]*cin[t+1]+fw[2]*cin[t+2]+fb[0];
            float g=gw[0]*cin[t]+gw[1]*cin[t+1]+gw[2]*cin[t+2]+gb[0];
            float r=fast_tanh(f)*fast_sigmoid(g);cn[t]=cin[t+2]+r;}}
    for(unsigned i=0;i<240;++i)cn[i]=block240[i]+cn[i];
    PROFILE_TICK;

    // in_conv: 13 x ENC_DIM x 48, NEON over k.
    const float*iw=fa(m,FA_IN_CONV_W);
    for(unsigned t=0;t<13;++t){
        float*o=m->e+(size_t)t*ENC_DIM;
        const float*cnp=cn+t*16;
        for(unsigned c=0;c<ENC_DIM;++c){
            const float*w=iw+(size_t)c*48;
            float32x4_t acc=vdupq_n_f32(0);
            for(unsigned k=0;k<48;k+=4)
                acc=vmlaq_f32(acc,vld1q_f32(w+k),vld1q_f32(cnp+k));
            float s=vgetq_lane_f32(acc,0)+vgetq_lane_f32(acc,1)+
                    vgetq_lane_f32(acc,2)+vgetq_lane_f32(acc,3);
            o[c]=s>0?s:0;
        }
    }

    memcpy(m->base,m->e,13*ENC_DIM*4);
    PROFILE_TICK;
    for(unsigned i=0;i<N_ENC_LAYERS;++i){unsigned d=1u<<i;
        unsigned base=FA_DCC_BASE+7*i;
        const float*dw=fa(m,base),*db=fa(m,base+1);
        const float*ln1w=fa(m,base+2),*ln1b=fa(m,base+3);
        const float*pb=fa(m,base+4);
        const float*ln2w=fa(m,base+5),*ln2b=fa(m,base+6);
        // transpose depthwise weights [c*3] -> w0,w1,w2
        float w0[ENC_DIM],w1[ENC_DIM],w2[ENC_DIM];
        for(unsigned c=0;c<ENC_DIM;++c){
            w0[c]=dw[c*3+0];w1[c]=dw[c*3+1];w2[c]=dw[c*3+2];}
        unsigned R=ring_size(i);unsigned head=s_ring_head[i];
        float*ring=m->enc_buf+(size_t)ring_start_calc(i)*ENC_DIM;
        for(unsigned t=0;t<13;++t)
            memcpy(ring+(size_t)((head+t)%R)*ENC_DIM,m->e+(size_t)t*ENC_DIM,ENC_DIM*4);
        depthwise_ring(ring,m->dccout,w0,w1,w2,db,13,ENC_DIM,d,R,head);
        s_ring_head[i]=(head+13)%R;
        layernorm(m->dccout,ln1w,ln1b,13,ENC_DIM);relu(m->dccout,13,ENC_DIM);
        dense(m,M_ENC0+i,m->dccout,m->pwout,13,ENC_DIM,ENC_DIM,
              ENC_DIM,ENC_DIM,ms(m,M_ENC0+i),pb);
        layernorm(m->pwout,ln2w,ln2b,13,ENC_DIM);relu(m->pwout,13,ENC_DIM);
        for(unsigned t=0;t<13;++t)for(unsigned c=0;c<ENC_DIM;++c)
            m->e[(size_t)t*ENC_DIM+c]+=m->pwout[(size_t)t*ENC_DIM+c];}
    PROFILE_TICK;

    const float*lconst=fa(m,FA_LABEL);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<ENC_DIM;++c)
        m->l[(size_t)t*ENC_DIM+c]=lconst[c]*m->e[(size_t)t*ENC_DIM+c];
    memcpy(features->e,m->e,sizeof(features->e));
    memcpy(features->base,m->base,sizeof(features->base));
    memcpy(features->l,m->l,sizeof(features->l));
    PROFILE_TICK;
}

void llvc_process_back(llvc_t*m,const llvc_features_t*features,float*out208){
    PROFILE_BEGIN_AT(3);

    // e2d 2->1 projection (encoder 384 -> decoder 192), grouped pair.
    const float*pew=fa(m,FA_PROJ_BASE),*peb=fa(m,FA_PROJ_BASE+1);
    const float*plw=fa(m,FA_PROJ_BASE+2),*plb=fa(m,FA_PROJ_BASE+3);
    for(unsigned t=0;t<13;++t){float*mr=m->mem+(size_t)t*DEC_DIM;float*tr=m->tgt+(size_t)t*DEC_DIM;
        const float*er=features->e+(size_t)t*ENC_DIM;
        const float*lr=features->l+(size_t)t*ENC_DIM;
        for(unsigned c=0;c<DEC_DIM;++c){mr[c]=pew[c*2]*er[2*c]+pew[c*2+1]*er[2*c+1];
            tr[c]=plw[c*2]*lr[2*c]+plw[c*2+1]*lr[2*c+1];}}
    for(unsigned t=0;t<13;++t){float*mr=m->mem+(size_t)t*DEC_DIM;float*tr=m->tgt+(size_t)t*DEC_DIM;
        for(unsigned c=0;c<DEC_DIM;++c){float v=mr[c]+peb[c];mr[c]=v>0?v:0;
            v=tr[c]+plb[c];tr[c]=v>0?v:0;}}

    memmove(m->mem+13*DEC_DIM,m->mem,13*DEC_DIM*4);
    for(unsigned t=0;t<13;++t){memcpy(m->mem+(size_t)t*DEC_DIM,m->mem_ctx+(size_t)t*DEC_DIM,DEC_DIM*4);
        memcpy(m->mem_ctx+(size_t)t*DEC_DIM,m->mem+(size_t)(13+t)*DEC_DIM,DEC_DIM*4);}
    memmove(m->tgt+13*DEC_DIM,m->tgt,13*DEC_DIM*4);
    for(unsigned t=0;t<13;++t){memcpy(m->tgt+(size_t)t*DEC_DIM,m->tgt_ctx+(size_t)t*DEC_DIM,DEC_DIM*4);
        memcpy(m->tgt_ctx+(size_t)t*DEC_DIM,m->tgt+(size_t)(13+t)*DEC_DIM,DEC_DIM*4);}
    add_posenc(m->mem,fa(m,FA_POSENC_26),26,DEC_DIM);
    add_posenc(m->tgt,fa(m,FA_POSENC_26),26,DEC_DIM);
    PROFILE_TICK;

    const float*sipb=fa(m,FA_TF_BASE),*sob=fa(m,FA_TF_BASE+1);
    attention(m,M_SELF_Q,M_SELF_K,M_SELF_O,m->tgt+13*DEC_DIM,m->tgt,13,26,
              sipb,sipb+DEC_DIM,sipb+2*DEC_DIM,sob,m->decout,m->q,m->kv,m->vv,m->attn);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<DEC_DIM;++c)
        m->q[(size_t)t*DEC_DIM+c]=m->tgt[(size_t)(t+13)*DEC_DIM+c]+m->decout[(size_t)t*DEC_DIM+c];
    layernorm(m->q,fa(m,FA_TF_BASE+6),fa(m,FA_TF_BASE+7),13,DEC_DIM);
    PROFILE_TICK;
    const float*cipb=fa(m,FA_TF_BASE+2),*cob=fa(m,FA_TF_BASE+3);
    attention(m,M_CROSS_Q,M_CROSS_K,M_CROSS_O,m->q,m->mem,13,26,
              cipb,cipb+DEC_DIM,cipb+2*DEC_DIM,cob,m->decout,m->cq,m->kv,m->vv,m->attn);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<DEC_DIM;++c)
        m->kv[(size_t)t*DEC_DIM+c]=m->q[(size_t)t*DEC_DIM+c]+m->decout[(size_t)t*DEC_DIM+c];
    layernorm(m->kv,fa(m,FA_TF_BASE+8),fa(m,FA_TF_BASE+9),13,DEC_DIM);
    PROFILE_TICK;
    dense(m,M_FFN1,m->kv,m->vv,13,DEC_DIM,ENC_DIM,
          DEC_DIM,ENC_DIM,ms(m,M_FFN1),fa(m,FA_TF_BASE+4));
    relu(m->vv,13,ENC_DIM);
    dense(m,M_FFN2,m->vv,m->decout,13,ENC_DIM,DEC_DIM,
          ENC_DIM,DEC_DIM,ms(m,M_FFN2),fa(m,FA_TF_BASE+5));
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<DEC_DIM;++c)
        m->attn[(size_t)t*DEC_DIM+c]=m->kv[(size_t)t*DEC_DIM+c]+m->decout[(size_t)t*DEC_DIM+c];
    layernorm(m->attn,fa(m,FA_TF_BASE+10),fa(m,FA_TF_BASE+11),13,DEC_DIM);
    PROFILE_TICK;

    // d2e 1->2 projection (decoder 192 -> encoder 384).
    const float*pdw=fa(m,FA_PROJ_BASE+4),*pdb2=fa(m,FA_PROJ_BASE+5);
    for(unsigned t=0;t<13;++t){const float*ar=m->attn+(size_t)t*DEC_DIM;float*mr=m->mout+(size_t)t*ENC_DIM;
        for(unsigned c=0;c<DEC_DIM;++c){mr[2*c]=pdw[2*c]*ar[c];mr[2*c+1]=pdw[2*c+1]*ar[c];}}
    for(unsigned t=0;t<13;++t){float*mr=m->mout+(size_t)t*ENC_DIM;
        for(unsigned c=0;c<ENC_DIM;++c){float v=mr[c]+pdb2[c];mr[c]=v>0?v:0;}}
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<ENC_DIM;++c)
        m->mout[(size_t)t*ENC_DIM+c]+=features->l[(size_t)t*ENC_DIM+c];

    memcpy(m->outin,m->out_buf,4*ENC_DIM*4);
    for(unsigned t=0;t<13;++t)for(unsigned c=0;c<ENC_DIM;++c)
        m->outin[(size_t)(t+4)*ENC_DIM+c]=features->base[(size_t)t*ENC_DIM+c]*m->mout[(size_t)t*ENC_DIM+c];
    memcpy(m->out_buf,m->outin+13*ENC_DIM,4*ENC_DIM*4);

    // out_conv: transposed conv in scatter form, channel-outer (NEON over k).
#ifdef LLVC_OUTCONV_TRANSPOSE
#ifdef LLVC_OUTCONV_TILE4
    // Four adjacent output samples use the same input frame. Reuse its NEON
    // register while accumulating four separate tap dot products.
    for(unsigned s0=0;s0<208;s0+=4){
        float32x4_t a0=vdupq_n_f32(0),a1=vdupq_n_f32(0);
        float32x4_t a2=vdupq_n_f32(0),a3=vdupq_n_f32(0);
        for(unsigned t=0;t<17;++t){
            int k=(int)s0+64-16*(int)t;
            if(k>=0&&k+3<80){
                const float*wr0=m->out_w_by_tap+(size_t)k*ENC_DIM;
                const float*wr1=wr0+ENC_DIM,*wr2=wr1+ENC_DIM,*wr3=wr2+ENC_DIM;
                const float*ir=m->outin+(size_t)t*ENC_DIM;
                for(unsigned c=0;c<ENC_DIM;c+=4){
                    float32x4_t x=vld1q_f32(ir+c);
                    a0=vmlaq_f32(a0,x,vld1q_f32(wr0+c));
                    a1=vmlaq_f32(a1,x,vld1q_f32(wr1+c));
                    a2=vmlaq_f32(a2,x,vld1q_f32(wr2+c));
                    a3=vmlaq_f32(a3,x,vld1q_f32(wr3+c));
                }
            }else{
                const float*ir=m->outin+(size_t)t*ENC_DIM;
                float32x4_t*acc[4]={&a0,&a1,&a2,&a3};
                for(unsigned lane=0;lane<4;++lane){
                    int tap=k+(int)lane;
                    if(tap<0||tap>=80)continue;
                    const float*wr=m->out_w_by_tap+(size_t)tap*ENC_DIM;
                    for(unsigned c=0;c<ENC_DIM;c+=4)
                        *acc[lane]=vmlaq_f32(*acc[lane],vld1q_f32(ir+c),vld1q_f32(wr+c));
                }
            }
        }
        float32x4_t a[4]={a0,a1,a2,a3};
        for(unsigned lane=0;lane<4;++lane){
            float z=vgetq_lane_f32(a[lane],0)+vgetq_lane_f32(a[lane],1)+
                    vgetq_lane_f32(a[lane],2)+vgetq_lane_f32(a[lane],3);
            out208[s0+lane]=fast_tanh(z);
        }
    }
#else
    for(unsigned s=0;s<208;++s){
#ifdef LLVC_OUTCONV_MULTIACC
        float32x4_t a0=vdupq_n_f32(0),a1=vdupq_n_f32(0);
        float32x4_t a2=vdupq_n_f32(0),a3=vdupq_n_f32(0);
#else
        float32x4_t vacc=vdupq_n_f32(0);
#endif
        for(unsigned t=0;t<17;++t){
            int k=(int)s+64-16*(int)t;
            if(k<0||k>=80)continue;
            const float*wr=m->out_w_by_tap+(size_t)k*ENC_DIM;
            const float*ir=m->outin+(size_t)t*ENC_DIM;
#ifdef LLVC_OUTCONV_MULTIACC
            for(unsigned c=0;c<ENC_DIM;c+=16){
                a0=vmlaq_f32(a0,vld1q_f32(ir+c),vld1q_f32(wr+c));
                a1=vmlaq_f32(a1,vld1q_f32(ir+c+4),vld1q_f32(wr+c+4));
                a2=vmlaq_f32(a2,vld1q_f32(ir+c+8),vld1q_f32(wr+c+8));
                a3=vmlaq_f32(a3,vld1q_f32(ir+c+12),vld1q_f32(wr+c+12));
            }
#else
            for(unsigned c=0;c<ENC_DIM;c+=4)
                vacc=vmlaq_f32(vacc,vld1q_f32(ir+c),vld1q_f32(wr+c));
#endif
        }
#ifdef LLVC_OUTCONV_MULTIACC
        float32x4_t vacc=vaddq_f32(vaddq_f32(a0,a1),vaddq_f32(a2,a3));
#endif
        float acc=vgetq_lane_f32(vacc,0)+vgetq_lane_f32(vacc,1)+
                  vgetq_lane_f32(vacc,2)+vgetq_lane_f32(vacc,3);
        out208[s]=fast_tanh(acc);
    }
#endif
#else
    const float*ow=fa(m,FA_OUT_CONV_W);
    float acc[208];
    memset(acc,0,sizeof(acc));
    for(unsigned c=0;c<ENC_DIM;++c){
        const float*w=ow+(size_t)c*80;
        for(unsigned t=0;t<17;++t){
            float rc=m->outin[(size_t)t*ENC_DIM+c];
            int base=(int)t*16-64;
            int k0=0,k1=79;
            if(base<0)k0=-base;
            if(base+k1>=208)k1=208-base-1;
            float*ao=acc+base+k0;
            int n=k1-k0+1;
            float32x4_t vrc=vdupq_n_f32(rc);
            for(int k=0;k+4<=n;k+=4){
                vst1q_f32(ao+k,vmlaq_f32(vld1q_f32(ao+k),vrc,vld1q_f32(w+k0+k)));
            }
            for(int k=n-(n%4);k<n;++k)ao[k]+=rc*w[k0+k];
        }
    }
    for(unsigned s=0;s<208;++s)out208[s]=fast_tanh(acc[s]);
#endif
    PROFILE_TICK;
}

void llvc_process_block(llvc_t*m,const float*block240,float*out208){
    llvc_features_t features;
    llvc_process_front(m,block240,&features);
    llvc_process_back(m,&features,out208);
}
