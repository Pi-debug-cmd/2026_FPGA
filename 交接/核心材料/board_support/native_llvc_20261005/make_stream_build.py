"""Bounded live PCM adapter for the separately validated small96 geometry."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=(ROOT/'native_llvc_small96_ring.cpp').read_text(encoding='utf-8')
source=source.replace('#include <cstdlib>','#include <cstdlib>\n#include <csignal>\n#include <cerrno>\n#ifdef _WIN32\n#include <io.h>\n#include <fcntl.h>\n#endif')
code=r'''
static volatile sig_atomic_t streaming=1;
static void stream_stop(int){streaming=0;}
static size_t read_pcm(int16_t *dst,size_t count){
    size_t have=0;
    while(have<count && streaming){
        size_t n=std::fread(dst+have,sizeof(int16_t),count-have,stdin);have+=n;
        if(!n){
            if(std::ferror(stdin) && errno==EINTR){std::clearerr(stdin);continue;}
            if(std::ferror(stdin))throw std::runtime_error("PCM input read failed");
            break;
        }
    }
    return have;
}
static void status(const char *path,size_t received,size_t produced,size_t chunks,double total,double maximum,size_t late,bool finished){
    std::string json="{\"input_samples\":"+std::to_string(received)+",\"output_samples\":"+std::to_string(produced)
        +",\"chunks\":"+std::to_string(chunks)+",\"mean_compute_ms\":"+std::to_string(chunks?total/chunks:0)
        +",\"max_compute_ms\":"+std::to_string(maximum)+",\"compute_deadlines_missed\":"+std::to_string(late)
        +",\"format\":\"S16_LE_mono_16000\",\"bounded_lookahead_samples\":16,\"finished\":"+(finished?"true":"false")
        +",\"target_quality_accepted\":false,\"acoustic_latency_measured\":false}\n";
    if(path){
        std::string tmp=std::string(path)+".tmp";std::ofstream f(tmp.c_str());f<<json;f.close();
        if(!f || std::rename(tmp.c_str(),path))throw std::runtime_error("status update failed");
    }
    if(finished)std::cerr<<json;
}
static int run_stream(const char *model_path,const char *status_path){
#ifdef _WIN32
    _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
    std::signal(SIGTERM,stream_stop);std::signal(SIGINT,stream_stop);
    std::setvbuf(stdin,0,_IONBF,0);std::setvbuf(stdout,0,_IONBF,0);
    Weights w(model_path);Net net(w);int16_t input[CHUNK+LOOK],output[CHUNK];V pending(CHUNK+LOOK,0);
    size_t got=read_pcm(input,CHUNK+LOOK),received=got,produced=0,chunks=0,late=0;
    for(size_t i=0;i<got;i++)pending[i]=input[i]/32768.f;
    bool eof=got<CHUNK+LOOK;double total=0,maximum=0;
    while(streaming && produced<received){
        auto start=std::chrono::steady_clock::now();V y=net.process(pending.data()+LOOK);
        double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
        total+=ms;maximum=std::max(maximum,ms);chunks++;if(ms>13)late++;
        size_t valid=std::min<size_t>(CHUNK,received-produced);
        for(size_t i=0;i<valid;i++){
            if(!std::isfinite(y[i]))throw std::runtime_error("nonfinite live output");
            float f=std::max(-1.f,std::min(32767.f/32768.f,y[i]));output[i]=int16_t(std::lrint(f*32768.f));
        }
        if(std::fwrite(output,sizeof(int16_t),valid,stdout)!=valid)throw std::runtime_error("PCM output write failed");
        produced+=valid;
        if(chunks%77==0)status(status_path,received,produced,chunks,total,maximum,late,false);
        if(eof && produced==received)break;
        std::memmove(pending.data(),pending.data()+CHUNK,LOOK*sizeof(float));
        got=read_pcm(input,CHUNK);received+=got;eof=got<CHUNK;
        for(size_t i=0;i<CHUNK;i++)pending[LOOK+i]=i<got?input[i]/32768.f:0.f;
    }
    status(status_path,received,produced,chunks,total,maximum,late,true);
    return 0;
}
'''
source=source.replace('int main(int argc,char **argv){',code+'\nint main(int argc,char **argv){')
source=source.replace('    try{\n        if(argc!=4', '    try{\n        if((argc==3 || argc==4) && std::string(argv[1])=="--stream")return run_stream(argv[2],argc==4?argv[3]:0);\n        if(argc!=4')
(ROOT/'native_llvc_small96_stream.cpp').write_text(source,encoding='utf-8')
print('Created bounded S16 stream adapter; no microphone recording started.')
