"""Generate an isolated timing build; preserve the verified baseline source."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / 'native_llvc.cpp').read_text(encoding='utf-8')
instrument = r'''
struct Timing { double inclusive=0, exclusive=0; unsigned calls=0; };
static std::map<std::string,Timing> timings;
struct Timer {
    std::string name; std::chrono::steady_clock::time_point start;
    double children; Timer *parent; static Timer *active;
    explicit Timer(std::string n):name(n),start(std::chrono::steady_clock::now()),children(0),parent(active){active=this;}
    ~Timer(){
        double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
        Timing &t=timings[name]; t.inclusive+=ms; t.exclusive+=ms-children; t.calls++;
        active=parent; if(parent)parent->children+=ms;
    }
};
Timer *Timer::active=0;
static void print_profile(){
    std::cout<<"{\"profile\":{";bool first=true;
    for(const auto &p:timings){
        if(!first)std::cout<<",";first=false;
        std::cout<<"\""<<p.first<<"\":{\"calls\":"<<p.second.calls
        <<",\"inclusive_ms\":"<<p.second.inclusive<<",\"exclusive_ms\":"<<p.second.exclusive<<"}";
    }
    std::cout<<"}}\n";
}
'''
source = source.replace('typedef std::vector<float> V;', instrument + '\ntypedef std::vector<float> V;')
marks = {
    'static V linear(const V &x,int frames,int in,int out,const V &w,const V &b){': 'linear_'+ '"+std::to_string(in)+"x"+std::to_string(out)+"_t"+std::to_string(frames)+"',
    'static void norm(V &v,int frames,int dim,const V &w,const V &b){': 'norm',
    '    V prenet(const V &x){': 'prenet',
    '    V encoder(V x){': 'encoder',
    '    V project_e2d(const V &x,const std::string &name){': 'project_e2d',
    '    V mha(const V &query,const V &memory,const std::string &p){': 'attention',
    '    V decoder(const V &e,const V &m){': 'decoder',
    '    V process(const float *shifted){': 'process',
}
for marker, name in marks.items():
    assert source.count(marker) == 1, marker
    source = source.replace(marker, marker + '\n        Timer timer("'+name+'");')
source = source.replace('        for(int t=0;t<T;t++)for(int c=0;c<E;c++)input',
                        '        {Timer timer("input_conv");\n        for(int t=0;t<T;t++)for(int c=0;c<E;c++)input')
source = source.replace('        dump("input",input);', '        }\n        dump("input",input);')
source = source.replace('        for(int t=0;t<17;t++)for(int c=0;c<E;c++){',
                        '        {Timer timer("output_conv");\n        for(int t=0;t<17;t++)for(int c=0;c<E;c++){')
source = source.replace('        dump("output",output);', '        }\n        dump("output",output);')
source = source.replace('        return 0;', '        print_profile();\n        return 0;')
(root / 'native_llvc_profile.cpp').write_text(source, encoding='utf-8')
print('Created separate native_llvc_profile.cpp; baseline unchanged.')
