"""Separate diagnostics adapter; default gains preserve the verified stream."""
from pathlib import Path
root=Path(__file__).resolve().parent
s=(root/'native_llvc_small96_stream.cpp').read_text(encoding='utf-8')
marker='static volatile sig_atomic_t streaming=1;'
code=r'''
struct Meter {
    double sum=0, peak=0; size_t count=0, clips=0;
    void add(float x){sum+=double(x)*x;peak=std::max(peak,double(std::fabs(x)));count++;if(std::fabs(x)>=32767.f/32768.f)clips++;}
    std::string json() const {return "{\"rms\":"+std::to_string(count?std::sqrt(sum/count):0)+",\"peak\":"+std::to_string(peak)+",\"samples\":"+std::to_string(count)+",\"clips\":"+std::to_string(clips)+"}";}
};
static Meter input_meter,raw_meter,output_meter;
static float input_gain=1,output_gain=1;
static float read_gain(const char *name,float maximum){
    const char *v=std::getenv(name);if(!v)return 1;
    char *end=0;float f=std::strtof(v,&end);
    if(end==v || *end || !std::isfinite(f) || f<0.125f || f>maximum)throw std::runtime_error("invalid gain");
    return f;
}
'''
s=s.replace(marker,code+'\n'+marker)
s=s.replace('+",\\\"target_quality_accepted\\\":false,\\\"acoustic_latency_measured\\\":false}\\n";', '+",\\\"target_quality_accepted\\\":false,\\\"acoustic_latency_measured\\\":false"\n        +",\\\"meter_window_input\\\":"+input_meter.json()+",\\\"meter_window_raw_model\\\":"+raw_meter.json()+",\\\"meter_window_output\\\":"+output_meter.json()\n        +",\\\"input_gain\\\":"+std::to_string(input_gain)+",\\\"output_gain\\\":"+std::to_string(output_gain)+"}\\n";')
s=s.replace('if(finished)std::cerr<<json;', 'if(finished)std::cerr<<json;\n    input_meter=Meter();raw_meter=Meter();output_meter=Meter();')
s=s.replace('Weights w(model_path);Net net(w);', 'input_gain=read_gain("LLVC_INPUT_GAIN",8);output_gain=read_gain("LLVC_OUTPUT_GAIN",4);\n    Weights w(model_path);Net net(w);')
s=s.replace('for(size_t i=0;i<got;i++)pending[i]=input[i]/32768.f;', 'for(size_t i=0;i<got;i++){float v=input[i]/32768.f;input_meter.add(v);pending[i]=std::max(-1.f,std::min(32767.f/32768.f,v*input_gain));}')
s=s.replace('float f=std::max(-1.f,std::min(32767.f/32768.f,y[i]));output[i]=int16_t(std::lrint(f*32768.f));', 'raw_meter.add(y[i]);float amplified=y[i]*output_gain;output_meter.add(amplified);\n            float f=std::max(-1.f,std::min(32767.f/32768.f,amplified));output[i]=int16_t(std::lrint(f*32768.f));')
s=s.replace('for(size_t i=0;i<CHUNK;i++)pending[LOOK+i]=i<got?input[i]/32768.f:0.f;', 'for(size_t i=0;i<CHUNK;i++){float v=i<got?input[i]/32768.f:0.f;if(i<got)input_meter.add(v);pending[LOOK+i]=std::max(-1.f,std::min(32767.f/32768.f,v*input_gain));}')
assert 'meter_window_input' in s
(root/'native_llvc_small96_meter.cpp').write_text(s,encoding='utf-8')
print('Created isolated meter candidate.')
