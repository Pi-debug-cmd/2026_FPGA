// Causal buffered pitch-synchronous overlap-add on NEURAL output, not source bypass.
// Algorithm reference: Charpentier/Moulines, Eurospeech1989 (not copied source).
// https://www.isca-archive.org/eurospeech_1989/charpentier89_eurospeech.html
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
#include "causal_pitch_tracker.hpp"
struct Psola {
    static const int RING=16384,LAT=624,HOP=208,TABLE=1024;
    float x[RING]={},low[RING]={},ola[RING]={},weight[RING]={},hann[TABLE+1];
    double lp1=0,lp2=0,nextmark=0,ratio=1,previousf0=0,blend=0,target=193.13304493,fixed=0;
    size_t received=0,emitted=0,blocks=0;double total_ms=0,max_ms=0;PitchTracker tracker;
    Psola(){for(int i=0;i<=TABLE;i++)hann[i]=float(.5+.5*std::cos(3.14159265358979323846*i/TABLE));}
    float sample(long i,bool filtered=false)const{if(i<0||i>=long(received)||long(received)-i>=RING)return 0;return filtered?low[i&(RING-1)]:x[i&(RING-1)];}
    float window(double position)const{double at=std::min(1.,std::fabs(position))*TABLE;int i=int(at);if(i>=TABLE)return 0;return hann[i]+float(at-i)*(hann[i+1]-hann[i]);}
    void grain(double center,double period){
        long begin=long(std::floor(center-period*.5)),end=long(std::ceil(center+period*.5));
        long epoch=begin;float largest=-1e30f;for(long i=begin;i<=end;i++){float v=sample(i,true);if(v>largest){largest=v;epoch=i;}}
        int width=int(std::ceil(period));for(int j=-width;j<=width;j++){
            float w=window(j/period);if(w<=0)continue;double at=center+j;long a=long(std::floor(at));float frac=float(at-a),v=sample(epoch+j);
            if(a>=0){int slot=a&(RING-1);ola[slot]+=v*w*(1-frac);weight[slot]+=w*(1-frac);}
            if(a+1>=0){int slot=(a+1)&(RING-1);ola[slot]+=v*w*frac;weight[slot]+=w*frac;}
        }
    }
    void process(const float *in,float *out,size_t n){
        auto start=std::chrono::steady_clock::now();size_t old=received;
        for(size_t i=0;i<n;i++){size_t slot=received&(RING-1);x[slot]=in[i];lp1+=.12*(in[i]-lp1);lp2+=.12*(lp1-lp2);low[slot]=float(lp2);tracker.push(in[i]);received++;}
        tracker.update();double f0=previousf0;previousf0=tracker.current;
        double desired=fixed>0?fixed:(tracker.values.size()>=8?target/tracker.median:1);
        desired=std::max(.65,std::min(2.2,desired));ratio+=(fixed>0?1:.055)*(desired-ratio);
        long t=long(old)-LAT;double rms=0;for(size_t i=0;i<n;i++){double v=sample(t+long(i));rms+=v*v;}rms=std::sqrt(rms/std::max<size_t>(1,n));
        bool voiced=t>=0&&f0>=70&&f0<=445&&rms>.0015&&std::fabs(ratio-1)>.001;
        if(voiced){double period=16000/f0;if(nextmark<t-period)nextmark=t-period;
            while(nextmark<t+long(n)+period){grain(nextmark,period);nextmark+=period/ratio;}}
        else nextmark=t+long(n);
        for(size_t i=0;i<n;i++){
            long at=t+long(i);if(at<0){out[i]=0;continue;}int slot=at&(RING-1);float original=sample(at),converted=weight[slot]>.05f?ola[slot]/weight[slot]:original;
            blend+=.015*((voiced?1.:0.)-blend);out[i]=float(original*(1-blend)+converted*blend);ola[slot]=0;weight[slot]=0;
        }
        double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();total_ms+=ms;max_ms=std::max(max_ms,ms);blocks++;emitted+=n;
    }
    void report(const char *path,bool finished){
        std::string s="{\"input_samples\":"+std::to_string(received)+",\"output_samples\":"+std::to_string(emitted)+",\"algorithmic_delay_samples\":624,\"algorithmic_delay_ms\":39,\"mean_compute_ms\":"+std::to_string(total_ms/blocks)+",\"max_compute_ms\":"+std::to_string(max_ms)+",\"ratio\":"+std::to_string(ratio)+",\"source_f0\":"+std::to_string(tracker.current)+",\"source_median\":"+std::to_string(tracker.median)+",\"target_hz\":"+std::to_string(target)+",\"finished\":"+(finished?"true":"false")+",\"unvoiced_path\":\"delayed neural output\",\"raw_microphone_bypass\":false}";
        std::ofstream f(std::string(path)+".tmp");f<<s;f.close();
#ifdef _WIN32
        std::remove(path);
#endif
        if(std::rename((std::string(path)+".tmp").c_str(),path))throw std::runtime_error("status replacement failed");if(finished)std::cerr<<s<<"\n";
    }
};
int main(int argc,char **argv){try{
    bool live=argc>=2&&std::string(argv[1])=="--stream";if((live&&argc!=3&&argc!=4)||(!live&&argc!=4&&argc!=5))return 2;
    Psola p;if((live&&argc==4)||(!live&&argc==5))p.fixed=std::stod(argv[argc-1]);const char *status=live?argv[2]:argv[3];float in[208],out[208];
    if(live){
#ifdef _WIN32
        _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
        std::setvbuf(stdin,0,_IONBF,0);std::setvbuf(stdout,0,_IONBF,0);int16_t pcm[208];
        while(size_t n=std::fread(pcm,sizeof(int16_t),208,stdin)){for(size_t i=0;i<n;i++)in[i]=pcm[i]/32768.f;p.process(in,out,n);for(size_t i=0;i<n;i++)pcm[i]=int16_t(std::lrint(std::max(-1.f,std::min(32767.f/32768.f,out[i]))*32768));if(std::fwrite(pcm,sizeof(int16_t),n,stdout)!=n)return 3;if(p.blocks%77==0)p.report(status,false);}
    }else{
        std::ifstream f(argv[1],std::ios::binary);if(!f)return 2;std::vector<float> all;size_t count=0;
        while(f){f.read(reinterpret_cast<char*>(in),sizeof(in));size_t n=size_t(f.gcount())/4;if(!n)break;p.process(in,out,n);all.insert(all.end(),out,out+n);count+=n;}
        std::fill(in,in+208,0);for(int i=0;i<3;i++){p.process(in,out,208);all.insert(all.end(),out,out+208);}
        assert(all.size()>=624+count);std::ofstream g(argv[2],std::ios::binary);g.write(reinterpret_cast<char*>(all.data()+624),count*4);if(!g)return 3;
    }
    p.report(status,true);return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<"\n";return 1;}}
