// Diagnostic only: identical PCM forwarded, no conversion, no waveform files.
#include <cstdio>
#include <cstdint>
#include <csignal>
#include <cerrno>
#include <cmath>
#include <algorithm>
#include <string>
#include <fstream>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
static volatile sig_atomic_t running=1;
static void stop(int){running=0;}
int main(int argc,char **argv){
    if(argc!=2)return 2;
#ifdef _WIN32
    _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
    std::signal(SIGTERM,stop);std::signal(SIGINT,stop);
    std::setvbuf(stdin,0,_IONBF,0);std::setvbuf(stdout,0,_IONBF,0);
    int16_t pcm[208];size_t total=0,chunks=0,count=0,clips=0;double power=0,peak=0;
    auto status=[&](bool finished){
        std::string meter="{\"rms\":"+std::to_string(count?std::sqrt(power/count):0)+",\"peak\":"+std::to_string(peak)+",\"samples\":"+std::to_string(count)+",\"clips\":"+std::to_string(clips)+"}";
        std::string json="{\"mode\":\"diagnostic_original_passthrough_NOT_voice_conversion\",\"input_samples\":"+std::to_string(total)+",\"output_samples\":"+std::to_string(total)+",\"chunks\":"+std::to_string(chunks)+",\"mean_compute_ms\":0,\"finished\":"+(finished?"true":"false")+",\"meter_window_input\":"+meter+",\"meter_window_output\":"+meter+"}\n";
        std::string tmp=std::string(argv[1])+".tmp";std::ofstream f(tmp.c_str());f<<json;f.close();
        if(!f)return false;
#ifdef _WIN32
        std::remove(argv[1]);
#endif
        if(std::rename(tmp.c_str(),argv[1]))return false;
        count=clips=0;power=peak=0;return true;
    };
    while(running){
        size_t have=0;
        while(have<208 && running){size_t n=std::fread(pcm+have,2,208-have,stdin);have+=n;if(!n){if(std::ferror(stdin)&&errno==EINTR){std::clearerr(stdin);continue;}break;}}
        if(!have)break;
        for(size_t i=0;i<have;i++){double v=pcm[i]/32768.;power+=v*v;peak=std::max(peak,std::fabs(v));count++;if(pcm[i]==-32768||pcm[i]==32767)clips++;}
        if(std::fwrite(pcm,2,have,stdout)!=have)return 3;
        total+=have;chunks++;
        if(chunks%77==0 && !status(false))return 4;
        if(have<208)break;
    }
    if(std::ferror(stdin))return 5;
    return status(true)?0:4;
}
