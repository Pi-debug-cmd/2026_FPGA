"""Explicit partial-band conversion experiment. Never claim complete target VC.
High-frequency input is intentionally retained; residual source identity exists.
All samples are prior public validation, not microphone recordings.
"""
from train_board_student_20261005 import BASE,CORPUS,read
from pathlib import Path
import json,sys,hashlib,time
import numpy as np,torch,soundfile as sf
from scipy.signal import firwin,lfilter

torch.set_num_threads(4);budget=BASE.parent/'board_budget_20261005';out=budget/'neural_band_hybrid';out.mkdir(exist_ok=True)
rows=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'))['files']
manifest=json.loads((BASE/'cross_evaluators/manifest.json').read_text());asset=next(r for r in manifest if r['evaluator'].startswith('UTMOS'))
assert hashlib.sha256(Path(asset['weight']['path']).read_bytes()).hexdigest()==asset['weight']['sha256'];sys.path.insert(0,asset['source_directory'])
from speechmos.utmos22.strong.model import UTMOS22Strong
mos=UTMOS22Strong();mos.load_state_dict(torch.load(asset['weight']['path'],map_location='cpu',weights_only=True));mos.eval()
def score(x):
 scores=[];weights=[]
 for t in range(0,len(x),96000):
  clip=x[t:t+96000]
  if len(clip)<24000:continue
  normalized=clip*.04/max(float(np.sqrt(np.mean(clip**2))),1e-8)
  with torch.inference_mode():s=float(mos(torch.tensor(normalized,dtype=torch.float32)[None],16000).item())
  scores.append(s);weights.append(len(clip))
 return float(np.average(scores,weights=weights))
records=[];started=time.monotonic()
for kind in ['small96_noise_refinement','small128_target_anchor_step400']:
 for cutoff in [1200,2200,3200]:
  name=kind+'_cut'+str(cutoff);folder=out/name;folder.mkdir(exist_ok=True)
  coefficients=firwin(63,cutoff,fs=16000,window='blackman').astype('float32');coefficients.tofile(folder/'lowpass63.f32')
  for row in [r for r in rows if r['split']=='validation']:
   x=read(row['path']);neural=read(budget/kind/(Path(row['filename']).stem+'_student.wav'));assert len(x)==len(neural)
   delayed=np.pad(x,(31,0))[:len(x)]
   # Same causal63-tap filter delays both branches by31samples, no offline alignment.
   y=(lfilter(coefficients,[1.],neural)+delayed-lfilter(coefficients,[1.],x)).astype('float32')
   path=folder/(Path(row['filename']).stem+'_student.wav');sf.write(path,y,16000,subtype='FLOAT')
   record=dict(row,kind=kind,cutoff_hz=cutoff,student_path=str(path),predicted_naturalness=score(y),rms=float(np.sqrt(np.mean(y*y))),peak=float(np.max(np.abs(y))),source_high_band_retained=True,full_target_voice_achieved=False)
   records.append(record);print('HYBRID',kind,cutoff,row['filename'],record['predicted_naturalness'],flush=True)
  decision=dict(complete=True,heldout_outputs=[r for r in records if r['kind']==kind and r['cutoff_hz']==cutoff],recognizer_used_as_loss=True,auxiliary_speaker_loss_used=True,source_high_band_retained=True,filter_taps=63,filter_group_delay_ms=31/16,quality_accepted=False,board_live_verified=False,full_target_voice_achieved=False)
  (folder/'decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf-8')
  (out/'status.json').write_text(json.dumps(dict(records=records,complete=False),ensure_ascii=False,indent=2),encoding='utf-8')
summary=[dict(kind=k,cutoff_hz=c,mean_predicted_naturalness=float(np.mean([r['predicted_naturalness'] for r in records if r['kind']==k and r['cutoff_hz']==c]))) for k in sorted({r['kind'] for r in records}) for c in [1200,2200,3200]]
(out/'report.json').write_text(json.dumps(dict(complete=True,records=records,summary=summary,seconds=time.monotonic()-started,source_high_band_retained=True,residual_source_identity=True,full_target_voice_achieved=False,utmos_used_for_development=True,chinese_domain_unvalidated=True,not_human_approval=True,not_unseen_test_acceptance=True),ensure_ascii=False,indent=2),encoding='utf-8')
print('HYBRID_SCREEN_DONE',json.dumps(summary),flush=True)
