"""Create a separate CPU optimization candidate. No model or baseline edits."""
from pathlib import Path

root=Path(__file__).resolve().parent
source=(root/'native_llvc.cpp').read_text(encoding='utf-8')
source=source.replace('#include <vector>', '#include <vector>\n#include <cstdlib>\n#include <thread>\n#include <mutex>\n#include <condition_variable>')
start=source.index('static V linear(')
end=source.index('static void relu',start)
kernel=r'''
// Output-quartet packing amortizes weight loads across four time frames.
// Cache keys reference immutable model storage, never ephemeral Q/K/V copies.
struct Packed { int in,out; V values; };
static std::map<const float*,Packed> packed_matrices;
static const V &packed(const float *w,int in,int out){
    auto it=packed_matrices.find(w);
    if(it!=packed_matrices.end()){
        if(it->second.in!=in || it->second.out!=out)throw std::runtime_error("packed shape mismatch");
        return it->second.values;
    }
    if(out%4)throw std::runtime_error("output not quartet aligned");
    Packed p;p.in=in;p.out=out;p.values.resize(in*out);
    for(int o=0;o<out;o+=4)for(int k=0;k<in;k++)for(int lane=0;lane<4;lane++)
        p.values[o*in+k*4+lane]=w[(o+lane)*in+k];
    return packed_matrices.emplace(w,std::move(p)).first->second.values;
}
static void linear_range(const float *x,int frames,int in,int out,const float *p,const float *b,float *y,int begin,int end){
#ifdef __ARM_NEON
    for(int o=begin;o<end;o+=4){
        int t=0;
        for(;t+4<=frames;t+=4){
            float32x4_t a0=vld1q_f32(b+o),a1=a0,a2=a0,a3=a0;
            for(int k=0;k<in;k+=4){
                float32x4_t x0=vld1q_f32(x+(t+0)*in+k),x1=vld1q_f32(x+(t+1)*in+k);
                float32x4_t x2=vld1q_f32(x+(t+2)*in+k),x3=vld1q_f32(x+(t+3)*in+k);
                const float *wp=p+o*in+k*4;
                float32x4_t w0=vld1q_f32(wp),w1=vld1q_f32(wp+4),w2=vld1q_f32(wp+8),w3=vld1q_f32(wp+12);
                a0=vmlaq_lane_f32(a0,w0,vget_low_f32(x0),0);a1=vmlaq_lane_f32(a1,w0,vget_low_f32(x1),0);
                a2=vmlaq_lane_f32(a2,w0,vget_low_f32(x2),0);a3=vmlaq_lane_f32(a3,w0,vget_low_f32(x3),0);
                a0=vmlaq_lane_f32(a0,w1,vget_low_f32(x0),1);a1=vmlaq_lane_f32(a1,w1,vget_low_f32(x1),1);
                a2=vmlaq_lane_f32(a2,w1,vget_low_f32(x2),1);a3=vmlaq_lane_f32(a3,w1,vget_low_f32(x3),1);
                a0=vmlaq_lane_f32(a0,w2,vget_high_f32(x0),0);a1=vmlaq_lane_f32(a1,w2,vget_high_f32(x1),0);
                a2=vmlaq_lane_f32(a2,w2,vget_high_f32(x2),0);a3=vmlaq_lane_f32(a3,w2,vget_high_f32(x3),0);
                a0=vmlaq_lane_f32(a0,w3,vget_high_f32(x0),1);a1=vmlaq_lane_f32(a1,w3,vget_high_f32(x1),1);
                a2=vmlaq_lane_f32(a2,w3,vget_high_f32(x2),1);a3=vmlaq_lane_f32(a3,w3,vget_high_f32(x3),1);
            }
            vst1q_f32(y+(t+0)*out+o,a0);vst1q_f32(y+(t+1)*out+o,a1);
            vst1q_f32(y+(t+2)*out+o,a2);vst1q_f32(y+(t+3)*out+o,a3);
        }
        for(;t<frames;t++){
            float32x4_t a=vld1q_f32(b+o);
            for(int k=0;k<in;k++)a=vmlaq_n_f32(a,vld1q_f32(p+o*in+k*4),x[t*in+k]);
            vst1q_f32(y+t*out+o,a);
        }
    }
#else
    for(int o=begin;o<end;o+=4)for(int t=0;t<frames;t++){
        float a[4]={b[o],b[o+1],b[o+2],b[o+3]};
        for(int k=0;k<in;k++)for(int lane=0;lane<4;lane++)a[lane]+=p[o*in+k*4+lane]*x[t*in+k];
        for(int lane=0;lane<4;lane++)y[t*out+o+lane]=a[lane];
    }
#endif
}
struct LinearWorker {
    std::mutex lock;std::condition_variable cv;std::thread worker;
    bool ready=false,done=true,stop=false;
    const float *x,*p,*b;float *y;int frames,in,out,begin,end;
    LinearWorker():worker([this]{
        std::unique_lock<std::mutex> guard(lock);
        for(;;){
            cv.wait(guard,[this]{return ready || stop;});if(stop)return;
            ready=false;guard.unlock();linear_range(x,frames,in,out,p,b,y,begin,end);
            guard.lock();done=true;cv.notify_all();
        }
    }){}
    void launch(const float *xx,int tt,int ii,int oo,const float *pp,const float *bb,float *yy,int start,int finish){
        std::lock_guard<std::mutex> guard(lock);
        x=xx;frames=tt;in=ii;out=oo;p=pp;b=bb;y=yy;begin=start;end=finish;done=false;ready=true;cv.notify_all();
    }
    void wait(){std::unique_lock<std::mutex> guard(lock);cv.wait(guard,[this]{return done;});}
    ~LinearWorker(){ {std::lock_guard<std::mutex> guard(lock);stop=true;cv.notify_all();}worker.join();}
};
static int thread_count(){const char *e=std::getenv("LLVC_THREADS");return e && std::atoi(e)==1?1:2;}
static V linear_raw(const V &x,int frames,int in,int out,const float *w,const float *b){
    const V &p=packed(w,in,out);V y((size_t)frames*out);
    if(thread_count()==2){
        static LinearWorker worker;
        int split=(out/8)*4;
        worker.launch(x.data(),frames,in,out,p.data(),b,y.data(),split,out);
        linear_range(x.data(),frames,in,out,p.data(),b,y.data(),0,split);worker.wait();
    }else linear_range(x.data(),frames,in,out,p.data(),b,y.data(),0,out);
    return y;
}
static V linear(const V &x,int frames,int in,int out,const V &w,const V &b){
    return linear_raw(x,frames,in,out,w.data(),b.data());
}
'''
source=source[:start]+kernel+source[end:]
old='''        V qw(a.begin(),a.begin()+D*D),kw(a.begin()+D*D,a.begin()+2*D*D),vw(a.begin()+2*D*D,a.end());
        V qb(b.begin(),b.begin()+D),kb(b.begin()+D,b.begin()+2*D),vb(b.begin()+2*D,b.end());
        V q=linear(query,T,D,D,qw,qb),k=linear(memory,2*T,D,D,kw,kb),v=linear(memory,2*T,D,D,vw,vb);'''
new='''        V q=linear_raw(query,T,D,D,a.data(),b.data());
        V k=linear_raw(memory,2*T,D,D,a.data()+D*D,b.data()+D);
        V v=linear_raw(memory,2*T,D,D,a.data()+2*D*D,b.data()+2*D);'''
assert old in source
source=source.replace(old,new)
# Preparing immutable matrices during model setup excludes one-time repacking
# from steady-state inference, while keeping total load memory measurable.
ctor='''        label=w.get("derived.label",E);pos=w.get("mask_gen.decoder.pos_enc.pe",200*D);'''
prepare=ctor+'''
        for(int i=0;i<8;i++)packed(w.get("mask_gen.encoder.dcc_layers.dcc_"+std::to_string(i)+".layers.3.weight",E*E).data(),E,E);
        std::string dp="mask_gen.decoder.tf_dec_layers.0";
        for(const std::string &attn:{std::string(".self_attn"),std::string(".multihead_attn")}){
            const V &a=w.get(dp+attn+".in_proj_weight",3*D*D);
            for(int j=0;j<3;j++)packed(a.data()+j*D*D,D,D);
            packed(w.get(dp+attn+".out_proj.weight",D*D).data(),D,D);
        }
        packed(w.get(dp+".linear1.weight",E*D).data(),D,E);
        packed(w.get(dp+".linear2.weight",D*E).data(),E,D);
'''
assert source.count(ctor)==1
source=source.replace(ctor,prepare)
source=source.replace('<<",\\\"core\\\":\\\"native_fp32\\\"', '<<",\\\"threads\\\":"<<thread_count()<<",\\\"core\\\":\\\"native_fp32_packed_candidate\\\"')
(root/'native_llvc_fast.cpp').write_text(source,encoding='utf-8')
print('Created isolated NEON packed/two-core candidate; model unchanged.')
