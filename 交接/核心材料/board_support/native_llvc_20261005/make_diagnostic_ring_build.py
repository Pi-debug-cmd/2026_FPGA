"""Bounded diagnostic PCM ring, output remains causal; dump on explicit flag."""
from pathlib import Path
r=Path(__file__).resolve().parent
s=(r/'native_llvc_small96_meter.cpp').read_text(encoding='utf-8')
code=r'''
// At most ~20 seconds retained in RAM; file dump only after a requested test.
static const size_t DIAG_KEEP=208*1538;
static std::vector<int16_t> diag_input(DIAG_KEEP+16),diag_output(DIAG_KEEP);
static size_t diag_received=0,diag_produced=0;
static bool diag_saved=false;
static void diag_read(const int16_t *x,size_t n){for(size_t i=0;i<n;i++)diag_input[diag_received++%(DIAG_KEEP+16)]=x[i];}
static void diag_write(const int16_t *x,size_t n){for(size_t i=0;i<n;i++)diag_output[diag_produced++%DIAG_KEEP]=x[i];}
static void diag_dump(){
    if(diag_saved)return;
    const char *flag=std::getenv("LLVC_DIAG_TRIGGER");const char *prefix=std::getenv("LLVC_DIAG_PREFIX");
    if(!flag || !prefix)return;
    std::ifstream trigger(flag);if(!trigger.good())return;trigger.close();
    size_t keep=std::min(DIAG_KEEP,diag_produced),start=diag_produced-keep;
    std::ofstream a((std::string(prefix)+".input.s16").c_str(),std::ios::binary);
    std::ofstream b((std::string(prefix)+".output.s16").c_str(),std::ios::binary);
    auto circular_write=[&](std::ofstream &f,const std::vector<int16_t> &buffer){
        size_t at=start%buffer.size(),first=std::min(keep,buffer.size()-at);
        f.write(reinterpret_cast<const char*>(buffer.data()+at),first*2);
        if(first<keep)f.write(reinterpret_cast<const char*>(buffer.data()),(keep-first)*2);
    };
    circular_write(a,diag_input);circular_write(b,diag_output);
    a.close();b.close();if(!a||!b)throw std::runtime_error("diagnostic dump failed");
    std::ofstream m((std::string(prefix)+".json").c_str());
    m<<"{\"format\":\"S16_LE_mono_16000\",\"start_sample\":"<<start<<",\"end_sample\":"<<diag_produced<<",\"samples\":"<<keep<<",\"realtime_output_not_delayed_by_ring\":true,\"diagnostic_only_not_source_enrollment\":true}\n";
    m.close();if(!m)throw std::runtime_error("diagnostic manifest failed");
    std::remove(flag);diag_saved=true;
}
'''
s=s.replace('static volatile sig_atomic_t streaming=1;',code+'\nstatic volatile sig_atomic_t streaming=1;')
s=s.replace('size_t got=read_pcm(input,CHUNK+LOOK),received=got,produced=0,chunks=0,late=0;',
 'size_t got=read_pcm(input,CHUNK+LOOK),received=got,produced=0,chunks=0,late=0;diag_read(input,got);')
s=s.replace('produced+=valid;', 'produced+=valid;diag_write(output,valid);')
s=s.replace('if(chunks%77==0)status(status_path,received,produced,chunks,total,maximum,late,false);',
 'if(chunks%77==0){status(status_path,received,produced,chunks,total,maximum,late,false);diag_dump();}')
s=s.replace('got=read_pcm(input,CHUNK);received+=got;eof=got<CHUNK;',
 'got=read_pcm(input,CHUNK);diag_read(input,got);received+=got;eof=got<CHUNK;')
s=s.replace('status(status_path,received,produced,chunks,total,maximum,late,true);','diag_dump();status(status_path,received,produced,chunks,total,maximum,late,true);')
(r/'native_llvc_small96_diag.cpp').write_text(s,encoding='utf-8')
print('Generated bounded input/output diagnostic ring candidate.')
