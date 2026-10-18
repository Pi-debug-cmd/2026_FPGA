from pathlib import Path
import numpy as np,subprocess,tarfile,json
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';out=base.parent/'board_budget_20261005/fargan_probe';out.mkdir(exist_ok=True)
x=np.fromfile(native/'fixed_text_B_wide.input.f32',dtype=np.float32);pcm=np.rint(np.clip(x,-1,32767/32768)*32768).astype('<i2');inp=out/'fixed_B.input.pcm';pcm.tofile(inp)
features=out/'fixed_B.features.f32';synth=out/'fixed_B.synth.pcm'
exe=str(native/'fargan_probe_host.exe')
subprocess.run([exe,'--features',str(inp),str(features),str(out/'host_features.json')],check=True)
subprocess.run([exe,'--synthesis',str(features),str(synth),str(out/'host_synthesis.json')],check=True)
assert np.isfinite(np.fromfile(features,dtype=np.float32)).all()
bundle=native/'fargan_probe_bundle_20261006.tar.gz'
with tarfile.open(bundle,'w:gz') as t:
 t.add(native/'fargan_probe_arm',arcname='fargan_probe_arm');t.add(inp,arcname='fargan_B.input.pcm');t.add(features,arcname='fargan_B.host_features.f32')
print('FARGAN_PROBE_READY',bundle.stat().st_size,json.loads((out/'host_synthesis.json').read_text()),flush=True)
