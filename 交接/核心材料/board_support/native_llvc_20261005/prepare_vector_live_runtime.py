from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'native_llvc_small128_vattn.cpp').read_text()
old=(root/'native_llvc_small96_meter.cpp').read_text()
includes='''#include <csignal>
#include <cerrno>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
'''
source=source.replace('#include <thread>',includes+'#include <thread>')
point=source.index('int main(int argc,char **argv)')
source=source[:point]+old[old.index('struct Meter {'):].replace('native_fp32_ring_candidate','native_fp32_vector_attention_candidate')
(root/'native_llvc_small128_vattn_meter.cpp').write_text(source)
helper=(root/'board_neural_calibrated.sh').read_text().replace('small96_noise_step9200.f32','small128_target_anchor_selected.f32').replace('native_llvc_small96_meter_arm','native_llvc_small128_vattn_meter_arm')
(root/'board_neural_small128.sh').write_text(helper,newline='\n')
original=(root/'board_original_accepted.sh').read_text().replace('        [ -f "$DIR/small96_step6400.f32" ]\n','')
(root/'board_original_accepted.sh').write_text(original,newline='\n')
