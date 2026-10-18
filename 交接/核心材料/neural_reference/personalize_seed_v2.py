"""Official V2 CFM loss and optimizer, fixed target-only 99.14s pilot."""
import run_seed_v2_controls as vc
from pathlib import Path
import random,time,json
import torch,numpy as np,soundfile as sf,torchaudio
OUT=vc.OUT/'personal_training';OUT.mkdir(exist_ok=True)
SPLIT=Path('D:/总进度/目标人物分析/SeedVC人物微调/training_split.json')
def main():
 split=vc.read(SPLIT)
 for row in split['train_originals']:
  assert 'Track 9' not in row['path'] and vc.sha(row['path'])==row['sha256']
 for row in split['train_segments']:assert vc.sha(row['path'])==row['sha256']
 model,_=vc.load_models();model.requires_grad_(False)
 model.cfm.requires_grad_(True);model.cfm_length_regulator.requires_grad_(True)
 from optimizers import build_single_optimizer
 optimizer,scheduler=build_single_optimizer(model,lr=2e-5)
 random.seed(20261003);np.random.seed(20261003);torch.manual_seed(20261003)
 # Frozen extractors in eval; cache exactly the inputs used by forward_cfm.
 features=[]
 with torch.no_grad():
  for row in split['train_segments']:
   x,sr=sf.read(row['path'],dtype='float32');assert sr==model.sr
   wave=torch.from_numpy(x).unsqueeze(0).to('cuda');mel=model.mel_fn(wave)
   w16=torchaudio.functional.resample(wave,sr,16000)
   _,indices,lens=model.content_extractor_wide(w16,torch.tensor([w16.shape[-1]],device='cuda'))
   style=model.compute_style(w16,torch.tensor([w16.shape[-1]],device='cuda'))
   features.append((indices.cpu(),lens.cpu(),mel.cpu(),torch.tensor([mel.shape[-1]]),style.cpu()))
 model.cfm.train();model.cfm_length_regulator.train()
 # Upstream t.squeeze() turns the batch1 timestep into a scalar, although the
 # estimator expects one timestep per batch element. Restore that shape only.
 def batch1_timestep(module,args):
  return (*args[:3],args[3].reshape(-1),*args[4:])
 model.cfm.estimator.register_forward_pre_hook(batch1_timestep)
 initial={name:{k:v.detach().cpu().clone() for k,v in net.state_dict().items()} for name,net in [('cfm',model.cfm),('length_regulator',model.cfm_length_regulator)]}
 training=[];checkpoints=[];started=time.perf_counter();torch.cuda.reset_peak_memory_stats()
 order=list(range(len(features)))
 for step in range(300):
  if step%len(features)==0:random.shuffle(order)
  batch=[b.to('cuda') for b in features[order[step%len(features)]]]
  loss=model.forward_cfm(*batch)
  if not torch.isfinite(loss):raise RuntimeError('Nonfinite training loss')
  loss.backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1000.)
  if not torch.isfinite(norm):raise RuntimeError('Nonfinite gradients')
  optimizer.step();scheduler.step(step);optimizer.zero_grad()
  training.append(dict(step=step+1,loss=float(loss.detach()),grad_norm=float(norm)))
  if (step+1)%25==0:
   vc.save(OUT/'training_status.json',dict(status='running',steps=step+1,last=training[-1]))
   print(f'V2 TRAIN {step+1}/300 loss={float(loss.detach()):.5f}',flush=True)
  if step+1 in [100,300]:
   state={name:{k:v.detach().cpu() for k,v in net.state_dict().items()} for name,net in [('cfm',model.cfm),('length_regulator',model.cfm_length_regulator)]}
   if any(not torch.isfinite(v).all() for network in state.values() for v in network.values() if v.is_floating_point()):raise RuntimeError('Nonfinite weights')
   path=OUT/f'personal_v2_step{step+1:03}.pth';torch.save(dict(net=state,iters=step+1),path)
   changes={name:dict(float_tensor_count=sum(v.is_floating_point() for v in network.values()),
    changed_float_tensors=sum(v.is_floating_point() and not torch.equal(v,initial[name][k]) for k,v in network.items())) for name,network in state.items()}
   checkpoints.append(dict(path=str(path),sha256=vc.sha(path),step=step+1,weight_changes=changes))
 vc.save(OUT/'training_run.json',dict(status='complete',steps=300,batch_size=1,seed=20261003,precision='FP32',
  official_loss='VoiceConversionWrapper.forward_cfm',official_optimizer='build_single_optimizer lr2e-5 AdamW(.9,.98),eps1e-6,weight_decay.01',
  scheduler='official MinLRExponentialLR, gamma.999996,min1e-5; step(iteration)',grad_clip=1000.,
  split=split,checkpoints=checkpoints,training=training,wall_seconds=time.perf_counter()-started,
  peak_cuda_bytes=torch.cuda.max_memory_allocated(),source_revision='51383efd921027683c89e5348211d93ff12ac2a8',
  adaptations=['25 contiguous4s clips rather than random full up-to30s','batch1','Frozen feature/style networks stay eval; deterministic outputs cached',
   'Direct official forward_cfm instead of full wrapper; no unused AR loss',
   'Restore batch1 timestep shape after upstream squeeze; values/loss unchanged','Weights-only export, no resume optimizer'],
  heldout9_used_for_training=False,source_validation_used_for_training=False,source_speaker_enrollment=False,
  original_weights_overwritten=False,board_deployed=False,subjectively_accepted=False,audio_uploaded=False))
 vc.save(OUT/'training_status.json',dict(status='complete',steps=300,checkpoints=checkpoints))
 print('V2 PERSONAL TRAIN COMPLETE',flush=True)
if __name__=='__main__':main()
