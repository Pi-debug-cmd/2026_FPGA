// Exact fixed-geometry LLVC FP32 inference trial.
// ARMv7 NEON or portable scalar; no Torch, Python, network or PC inference.
// This moves the existing 20-step checkpoint, NOT the accepted CV3 teacher.
// Quality and real-time performance are unapproved. File-based trial first.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <cstdlib>
#include <thread>
#include <mutex>
#include <condition_variable>
#ifdef __ARM_NEON
#include <arm_neon.h>
#endif
#ifdef __linux__
#include <sys/resource.h>
#endif

typedef std::vector<float> V;
static const int E=96, D=48, T=13, CHUNK=208, LOOK=16, BLOCK=240;
struct Tensor { std::vector<uint32_t> shape; V a; };
struct Weights {
    std::map<std::string,Tensor> table;
    uint32_t readu(std::ifstream &f) {
        uint32_t x=0; f.read((char*)&x,4);
        if(!f) throw std::runtime_error("truncated model");
        return x;
    }
    explicit Weights(const char *path) {
        std::ifstream f(path,std::ios::binary);
        char magic[8]; f.read(magic,8);
        if(!f || std::memcmp(magic,"LLVCF001",8)) throw std::runtime_error("bad model header");
        uint32_t n=readu(f); if(n!=148) throw std::runtime_error("unexpected tensor count");
        for(uint32_t i=0;i<n;i++){
            uint32_t len=readu(f),nd=readu(f);
            if(!len || len>200 || !nd || nd>4) throw std::runtime_error("bad tensor metadata");
            std::string key(len,' ');f.read(&key[0],len);
            Tensor a;size_t count=1;
            for(uint32_t j=0;j<nd;j++){uint32_t d=readu(f);if(!d || d>10000)throw std::runtime_error("bad dimension");a.shape.push_back(d);count*=d;}
            if(count>4000000 || table.count(key))throw std::runtime_error("bad tensor size/name");
            a.a.resize(count);f.read((char*)a.a.data(),count*sizeof(float));
            if(!f)throw std::runtime_error("truncated tensor data");
            for(size_t j=0;j<count;j++)if(!std::isfinite(a.a[j]))throw std::runtime_error("nonfinite weight");
            table[key]=std::move(a);
        }
        char tail;if(f.read(&tail,1))throw std::runtime_error("unexpected model trailing data");
    }
    const V &get(const std::string &key, size_t count) const {
        auto p=table.find(key);if(p==table.end() || p->second.a.size()!=count)throw std::runtime_error("tensor missing/shape mismatch: "+key);
        return p->second.a;
    }
};
static float dot(const float *a,const float *b,int n){
#ifdef __ARM_NEON
    float32x4_t s=vdupq_n_f32(0);int i=0;
    for(;i+4<=n;i+=4)s=vmlaq_f32(s,vld1q_f32(a+i),vld1q_f32(b+i));
    float32x2_t u=vadd_f32(vget_low_f32(s),vget_high_f32(s));
    u=vpadd_f32(u,u);float v=vget_lane_f32(u,0);
    for(;i<n;i++)v+=a[i]*b[i];return v;
#elif defined(LLVC_EMULATE_NEON)
    float s[4]={0,0,0,0};int i=0;
    for(;i+4<=n;i+=4)for(int lane=0;lane<4;lane++)s[lane]+=a[i+lane]*b[i+lane];
    float v=(s[0]+s[2])+(s[1]+s[3]);
    for(;i<n;i++)v+=a[i]*b[i];return v;
#else
    float v=0;for(int i=0;i<n;i++)v+=a[i]*b[i];return v;
#endif
}

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
static void relu(V &v){for(size_t i=0;i<v.size();i++)v[i]=std::max(0.f,v[i]);}
static void norm(V &v,int frames,int dim,const V &w,const V &b){
    for(int t=0;t<frames;t++){
        float *row=&v[t*dim];double mean=0,var=0;
        for(int c=0;c<dim;c++)mean+=row[c];mean/=dim;
        for(int c=0;c<dim;c++){double d=row[c]-mean;var+=d*d;}
        float inv=1.f/std::sqrt(float(var/dim)+1e-5f),m=float(mean);
        for(int c=0;c<dim;c++)row[c]=(row[c]-m)*inv*w[c]+b[c];
    }
}
static V concatenate(const V &old,const V &x){V v=old;v.insert(v.end(),x.begin(),x.end());return v;}
static void savef(const std::string &path,const V &v){
    std::ofstream f(path.c_str(),std::ios::binary);f.write((const char*)v.data(),v.size()*4);
    if(!f)throw std::runtime_error("cannot write output");
}
static V readf(const char *path){
    std::ifstream f(path,std::ios::binary|std::ios::ate);
    if(!f)throw std::runtime_error("cannot read input");
    std::streamoff bytes=f.tellg();
    if(bytes<0 || bytes%4 || bytes>30*16000*4)throw std::runtime_error("input must be float32 mono16k, <=30s");
    V x((size_t)bytes/4);f.seekg(0);f.read((char*)x.data(),bytes);
    for(size_t i=0;i<x.size();i++)if(!std::isfinite(x[i]))throw std::runtime_error("nonfinite input");
    return x;
}
struct Net {
    const Weights &w; V enc[8],memctx,tgtctx,outctx,front;float pre[12][2];V label,pos;
    std::string debug; bool first;
    explicit Net(const Weights &weights):w(weights),memctx(T*D,0),tgtctx(T*D,0),outctx(4*E,0),front(32,0),first(true){
        std::memset(pre,0,sizeof(pre));
        for(int i=0;i<8;i++)enc[i].assign((size_t)(2<<i)*E,0);
        label=w.get("derived.label",E);pos=w.get("mask_gen.decoder.pos_enc.pe",200*D);
        for(int i=0;i<8;i++)packed(w.get("mask_gen.encoder.dcc_layers.dcc_"+std::to_string(i)+".layers.3.weight",E*E).data(),E,E);
        std::string dp="mask_gen.decoder.tf_dec_layers.0";
        for(const std::string &attn:{std::string(".self_attn"),std::string(".multihead_attn")}){
            const V &a=w.get(dp+attn+".in_proj_weight",3*D*D);
            for(int j=0;j<3;j++)packed(a.data()+j*D*D,D,D);
            packed(w.get(dp+attn+".out_proj.weight",D*D).data(),D,D);
        }
        packed(w.get(dp+".linear1.weight",E*D).data(),D,E);
        packed(w.get(dp+".linear2.weight",D*E).data(),E,D);

    }
    void dump(const std::string &name,const V &v){if(first && !debug.empty())savef(debug+"."+name+".f32",v);}
    V prenet(const V &x){
        V cur=x;
        for(int layer=0;layer<12;layer++){
            std::string p="convnet_pre.down_convs."+std::to_string(layer);
            const V &fw=w.get(p+".filter.weight",3),&fb=w.get(p+".filter.bias",1);
            const V &gw=w.get(p+".gate.weight",3),&gb=w.get(p+".gate.bias",1);
            V ext;ext.push_back(pre[layer][0]);ext.push_back(pre[layer][1]);ext.insert(ext.end(),cur.begin(),cur.end());
            pre[layer][0]=ext[ext.size()-2];pre[layer][1]=ext.back();
            V next(BLOCK);
            for(int t=0;t<BLOCK;t++){
                float f=dot(&ext[t],fw.data(),3)+fb[0],g=dot(&ext[t],gw.data(),3)+gb[0];
                next[t]=ext[t+2]+std::tanh(f)/(1.f+std::exp(-g));
            }
            cur.swap(next);
        }
        for(int t=0;t<BLOCK;t++)cur[t]+=x[t];return cur;
    }
    V encoder(V x){
        for(int layer=0;layer<8;layer++){
            int dil=1<<layer,context=2*dil;
            std::string p="mask_gen.encoder.dcc_layers.dcc_"+std::to_string(layer)+".layers.";
            V ext=concatenate(enc[layer],x);
            enc[layer].assign(ext.end()-context*E,ext.end());
            const V &dw=w.get(p+"0.weight",E*3),&db=w.get(p+"0.bias",E);
            V y(T*E);
            for(int t=0;t<T;t++)for(int c=0;c<E;c++)
                y[t*E+c]=db[c]+ext[t*E+c]*dw[c*3]+ext[(t+dil)*E+c]*dw[c*3+1]+ext[(t+2*dil)*E+c]*dw[c*3+2];
            norm(y,T,E,w.get(p+"1.weight",E),w.get(p+"1.bias",E));relu(y);
            y=linear(y,T,E,E,w.get(p+"3.weight",E*E),w.get(p+"3.bias",E));
            norm(y,T,E,w.get(p+"4.weight",E),w.get(p+"4.bias",E));relu(y);
            for(size_t j=0;j<x.size();j++)x[j]+=y[j];
        }
        return x;
    }
    V project_e2d(const V &x,const std::string &name){
        const V &a=w.get(name+".weight",D*2),&b=w.get(name+".bias",D);V y(T*D);
        for(int t=0;t<T;t++)for(int c=0;c<D;c++)y[t*D+c]=std::max(0.f,x[t*E+2*c]*a[2*c]+x[t*E+2*c+1]*a[2*c+1]+b[c]);
        return y;
    }
    V mha(const V &query,const V &memory,const std::string &p){
        const V &a=w.get(p+".in_proj_weight",3*D*D),&b=w.get(p+".in_proj_bias",3*D);
        V q=linear_raw(query,T,D,D,a.data(),b.data());
        V k=linear_raw(memory,2*T,D,D,a.data()+D*D,b.data()+D);
        V v=linear_raw(memory,2*T,D,D,a.data()+2*D*D,b.data()+2*D);
        V result(T*D,0);const float scale=1.f/std::sqrt(float(D/8));
        for(int head=0;head<8;head++)for(int t=0;t<T;t++){
            float scores[26],maxscore=-1e30f;
            for(int j=0;j<2*T;j++){scores[j]=dot(&q[t*D+head*(D/8)],&k[j*D+head*(D/8)],D/8)*scale;maxscore=std::max(maxscore,scores[j]);}
            float sum=0;for(int j=0;j<2*T;j++){scores[j]=std::exp(scores[j]-maxscore);sum+=scores[j];}
            for(int j=0;j<2*T;j++){
                float f=scores[j]/sum;
                for(int c=0;c<D/8;c++)result[t*D+head*(D/8)+c]+=f*v[j*D+head*(D/8)+c];
            }
        }
        return linear(result,T,D,D,w.get(p+".out_proj.weight",D*D),w.get(p+".out_proj.bias",D));
    }
    V decoder(const V &e,const V &m){
        V memory=concatenate(memctx,e),target=concatenate(tgtctx,m);
        memctx=e;tgtctx=m;
        for(int t=0;t<2*T;t++)for(int c=0;c<D;c++){memory[t*D+c]+=pos[t*D+c];target[t*D+c]+=pos[t*D+c];}
        V q(target.begin()+T*D,target.end());
        std::string p="mask_gen.decoder.tf_dec_layers.0";
        V tmp=mha(q,target,p+".self_attn");
        for(size_t i=0;i<q.size();i++)q[i]+=tmp[i];
        norm(q,T,D,w.get(p+".norm1.weight",D),w.get(p+".norm1.bias",D));
        tmp=mha(q,memory,p+".multihead_attn");
        for(size_t i=0;i<q.size();i++)q[i]+=tmp[i];
        norm(q,T,D,w.get(p+".norm2.weight",D),w.get(p+".norm2.bias",D));
        tmp=linear(q,T,D,E,w.get(p+".linear1.weight",E*D),w.get(p+".linear1.bias",E));relu(tmp);
        tmp=linear(tmp,T,E,D,w.get(p+".linear2.weight",D*E),w.get(p+".linear2.bias",D));
        for(size_t i=0;i<q.size();i++)q[i]+=tmp[i];
        norm(q,T,D,w.get(p+".norm3.weight",D),w.get(p+".norm3.bias",D));return q;
    }
    V process(const float *shifted){
        V block=front;block.insert(block.end(),shifted,shifted+CHUNK);
        front.assign(shifted+CHUNK-32,shifted+CHUNK);
        V x=prenet(block);dump("pre",x);
        const V &iw=w.get("in_conv.0.weight",E*48);
        V input(T*E);
        for(int t=0;t<T;t++)for(int c=0;c<E;c++)input[t*E+c]=std::max(0.f,dot(&x[t*16],&iw[c*48],48));
        dump("input",input);
        V encoded=encoder(input);dump("encoded",encoded);
        V integrated=encoded;
        for(int t=0;t<T;t++)for(int c=0;c<E;c++)integrated[t*E+c]*=label[c];
        V e=project_e2d(encoded,"mask_gen.proj_e2d_e.0");
        V m=project_e2d(integrated,"mask_gen.proj_e2d_l.0");
        m=decoder(e,m);dump("decoded",m);
        const V &pw=w.get("mask_gen.proj_d2e.0.weight",E),&pb=w.get("mask_gen.proj_d2e.0.bias",E);
        V masked(T*E);
        for(int t=0;t<T;t++)for(int c=0;c<E;c++){
            float mask=integrated[t*E+c]+std::max(0.f,m[t*D+c/2]*pw[c]+pb[c]);
            masked[t*E+c]=input[t*E+c]*mask;
        }
        dump("masked",masked);
        V total=concatenate(outctx,masked);
        outctx.assign(masked.end()-4*E,masked.end());
        const V &ow=w.get("out_conv.0.weight",E*80);V output(CHUNK,0);
        for(int t=0;t<17;t++)for(int c=0;c<E;c++){
            float f=total[t*E+c];
            int begin=std::max(0,64-t*16),end=std::min(80,CHUNK+64-t*16);
            for(int j=begin;j<end;j++)output[t*16+j-64]+=f*ow[c*80+j];
        }
        for(int i=0;i<CHUNK;i++)output[i]=std::tanh(output[i]);
        dump("output",output);first=false;return output;
    }
};
int main(int argc,char **argv){
    try{
        if(argc!=4 && argc!=5){std::cerr<<"usage: native_llvc MODEL.f32 INPUT.f32 OUTPUT.f32 [DEBUG_PREFIX]\n";return 2;}
        auto load_start=std::chrono::steady_clock::now();Weights w(argv[1]);Net model(w);
        if(argc==5)model.debug=argv[4];
        V input=readf(argv[2]);size_t n=input.size(),chunks=(n+CHUNK-1)/CHUNK;
        input.resize(chunks*CHUNK+LOOK,0);
        V output;output.reserve(chunks*CHUNK);
        auto start=std::chrono::steady_clock::now();double maxms=0,summs=0;
        for(size_t c=0;c<chunks;c++){
            auto before=std::chrono::steady_clock::now();
            V block=model.process(&input[c*CHUNK+LOOK]);
            double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-before).count();
            maxms=std::max(maxms,ms);summs+=ms;
            for(size_t i=0;i<block.size();i++)if(!std::isfinite(block[i]))throw std::runtime_error("nonfinite output");
            output.insert(output.end(),block.begin(),block.end());
        }
        double inference=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        output.resize(n);savef(argv[3],output);
        long peakrss=0;
#ifdef __linux__
        struct rusage use;if(!getrusage(RUSAGE_SELF,&use))peakrss=use.ru_maxrss;
#endif
        std::cout<<"{\"samples\":"<<n<<",\"chunks\":"<<chunks<<",\"audio_seconds\":"<<(double(n)/16000)
                 <<",\"inference_seconds\":"<<inference<<",\"mean_chunk_ms\":"<<(chunks?summs/chunks:0)
                 <<",\"max_chunk_ms\":"<<maxms<<",\"peak_rss_kib\":"<<peakrss
                 <<",\"threads\":"<<thread_count()<<",\"core\":\"native_fp32_packed_candidate\",\"source_enrollment\":false,\"real_time_verified\":false,\"quality_accepted\":false}\n";
        return 0;
    }catch(const std::exception &e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
}