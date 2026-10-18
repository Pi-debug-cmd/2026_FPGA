from run_rvc_pilot import settings
settings()
from fargan_feature_mapper_20261006 import FeatureMapper,normalize_pitch
from pathlib import Path
import numpy as np,torch,json,subprocess,hashlib,tarfile
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005'
out=budget/'fargan_mapper_c_verification';out.mkdir(exist_ok=True)
checkpoint=torch.load(budget/'fargan_mapper_v1/checkpoint_step1200.pt',map_location='cpu',weights_only=False)
model=FeatureMapper(checkpoint['mean'],checkpoint['std']);model.load_state_dict(checkpoint['model']);model.eval();torch.set_num_threads(4)
manifest=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'))
row=next(r for r in manifest['files'] if r['split']=='validation');raw=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20)
raw.tofile(out/'input.f32')
with torch.inference_mode():gold,_=model(torch.tensor(normalize_pitch(raw))[None]);gold=gold[0].numpy()
gold.tofile(out/'reference.f32')
weight=budget/'fargan_mapper_v1/fargan_mapper_v1.f32'
subprocess.run([str(native/'fargan_mapper_probe_host.exe'),str(weight),str(out/'input.f32'),str(out/'host.f32'),str(out/'host.json')],check=True)
actual=np.fromfile(out/'host.f32',dtype='float32').reshape(-1,20)
report=dict(frames=len(raw),nrmse=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold)),max_abs=float(np.max(np.abs(actual-gold))),host_verified=False,quality_accepted=False)
assert report['nrmse']<1e-5 and report['max_abs']<1e-4,report
report['host_verified']=True
(out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bundle=native/'fargan_mapper_probe_bundle_20261006.tar.gz'
with tarfile.open(bundle,'w:gz') as tar:
    for p,name in [(native/'fargan_mapper_probe_arm','fargan_mapper_probe_arm'),(weight,'fargan_mapper_probe_v1.f32'),(out/'input.f32','fargan_mapper_probe_input.f32')]:tar.add(p,arcname=name)
report['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest();report['bundle_bytes']=bundle.stat().st_size
(out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
