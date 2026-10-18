from pathlib import Path
import sys,json
r=Path(__file__).resolve().parent;base=r.parents[1]/'neural_reference';sys.path[:0]=[str(r),str(base)]
from prepare_small_geometry import build_small,stream
import torch,numpy as np
out=r.parents[1]/'board_budget_20261005/small96_noise_refinement'
model,_,_=build_small(96);model.load_state_dict(torch.load(out/'checkpoint_step1200.pt',map_location='cpu',weights_only=True)['model'],strict=True);model.eval()
n=208*160;x=np.fromfile(r/'fleurs_full.input.f32',dtype='<f4')[:n];x*=.04/np.sqrt(np.mean(x*x))
with torch.inference_mode():full=model(torch.from_numpy(x)[None,None])[0,0].numpy()
online=stream(model,x);assert len(full)==len(online)==len(x)
cut=8192;a=full[cut:].astype('float64');b=online[cut:].astype('float64')
result={'test':'Public normalized speech, same checkpoint, full forward vs reference stream after first512ms',
 'full_rms':float(np.sqrt(np.mean(a*a))),'stream_rms':float(np.sqrt(np.mean(b*b))),
 'relative_difference_rms':float(np.sqrt(np.mean((a-b)**2))/np.sqrt(np.mean(a*a))),
 'correlation':float(np.corrcoef(a,b)[0,1]),'max_abs_difference':float(np.max(np.abs(a-b))),
 'source_enrollment':False,'user_audio_used':False}
(r/'full_vs_stream_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
