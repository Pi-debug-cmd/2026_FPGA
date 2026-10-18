from run_rvc_pilot import settings
settings()
from fargan_feature_mapper_20261006 import PitchAwareMapper,pitch_aware_features
from pathlib import Path
import torch,numpy as np,subprocess,json
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005';out=budget/'fargan_pitchaware_c_verification';out.mkdir(exist_ok=True)
trained=budget/'fargan_mapper_pitchaware';checkpoint=torch.load(trained/'checkpoint_step3000.pt',map_location='cpu',weights_only=False)
model=PitchAwareMapper(checkpoint['mean'],checkpoint['std']);model.load_state_dict(checkpoint['model'],strict=True);model.eval();torch.set_num_threads(4)
manifest=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'));row=next(r for r in manifest['files'] if r['split']=='validation');raw=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20)
with torch.inference_mode():gold,_=model(torch.tensor(pitch_aware_features(raw))[None]);gold=gold[0].numpy()
subprocess.run([str(native/'fargan_mapper_probe_host.exe'),str(trained/'fargan_mapper_pitchaware.f32'),row['source_features'],str(out/'actual.f32'),str(out/'stats.json')],check=True)
actual=np.fromfile(out/'actual.f32',dtype='float32').reshape(-1,20);report=dict(nrmse=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold)),max_abs=float(np.max(np.abs(actual-gold))),native_c_verified=False,quality_accepted=False)
assert report['nrmse']<1e-5 and report['max_abs']<1e-4;report['native_c_verified']=True
(out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
