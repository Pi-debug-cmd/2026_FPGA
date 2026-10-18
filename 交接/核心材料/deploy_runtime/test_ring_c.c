// test_ring_c.c - compare ring depthwise vs linear depthwise for one block
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <arm_neon.h>

static void dw_linear(const float*in,float*out,const float*w,const float*bias,
                      unsigned frames,unsigned c,unsigned d){
    for(unsigned t=0;t<frames;++t){
        const float*r0=in+(size_t)t*512,*r1=in+(size_t)(t+d)*512,*r2=in+(size_t)(t+2*d)*512;
        float*o=out+(size_t)t*512;
        for(unsigned ch=0;ch<c;ch+=4){
            float32x4_t v=vld1q_f32(bias+ch);
            for(int e=0;e<4;++e){unsigned cc=ch+e;
                float val=w[cc*3]*r0[cc]+w[cc*3+1]*r1[cc]+w[cc*3+2]*r2[cc];
                v=vsetq_lane_f32(vgetq_lane_f32(v,e)+val,v,e);}
            vst1q_f32(o+ch,v);}
    }
}
static void dw_ring(const float*ring,float*out,const float*w,const float*bias,
                    unsigned frames,unsigned c,unsigned d,unsigned R,unsigned head){
    for(unsigned t=0;t<frames;++t){
        int ih=(int)head,it=(int)t,id=(int)d,iR=(int)R;
        int ic=(ih+it)%iR,i1=(ih+it-id)%iR;if(i1<0)i1+=iR;
        int i2=(ih+it-2*id)%iR;if(i2<0)i2+=iR;
        const float*rc=ring+(size_t)ic*512,*r1=ring+(size_t)i1*512,*r2=ring+(size_t)i2*512;
        if(t==0&&d==1)printf("   inside: ic=%d i1=%d i2=%d rc=%.5f r1=%.5f r2=%.5f\n",
            ic,i1,i2,rc[0],r1[0],r2[0]);
        float*o=out+(size_t)t*512;
        for(unsigned ch=0;ch<c;ch+=4){
            float32x4_t v=vld1q_f32(bias+ch);
            for(int e=0;e<4;++e){unsigned cc=ch+e;
                float val=w[cc*3+2]*rc[cc]+w[cc*3+1]*r1[cc]+w[cc*3]*r2[cc];
                v=vsetq_lane_f32(vgetq_lane_f32(v,e)+val,v,e);}
            vst1q_f32(o+ch,v);}
    }
}
int main(){
    setbuf(stdout,NULL);
    srand(123);
    unsigned nchunks=60;
    for(unsigned bi=0;bi<8;++bi){
        unsigned d=1u<<bi,bl=2*d,R=bl+13;
        float*w=malloc(512*3*4),*bias=malloc(512*4);
        for(unsigned i=0;i<512*3;++i)w[i]=(rand()%200-100)/1000.0f;
        for(unsigned i=0;i<512;++i)bias[i]=(rand()%200-100)/1000.0f;
        // linear
        float*cbuf=calloc(bl*512,4);
        float*din=malloc((bl+13)*512*4);
        float*ol=malloc(13*512*4);
        // ring
        float*ring=calloc(R*512,4);
        float*orr=malloc(13*512*4);
        unsigned head=0;
        float maxd=0;
        int dbg=0;
        for(unsigned c=0;c<nchunks;++c){
            float cur[13*512];
            for(unsigned i=0;i<13*512;++i)cur[i]=(rand()%200-100)/1000.0f;
            if(c==0){
                printf("   ch0 w0=%.5f w1=%.5f w2=%.5f cur0=%.5f bias0=%.5f\n",
                    w[0],w[1],w[2],cur[0],bias[0]);
                printf("   manual lin=%.5f\n",w[0]*0+w[1]*0+w[2]*cur[0]+bias[0]);
                printf("   manual ring=%.5f\n",w[2]*cur[0]+w[1]*0+w[0]*0+bias[0]);
            }
            // linear
            memcpy(din,cbuf,bl*512*4);
            memcpy(din+(size_t)bl*512,cur,13*512*4);
            dw_linear(din,ol,w,bias,13,512,d);
            memcpy(cbuf,din+(size_t)13*512,bl*512*4);
            // ring
            for(unsigned t=0;t<13;++t)
                memcpy(ring+(size_t)((head+t)%R)*512,cur+t*512,512*4);
            if(c==0)printf("   ring[cur0]=%.5f ring[13*512]=%.5f ring[14*512]=%.5f\n",
                    ring[0],ring[13*512],ring[14*512]);
            dw_ring(ring,orr,w,bias,13,512,d,R,head);
            head=(head+13)%R;
            for(unsigned i=0;i<13*512;++i){float dd=fabsf(ol[i]-orr[i]);if(dd>maxd){maxd=dd;
                if(!dbg&&dd>1e-3){dbg=1;
                    printf("   first at chunk%u frame%u ch%u lin=%.5f ring=%.5f\n",c,i/512,i%512,ol[i],orr[i]);}}}
        }
        printf("d=%3d R=%3d maxdiff=%.5f %s\n",d,R,maxd,maxd<1e-4?"OK":"MISMATCH");
        free(w);free(bias);free(cbuf);free(din);free(ol);free(ring);free(orr);
    }
    return 0;
}
