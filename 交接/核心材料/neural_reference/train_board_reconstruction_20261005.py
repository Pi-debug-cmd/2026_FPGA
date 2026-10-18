"""E128 codec restoration before conversion; no inference bypass or enrolled source.

Train only prior training speakers and target Tracks5-8. Exact waveform
reconstruction is a diagnostic/pretraining objective, never final conversion.
"""
from train_board_student_20261005 import BASE,CORPUS,build_small,export,stream,read,Objective
from pathlib import Path
import json,time,hashlib
import numpy as np
import torch
import torch.nn.functional as F
import soundfile as sf

OUT=BASE.parent/'board_budget_20261005/small128_reconstruction'
STEPS=800

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 torch.manual_seed(20261005+72);rng=np.random.default_rng(20261005+72);torch.set_num_threads(4)
 device='cuda';assert torch.cuda.is_available()
 doc=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'));rows=doc['files']
 train=[r for r in rows if r['split']=='train'];assert doc['complete']
 assert not ({r['speaker'] for r in train}&{r['speaker'] for r in rows if r['split']!='train'})
 paths=[Path(r['path']) for r in train]+[Path('D:/总进度/目标人物语音')/('Track '+str(i)+'.wav') for i in range(5,9)]
 data=[torch.tensor(read(p),device=device) for p in paths]
 model,cfg,selection=build_small(128);model=model.to(device).eval();objective=Objective(device)
 optimizer=torch.optim.AdamW(model.parameters(),lr=2e-4,betas=(.8,.99),weight_decay=0)
 length=208*154;warm=8192;history=[];begin=time.perf_counter()
 print('RESTORATION_READY',len(data),sum(p.numel() for p in model.parameters()),flush=True)
 for step in range(STEPS):
  batch=[]
  for _ in range(3):
   x=data[int(rng.integers(len(data)))];at=int(rng.integers(max(1,len(x)-length+1)))
   clip=x[at:at+length];clip=F.pad(clip,(0,length-len(clip)))
   rms=float(np.exp(rng.uniform(np.log(.01),np.log(.08))))
   clip=clip*(rms/clip.square().mean().sqrt().clamp_min(.0001));batch.append(clip.clamp(-.95,.95))
  source=torch.stack(batch);fake=model(source[:,None])[:,0][:,warm:];real=source[:,warm:]
  spectral=objective.loss(fake,real)
  waveform=(fake-real).abs().mean()/real.abs().mean().clamp_min(.001)
  quiet_source=torch.zeros(1,1,208*40,device=device)
  quiet=model(quiet_source)[:,0];quiet_loss=quiet.abs().mean()/.005
  loss=2*spectral+8*waveform+quiet_loss
  optimizer.zero_grad(set_to_none=True);assert torch.isfinite(loss);loss.backward()
  grad=torch.nn.utils.clip_grad_norm_(model.parameters(),5);assert torch.isfinite(grad);optimizer.step()
  if step%40==0 or step==STEPS-1:
   row=dict(step=step+1,loss=float(loss.detach()),spectral=float(spectral.detach()),waveform=float(waveform.detach()),quiet=float(quiet_loss.detach()),seconds=time.perf_counter()-begin)
   history.append(row);print('RESTORE',json.dumps(row),flush=True)
   (OUT/'training_status.json').write_text(json.dumps(dict(history=history,complete=False),indent=2))
 model=model.cpu().float().eval()
 torch.save(dict(model=model.state_dict(),config=cfg,selection=selection,steps=STEPS,conversion_trained=False,target_track9_used_for_training=False),OUT/'checkpoint_step800.pt')
 export(model,OUT/'small128_reconstruction.f32')
 outputs=[]
 for row in [r for r in rows if r['split']=='validation']:
  x=read(row['path']);y=stream(model,x);path=OUT/(Path(row['filename']).stem+'_student.wav');sf.write(path,y,16000,subtype='FLOAT')
  a,b=x[8192:],y[8192:]
  record=dict(row,student_path=str(path),normalized_waveform_rmse=float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-8)),correlation=float(np.corrcoef(a,b)[0,1]),rms=float(np.sqrt(np.mean(y*y))))
  outputs.append(record);print('RESTORE_STREAM',json.dumps(record),flush=True)
 report=dict(complete=True,history=history,heldout_outputs=outputs,config=cfg,parameters=sum(p.numel() for p in model.parameters()),steps=STEPS,training_paths=[str(p) for p in paths],training_speakers=sorted({r['speaker'] for r in train}),target_track9_used_for_training=False,conversion_trained=False,source_enrollment=False,quality_accepted=False,board_live_verified=False,weight_sha256=hashlib.sha256((OUT/'small128_reconstruction.f32').read_bytes()).hexdigest(),purpose='Restore small learned waveform codec; not final identity conversion')
 (OUT/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('RESTORATION_DONE',flush=True)
if __name__=='__main__':main()
