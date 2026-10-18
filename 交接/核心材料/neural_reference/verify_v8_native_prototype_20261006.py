"""Untrained random-weight native budget probe, explicitly NOT audio quality."""
from run_rvc_pilot import settings
settings()
from fargan_mapper_v8_20261006 import MapperV8,pitch_aware_features
from fargan_feature_mapper_20261006 import export_mapper
from pathlib import Path
import torch,numpy as np,json,subprocess,tarfile,hashlib
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005';out=budget/'fargan_v8_native_prototype';out.mkdir(exist_ok=True)
torch.set_num_threads(4);torch.manual_seed(20261006+87)
old=torch.load(budget/'fargan_mapper_pitchaware/checkpoint_step3000.pt',map_location='cpu',weights_only=False);model=MapperV8(old['mean'],old['std']).eval()
with torch.no_grad():model.head.weight.normal_(0,.005);model.head.bias.normal_(0,.005)
raw=np.fromfile(budget/'fargan_probe/fixed_B.features.f32',dtype='float32').reshape(-1,20);raw.tofile(out/'input.f32')
with torch.inference_mode():gold,_=model(torch.tensor(pitch_aware_features(raw))[None]);gold=gold[0].numpy()
gold.tofile(out/'reference.f32');weight=out/'prototype_v8.f32';export_mapper(model,weight)
subprocess.run([str(native/'fargan_mapper_probe_v8_host.exe'),str(weight),str(out/'input.f32'),str(out/'host.f32'),str(out/'host.json')],check=True)
actual=np.fromfile(out/'host.f32',dtype='float32').reshape(-1,20);report=dict(parameters=sum(p.numel() for p in model.parameters()),nrmse=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold)),max_abs=float(np.max(np.abs(actual-gold))),random_untrained_weights=True,quality_accepted=False,board_live_deployed=False)
assert report['nrmse']<1e-5 and report['max_abs']<1e-4
bundle=native/'fargan_v8_prototype_bundle_20261006.tar.gz'
with tarfile.open(bundle,'w:gz',compresslevel=9) as t:
    for p,name in [(native/'fargan_mapper_probe_v8_arm','fargan_mapper_probe_v8_arm'),(weight,'prototype_v8.f32'),(out/'input.f32','prototype_v8_input.f32')]:t.add(p,arcname=name)
report['bundle_bytes']=bundle.stat().st_size;report['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest();(out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
