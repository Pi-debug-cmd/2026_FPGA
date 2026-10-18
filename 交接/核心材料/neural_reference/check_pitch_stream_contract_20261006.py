from pathlib import Path
import numpy as np,json,subprocess,hashlib,tarfile
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';out=base.parent/'board_budget_20261005/pitch_stream_contract';out.mkdir(exist_ok=True)
source=np.fromfile(native/'fixed_text_B_wide.input.f32',dtype=np.float32)
pcm=np.rint(np.clip(source,-1,32767/32768)*32768).astype('<i2');x=(pcm.astype('float32')/32768)
inp=out/'fixed_B_quantized.f32';inp.write_bytes(x.tobytes());dst=out/'fixed_B_normalized.f32';stats=out/'fixed_B_normalized.json'
exe=str(native/'causal_pitch_normalizer_host.exe')
subprocess.run([exe,str(inp),str(dst),str(stats)],check=True,capture_output=True)
r=subprocess.run([exe,'--stream',str(out/'stream_status.json')],input=pcm.tobytes(),check=True,capture_output=True)
y=np.fromfile(dst,dtype=np.float32);streamed=np.frombuffer(r.stdout,dtype='<i2');expected=np.rint(np.clip(y,-1,32767/32768)*32768).astype('<i2')
assert len(streamed)==len(expected),(len(streamed),len(expected))
assert np.array_equal(streamed,expected),np.max(np.abs(streamed.astype('int32')-expected.astype('int32')))
report=dict(samples=len(y),int16_stream_bit_exact_to_file_reference=True,float_input_quantized_first=True,public_synthetic_fixed_text=True,microphone_recorded=False,stats=json.loads(stats.read_text()),source_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),host_binary_sha256=hashlib.sha256(Path(exe).read_bytes()).hexdigest())
(out/'contract.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bundle=native/'pitch_normalizer_benchmark_20261006.tar.gz'
with tarfile.open(bundle,'w:gz') as t:
 t.add(native/'causal_pitch_normalizer_arm',arcname='causal_pitch_normalizer_arm')
 t.add(inp,arcname='pitch_benchmark.input.f32')
print('CONTRACT_PASSED',len(y),'BUNDLE',bundle.stat().st_size,flush=True)
