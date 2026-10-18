from pathlib import Path
import sys,json,hashlib,tarfile
r=Path(__file__).resolve().parent;base=r.parents[1]/'neural_reference';sys.path[:0]=[str(base),str(r)]
from run_rvc_pilot import settings
settings()
import torch,numpy as np
from prepare_small_geometry import build_small,stream
out=r.parents[1]/'board_budget_20261005/small96_noise_refinement'
decision=json.loads((out/'decision.json').read_text(encoding='utf-8'));assert decision['complete'] and decision['parameters']==173456
model,cfg,_=build_small(96);model.load_state_dict(torch.load(out/'checkpoint_step1200.pt',map_location='cpu',weights_only=True)['model'],strict=True);model.eval()
x=np.fromfile(r/'real_16000.input.f32',dtype='<f4');y=stream(model,x);assert len(y)==len(x) and np.isfinite(y).all()
y.tofile(r/'real_16000.small96_step9200.torch.f32')
s=(r/'board_neural_meter.sh').read_text(encoding='utf-8').replace('small96_step6400.f32','small96_noise_step9200.f32')
s=s.replace('Headphone 95,95','Headphone 101,101').replace('Playback 210,210','Playback 222,222')
(r/'board_neural_noise.sh').write_text(s,encoding='utf-8',newline='\n')
with tarfile.open(r/'noise_refine_candidate_bundle.tar.gz','w:gz') as t:
    t.add(out/'small96_noise_step9200.f32',arcname='small96_noise_step9200.f32')
    t.add(r/'board_neural_noise.sh',arcname='board_neural_noise.sh')
print(json.dumps({'weight_sha256':decision['weights_sha256'],'bundle_bytes':(r/'noise_refine_candidate_bundle.tar.gz').stat().st_size,'torch_reference_samples':len(y),'model_size_unchanged':True}))
