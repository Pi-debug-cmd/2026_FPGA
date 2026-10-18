// Automatic causal pitch normalization feeding a separate neural timbre model.
// SoundTouch reference: https://www.surina.net/soundtouch/README.html
// This DSP alone is NOT target-person voice conversion.
#include "SoundTouch.h"
#include <vector>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <chrono>
#include <cstdio>
#include <cstdint>
#include <cstring>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
using namespace soundtouch;
struct PitchTracker {
    float ring[512]={},low1=0,low2=0;unsigned wr=0,div=0,filled=0;
    std::vector<float> values;unsigned next=0,quietblocks=0;
    double current=0,median=0,confidence=0,rms=0;
    void push(float v){low1+=.35f*(v-low1);low2+=.35f*(low1-low2);if(++div==4){div=0;ring[wr]=low2;wr=(wr+1)&511;if(filled<512)filled++;}}
    void update(){
        current=0;confidence=0;if(filled<224)return;
        float x[224],d[58];double mean=0,en=0;
        for(int i=0;i<224;i++){x[i]=ring[(wr+512-224+i)&511];mean+=x[i];}mean/=224;
        for(float &v:x){v-=float(mean);en+=v*v;}rms=std::sqrt(en/224);
        if(rms<.002){if(++quietblocks>77){values.clear();next=0;median=0;}return;}quietblocks=0;
        float sum=0;d[0]=1;
        for(int lag=1;lag<=57;lag++){float a=0;for(int i=0;i<160;i++){float z=x[i]-x[i+lag];a+=z*z;}sum+=a;d[lag]=sum>1e-20f?a*lag/sum:1;}
        for(int lag=9;lag<57;lag++)if(d[lag]<.15f && d[lag]<=d[lag-1] && d[lag]<d[lag+1]){
            // Reject weak half-period dips when the full-period match is much stronger.
            int full=0;for(int k=std::max(9,lag*2-2);k<=std::min(56,lag*2+2);k++)
                if(d[k]<=d[k-1]&&d[k]<d[k+1]&&d[k]<.45f*d[lag]&&d[lag]>.025f)if(!full||d[k]<d[full])full=k;
            if(full)lag=full;
            double denom=d[lag-1]-2*d[lag]+d[lag+1];double delta=std::fabs(denom)>1e-12?.5*(d[lag-1]-d[lag+1])/denom:0;
            delta=std::max(-.5,std::min(.5,delta));current=4000/(lag+delta);confidence=1-d[lag];
            if(values.size()<151)values.push_back(float(current));else{values[next]=float(current);next=(next+1)%151;}
            auto sorted=values;std::sort(sorted.begin(),sorted.end());median=sorted[sorted.size()/2];return;
        }
    }
};
struct Normalizer {
    SoundTouch st;PitchTracker tracker;double ratio=1,target=193.13304493,fixed=0;
    size_t received=0,emitted=0,blocks=0,first_output_input=0;double total_ms=0,max_ms=0;
    Normalizer(){st.setSampleRate(16000);st.setChannels(1);st.setTempo(1);st.setPitch(1);st.setSetting(SETTING_SEQUENCE_MS,32);st.setSetting(SETTING_SEEKWINDOW_MS,12);st.setSetting(SETTING_OVERLAP_MS,8);st.setSetting(SETTING_USE_QUICKSEEK,0);}
    void put(const float *x,size_t n){
        auto begin=std::chrono::steady_clock::now();for(size_t i=0;i<n;i++)tracker.push(x[i]);tracker.update();
        double desired=fixed>0?fixed:(tracker.values.size()>=8?target/tracker.median:1);
        desired=std::max(.65,std::min(2.2,desired));ratio+=(fixed>0?1:.055)*(desired-ratio);st.setPitch(ratio);st.putSamples(x,unsigned(n));
        double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();total_ms+=ms;max_ms=std::max(max_ms,ms);blocks++;received+=n;
    }
    unsigned take(float *x,unsigned n){unsigned got=st.receiveSamples(x,n);if(got&&!first_output_input)first_output_input=received;emitted+=got;return got;}
    void report(const char *path,bool done){
        std::string j="{\"received\":"+std::to_string(received)+",\"emitted\":"+std::to_string(emitted)+",\"blocks\":"+std::to_string(blocks)+",\"mean_compute_ms\":"+std::to_string(blocks?total_ms/blocks:0)+",\"max_compute_ms\":"+std::to_string(max_ms)+",\"first_output_input_samples\":"+std::to_string(first_output_input)+",\"reported_initial_latency_samples\":"+std::to_string(st.getSetting(SETTING_INITIAL_LATENCY))+",\"pitch_ratio\":"+std::to_string(ratio)+",\"source_current_hz\":"+std::to_string(tracker.current)+",\"source_median_hz\":"+std::to_string(tracker.median)+",\"target_hz\":"+std::to_string(target)+",\"finished\":"+(done?"true":"false")+",\"standalone_target_voice_conversion\":false}";
        if(path){std::ofstream f(std::string(path)+".tmp");f<<j;f.close();
#ifdef _WIN32
            std::remove(path); // Windows C rename cannot replace an existing destination.
#endif
            if(std::rename((std::string(path)+".tmp").c_str(),path))throw std::runtime_error("status replace failed");}if(done)std::cerr<<j<<"\n";
    }
};
int main(int argc,char **argv){
    try{
        bool stream=argc>=2&&std::string(argv[1])=="--stream";
        if((stream&&argc!=3&&argc!=4)||(!stream&&argc!=4&&argc!=5)){std::cerr<<"usage: pitch INPUT.f32 OUTPUT.f32 STATUS.json [fixed_ratio] | --stream STATUS.json [fixed_ratio]\n";return 2;}
        Normalizer p;const char *status=stream?argv[2]:argv[3];if((stream&&argc==4)||(!stream&&argc==5))p.fixed=std::stod(argv[argc-1]);
        float x[208],y[4096];
        if(stream){
#ifdef _WIN32
            _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
            std::setvbuf(stdin,0,_IONBF,0);std::setvbuf(stdout,0,_IONBF,0);int16_t pcm[4096];
            while(size_t n=std::fread(pcm,sizeof(int16_t),208,stdin)){
                for(size_t i=0;i<n;i++)x[i]=pcm[i]/32768.f;p.put(x,n);unsigned got;
                while((got=p.take(y,4096))){for(unsigned i=0;i<got;i++)pcm[i]=int16_t(std::lrint(std::max(-1.f,std::min(32767.f/32768.f,y[i]))*32768.f));if(std::fwrite(pcm,sizeof(int16_t),got,stdout)!=got)return 3;}
                if(p.blocks%77==0)p.report(status,false);
            }
            p.st.flush();unsigned got;while((got=p.take(y,4096))){for(unsigned i=0;i<got;i++)pcm[i]=int16_t(std::lrint(std::max(-1.f,std::min(32767.f/32768.f,y[i]))*32768.f));std::fwrite(pcm,sizeof(int16_t),got,stdout);}
        }else{
            std::ifstream in(argv[1],std::ios::binary);if(!in)return 2;std::vector<float> output;std::ofstream trace(std::string(status)+".trace.csv");trace<<"sample,current,median,confidence,ratio\n";
            while(in){in.read(reinterpret_cast<char*>(x),sizeof(x));size_t n=size_t(in.gcount())/4;if(!n)break;p.put(x,n);trace<<p.received<<","<<p.tracker.current<<","<<p.tracker.median<<","<<p.tracker.confidence<<","<<p.ratio<<"\n";unsigned got;while((got=p.take(y,4096)))output.insert(output.end(),y,y+got);}
            p.st.flush();unsigned got;while((got=p.take(y,4096)))output.insert(output.end(),y,y+got);
            output.resize(p.received,0);std::ofstream out(argv[2],std::ios::binary);out.write(reinterpret_cast<char*>(output.data()),output.size()*4);if(!out)return 3;
        }
        p.report(status,true);return 0;
    }catch(const std::exception &e){std::cerr<<e.what()<<"\n";return 1;}
}
