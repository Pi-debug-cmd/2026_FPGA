from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'native_llvc_wide192_shallow2_outpack.cpp').read_text()
old=(root/'native_llvc_small96_meter.cpp').read_text()
includes='''#include <csignal>
#include <cerrno>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
'''
source=source.replace('#include <thread>',includes+'#include <thread>')
source=source[:source.index('int main(int argc,char **argv)')]+old[old.index('struct Meter {'):].replace('native_fp32_ring_candidate','native_fp32_wide_packed_output_candidate')
(root/'native_llvc_wide192_shallow2_meter.cpp').write_text(source)
helper=(root/'board_neural_calibrated.sh').read_text().replace('small96_noise_step9200.f32','wide192_shallow2_target_anchor_selected.f32').replace('native_llvc_small96_meter_arm','native_llvc_wide192_shallow2_meter_arm')
(root/'board_neural_wide192.sh').write_text(helper,newline='\n')
