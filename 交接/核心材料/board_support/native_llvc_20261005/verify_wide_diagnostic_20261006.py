from pathlib import Path
import os,subprocess,json,hashlib,numpy as np
r=Path(__file__).resolve().parent;out=r/'wide_diagnostic_verification_20261006';out.mkdir(exist_ok=True)
env=os.environ.copy();env['TEMP']=env['TMP']='D:/Tools_codex/temp'
env['LLVC_DIAG_TRIGGER']=str(out/'trigger.flag');env['LLVC_DIAG_PREFIX']=str(out/'capture')
w=str(r/'wide192_shallow2_target_anchor_selected.f32')
fixed=np.fromfile(r/'fixed_text_B_wide.input.f32',dtype='<f4');pcm=np.clip(np.rint(fixed*32768),-32768,32767).astype('<i2')
checks=[]
for n in (0,1,207,224,16000,len(pcm)):
 data=pcm[:n].tobytes();(out/'trigger.flag').write_text('save')
 a=subprocess.run([str(r/'native_llvc_wide192_meter_parity_host.exe'),'--stream',w],input=data,capture_output=True,env=env,check=True)
 b=subprocess.run([str(r/'native_llvc_wide192_diag120_host.exe'),'--stream',w],input=data,capture_output=True,env=env,check=True)
 assert a.stdout==b.stdout,(n,'changed waveform')
 assert (out/'capture.input.s16').read_bytes()==data,(n,'input mismatch')
 assert (out/'capture.output.s16').read_bytes()==b.stdout,(n,'output mismatch')
 checks.append(dict(samples=n,output_bit_exact=True,captured_input_exact=True,captured_output_exact=True))
# Force the ring through wrap without running 120s of model processing.
code=r'''#define main original_entry
#include "native_llvc_wide192_diag120.cpp"
#undef main
int main(){
 for(size_t at=0;at<DIAG_KEEP+208;at+=208){
   int16_t x[208],y[208];for(size_t i=0;i<208;i++){x[i]=int16_t((at+i)%30000);y[i]=int16_t(-((at+i)%30000));}
   diag_read(x,208);diag_write(y,208);
 }
 int16_t look[16];for(size_t i=0;i<16;i++)look[i]=int16_t((diag_produced+i)%30000);diag_read(look,16);
 diag_dump();return 0;
}
'''
(r/'wide_diag_ring_wrap_test.cpp').write_text(code,encoding='utf-8')
host='D:/Vivado/Vivado/2018.3/tps/mingw/6.2.0/win64.o/nt/bin/g++.exe'
subprocess.run([host,'-std=c++11','-O3','-static','-pthread',str(r/'wide_diag_ring_wrap_test.cpp'),'-o',str(out/'ring_wrap_test.exe')],check=True,env=env)
(out/'trigger.flag').write_text('save');subprocess.run([str(out/'ring_wrap_test.exe')],check=True,env=env)
meta=json.loads((out/'capture.json').read_text());expected=(np.arange(meta['start_sample'],meta['end_sample'])%30000).astype('<i2')
assert np.array_equal(expected,np.fromfile(out/'capture.input.s16',dtype='<i2'))
assert np.array_equal(-expected,np.fromfile(out/'capture.output.s16',dtype='<i2'))
report=dict(checks=checks,ring_wrap=dict(**meta,input_exact=True,output_exact=True),passed=True,
            arm_sha256=hashlib.sha256((r/'native_llvc_wide192_diag120_arm').read_bytes()).hexdigest(),
            weights_sha256=hashlib.sha256(Path(w).read_bytes()).hexdigest(),disk_dump_only_after_stream_ends=True)
(out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
