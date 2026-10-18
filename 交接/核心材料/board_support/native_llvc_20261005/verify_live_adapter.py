"""Verify PCM adapter lengths and first output without a full utterance."""
from pathlib import Path
import subprocess,json,time
import numpy as np
ROOT=Path(__file__).resolve().parent
exe=ROOT/'native_llvc_small96_stream_host.exe';model=ROOT/'small96_initial.f32'
wave=np.fromfile(ROOT/'real_16000.input.f32',dtype='<f4')
pcm=np.clip(np.rint(wave*32768),-32768,32767).astype('<i2')
rows=[]
for n in [0,1,16,207,208,209,224,416,16000]:
    x=pcm[:n];input_file=ROOT/'adapter_check.input.f32';output_file=ROOT/'adapter_check.output.f32'
    (x.astype(np.float32)/32768).tofile(input_file)
    r=subprocess.run([str(exe),str(model),str(input_file),str(output_file)],capture_output=True,check=True)
    y=np.fromfile(output_file,dtype='<f4')
    expected=np.clip(np.rint(np.clip(y,-1,32767/32768)*32768),-32768,32767).astype('<i2').tobytes()
    r=subprocess.run([str(exe),'--stream',str(model)],input=x.tobytes(),capture_output=True,check=True)
    assert len(r.stdout)==2*n and r.stdout==expected,(n,len(r.stdout))
    status=json.loads(r.stderr.decode());assert status['output_samples']==n
    rows.append(dict(samples=n,exact_pcm_match=True))
# Prefix produces a block while input remains open: no utterance buffering.
p=subprocess.Popen([str(exe),'--stream',str(model)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
p.stdin.write(pcm[:224].tobytes());p.stdin.flush()
start=time.perf_counter();prefix=p.stdout.read(416)
assert len(prefix)==416
first_seconds=time.perf_counter()-start
p.stdin.close();tail=p.stdout.read();err=p.stderr.read();assert p.wait(timeout=5)==0
assert len(tail)==32
report=dict(cases=rows,prefix_224_samples_produced_208_before_eof=True,
            host_prefix_wait_seconds=first_seconds,host_timing_is_not_board_latency=True,
            bounded_pending_samples=224,model_geometry='E96_D48_T13',actual_microphone_test=False)
(ROOT/'live_adapter_contract.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Full real10.38s source, PCM format for board's scheduled stream test.
full=np.fromfile(ROOT/'fleurs_full.input.f32',dtype='<f4')
np.clip(np.rint(full*32768),-32768,32767).astype('<i2').tofile(ROOT/'fleurs_full.s16')
print(json.dumps(report,indent=2))
