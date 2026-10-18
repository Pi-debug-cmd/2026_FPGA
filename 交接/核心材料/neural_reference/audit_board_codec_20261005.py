"""Public-input codec audit. Mask=1 is diagnostic only, not voice conversion."""
from pathlib import Path
import json,sys,types
import numpy as np,torch,soundfile as sf
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE.parent/'board_support/native_llvc_20261005'))
from prepare_small_geometry import build_small
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
OUT=BASE.parent/'board_budget_20261005/codec_reconstruction_audit';OUT.mkdir(exist_ok=True)
manifest=json.loads((BASE.parent/'board_budget_20261005/student_corpus/paired_manifest.json').read_text(encoding='utf-8'));row=next(r for r in manifest['files'] if r['split']=='validation')
x=read(row['path']);x=x*.04/np.sqrt(np.mean(x*x));x=x.astype('float32');torch.set_num_threads(4)
checks=[]
for name,checkpoint in [('initial96',None),('student6400',BASE.parent/'board_budget_20261005/small96_identity_training/checkpoint_step4000.pt'),('student9200',BASE.parent/'board_budget_20261005/small96_noise_refinement/checkpoint_step1200.pt'),('full512_original',None)]:
 m,cfg,_=build_small(96) if name!='full512_original' else (*load_model(True),None)
 if checkpoint:m.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['model'],strict=True)
 m=m.cpu().eval();m.mask_gen.forward=lambda e,l,a,b:(torch.ones_like(e),a,b)
 with torch.inference_mode():y=m(torch.from_numpy(x)[None,None])[0,0].numpy()
 assert len(y)==len(x);sf.write(OUT/(name+'_mask1.wav'),y,16000,subtype='FLOAT');a=x[8192:].astype('float64');b=y[8192:].astype('float64');gain=float(a@b/max(b@b,1e-20));err=np.sqrt(np.mean((a-b*gain)**2))/np.sqrt(np.mean(a*a))
 checks.append(dict(name=name,scale_adjusted_nrmse=float(err),fitted_gain=gain,correlation=float(np.corrcoef(a,b)[0,1]),input_rms=float(np.sqrt(np.mean(x*x))),output_rms=float(np.sqrt(np.mean(y*y))),diagnostic_not_conversion=True,wav=str(OUT/(name+'_mask1.wav'))));print(json.dumps(checks[-1]),flush=True)
 del m
report=dict(checks=checks,source_path=row['path'],source_text=row['text'],source_not_used_for_training_this_audit=True,mask1_diagnostic_not_final_mode=True)
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
