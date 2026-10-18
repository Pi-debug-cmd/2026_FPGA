"""E128 native-budget VC, restored codec + genuine target reconstruction anchor.

Actual online network outputs are fully neural, without input bypass, speaker
enrollment, text synthesis or lookahead beyond the existing 14ms contract.
Heavy Chinese/speaker networks are frozen offline training aids only.
"""
from train_board_student_20261005 import BASE,CORPUS,build_small,export,stream,read,Objective,PeriodDiscriminator
from pathlib import Path
import json,time,hashlib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import soundfile as sf
from differentiable_chinese_ctc_20261005 import FrozenChineseCTC
from run_sensevoice_pinyin_validation_20261004 import load_frontend
from differentiable_speaker_20261005 import FrozenSpeaker

OUT=BASE.parent/'board_budget_20261005/small128_target_anchor'
PARENT=BASE.parent/'board_budget_20261005/small128_reconstruction/checkpoint_step800.pt'
STEPS=2400

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 torch.manual_seed(20261005+73);rng=np.random.default_rng(20261005+73);torch.set_num_threads(4)
 device='cuda';assert torch.cuda.is_available()
 doc=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'));assert doc['complete'];rows=doc['files']
 training=[r for r in rows if r['split']=='train']
 assert not ({r['speaker'] for r in training}&{r['speaker'] for r in rows if r['split']!='train'})
 data=[]
 for row in training:
  x,y=read(row['path']),read(row['teacher_path']);assert abs(len(x)-len(y))<=1600
  y=np.pad(y,(0,max(0,len(x)-len(y))))[:len(x)]
  data.append((torch.tensor(x,device=device),torch.tensor(y,device=device)))
 target_paths=[Path('D:/总进度/目标人物语音')/('Track '+str(i)+'.wav') for i in range(5,9)]
 target_data=[torch.tensor(read(p),device=device) for p in target_paths]
 model,cfg,selection=build_small(128);parent=torch.load(PARENT,map_location='cpu',weights_only=True)
 model.load_state_dict(parent['model'],strict=True);model=model.to(device).eval()
 content=FrozenChineseCTC().to(device).eval();frontend=load_frontend().to(device).eval()
 verification=json.loads((BASE.parent/'board_support/native_llvc_20261005/differentiable_chinese_ctc_verification.json').read_text())
 assert content.model_sha256==verification['model_sha256'] and verification['waveform_gradient_finite']
 ctc=nn.CTCLoss(blank=0,reduction='mean',zero_infinity=False)
 def logits(wave):
  norm=wave/wave.abs().amax(dim=-1,keepdim=True).detach().clamp_min(1e-7)
  feats,lens=frontend(norm,torch.full((wave.shape[0],),wave.shape[-1],dtype=torch.int64))
  _,lp,n=content(feats,lens);return lp,n
 def transcript_loss(fake,clean):
  with torch.no_grad():
   lp,n=logits(clean);labels=[];lengths=[]
   for b in range(clean.shape[0]):
    ids=lp[:int(n[b]),b].argmax(dim=-1).tolist();last=0;seq=[]
    for k in ids:
     if k and k!=last:seq.append(k)
     last=k
    labels.extend(seq);lengths.append(len(seq))
  predicted,pn=logits(fake)
  return ctc(predicted,torch.tensor(labels,dtype=torch.long,device=device),pn.cpu().long(),torch.tensor(lengths,dtype=torch.long))
 speaker=FrozenSpeaker().to(device).eval()
 with torch.no_grad():reference=speaker.embedding(torch.tensor(read('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav'),device=device))
 objective=Objective(device);discs=nn.ModuleList([PeriodDiscriminator(p) for p in [2,3,5]]).to(device)
 go=torch.optim.AdamW(model.parameters(),lr=8e-5,betas=(.8,.99),weight_decay=0)
 do=torch.optim.AdamW(discs.parameters(),lr=1e-4,betas=(.8,.99),weight_decay=0)
 length=208*154;warm=8192;timeline=torch.arange(length,device=device)/16000
 def crop(x,at=None):
  if at is None:at=int(rng.integers(max(1,len(x)-length+1)))
  clip=x[at:at+length];return F.pad(clip,(0,length-len(clip))),at
 def colored(rms):
  z=torch.randn(length//16+1,device=device)
  color=F.interpolate(z[None,None],size=length,mode='linear',align_corners=False)[0,0]
  x=.7*color+.15*torch.randn(length,device=device)+.2*torch.sin(2*torch.pi*float(rng.choice([50,60]))*timeline)
  return x*(rms/x.square().mean().sqrt().clamp_min(1e-8))
 history=[];start=time.perf_counter();print('TARGET_ANCHOR_READY',len(data),STEPS,sum(p.numel() for p in model.parameters()),flush=True)
 for step in range(STEPS):
  xs=[];ys=[];clean=[]
  for _ in range(2):
   x,y=data[int(rng.integers(len(data)))];xx,at=crop(x);yy,_=crop(y,at);clean.append(xx)
   desired_rms=float(np.exp(rng.uniform(np.log(.01),np.log(.08))))
   xx=xx*(desired_rms/xx.square().mean().sqrt().clamp_min(.0001))
   if rng.random()<.2:
    snr=float(rng.uniform(20,35));xx=xx+colored(float(xx.square().mean().sqrt())/10**(snr/20))
   xs.append(xx.clamp(-.95,.95));ys.append(yy)
  anchor,_=crop(target_data[int(rng.integers(len(target_data)))])
  anchor=anchor*(.06/anchor.square().mean().sqrt().clamp_min(.0001));anchor=anchor.clamp(-.8,.8)
  anchor_input=anchor*float(rng.uniform(.5,1.3))
  quiet_rms=float(np.exp(rng.uniform(np.log(.00005),np.log(.0015))))
  quiet=colored(quiet_rms) if step%3 else torch.zeros(length,device=device)
  source=torch.stack(xs+[anchor_input,quiet]);prediction=model(source[:,None])[:,0].float()
  assert torch.isfinite(prediction).all()
  fake=prediction[:2,warm:];real=torch.stack(ys)[:,warm:]
  anchor_fake=prediction[2:3,warm:];anchor_real=anchor[None,warm:];quiet_fake=prediction[3,warm:]
  adversarial=step>=200
  if adversarial:
   for p in discs.parameters():p.requires_grad_(True)
   do.zero_grad(set_to_none=True);dl=0
   for disc in discs:
    a,_=disc(real[:,None]);b,_=disc(fake.detach()[:,None]);dl+=((a-1)**2).mean()+b.square().mean()
   dl.backward();torch.nn.utils.clip_grad_norm_(discs.parameters(),5);do.step()
  for p in discs.parameters():p.requires_grad_(False)
  go.zero_grad(set_to_none=True)
  spectral=objective.loss(fake,real)
  anchor_spectral=objective.loss(anchor_fake,anchor_real)
  anchor_wave=(anchor_fake-anchor_real).abs().mean()/anchor_real.abs().mean().clamp_min(.001)
  cl=transcript_loss(fake,torch.stack(clean)[:,warm:])
  identity=1-(speaker.embedding(fake)*reference).sum(dim=-1).mean()
  quiet_loss=quiet_fake.abs().mean()/.005+quiet_fake.square().mean()/.0001
  gl=torch.tensor(0.,device=device);fm=torch.tensor(0.,device=device)
  if adversarial:
   for disc in discs:
    score,maps=disc(fake[:,None]);gl+=((score-1)**2).mean()
    with torch.no_grad():_,truth=disc(real[:,None])
    fm+=sum(F.l1_loss(a,b) for a,b in zip(maps,truth))/len(maps)
  loss=5*spectral+2*cl+.75*identity+2*anchor_spectral+8*anchor_wave+3*quiet_loss+(.3*gl+fm if adversarial else 0)
  assert torch.isfinite(loss);loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),5);assert torch.isfinite(grad);go.step()
  if step%40==0 or step==STEPS-1:
   record=dict(step=step+1,seconds=time.perf_counter()-start,loss=float(loss.detach()),spectral=float(spectral.detach()),pinyin_ctc=float(cl.detach()),identity=float(identity.detach()),anchor_spectral=float(anchor_spectral.detach()),anchor_waveform=float(anchor_wave.detach()),quiet=float(quiet_loss.detach()),adversarial=float(gl.detach()),feature_match=float(fm.detach()),rms=float(fake.detach().square().mean().sqrt()))
   history.append(record);print('ANCHOR',json.dumps(record),flush=True)
   (OUT/'training_status.json').write_text(json.dumps(dict(history=history,complete=False),indent=2))
  if (step+1)%400==0:
   torch.save(dict(model={k:v.detach().cpu() for k,v in model.state_dict().items()},config=cfg,selection=selection,steps=step+1,reconstruction_steps=800,conversion_trained=True,target_track9_used_for_training=False,quality_accepted=False),OUT/('checkpoint_step'+str(step+1)+'.pt'))
 model=model.cpu().float().eval();export(model,OUT/'small128_target_anchor.f32');outputs=[]
 for row in [r for r in rows if r['split']=='validation']:
  x=read(row['path']);y=stream(model,x);path=OUT/(Path(row['filename']).stem+'_student.wav');sf.write(path,y,16000,subtype='FLOAT')
  outputs.append(dict(row,student_path=str(path),rms=float(np.sqrt(np.mean(y*y))),peak=float(np.max(np.abs(y))),human_acceptance=False))
 report=dict(complete=True,history=history,heldout_outputs=outputs,config=cfg,parameters=sum(p.numel() for p in model.parameters()),steps=STEPS,reconstruction_steps=800,training_speakers=sorted({r['speaker'] for r in training}),target_anchor_paths=[str(p) for p in target_paths],target_track9_used_for_training=False,teacher_waveform_time_warp=False,source_enrollment=False,recognizer_used_as_loss=True,recognizer_is_not_independent=True,auxiliary_speaker_loss_used=True,wespeaker_is_not_independent=True,utmos_used_in_training=False,quality_accepted=False,board_live_verified=False,parent_path=str(PARENT),parent_sha256=hashlib.sha256(PARENT.read_bytes()).hexdigest(),weights_sha256=hashlib.sha256((OUT/'small128_target_anchor.f32').read_bytes()).hexdigest(),checkpoint_selection='fixed2400step_endpoint',runtime_no_original_mix=True)
 (OUT/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('TARGET_ANCHOR_DONE',flush=True)
if __name__=='__main__':main()
