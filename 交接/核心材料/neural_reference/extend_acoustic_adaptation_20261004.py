"""Frozen vocoder, longer official target acoustic adaptation; real conversions only.
Weights-only restart from personal300: optimizer/scheduler are explicitly reset.
"""
from pathlib import Path
from types import SimpleNamespace
import random,time,sys,json
import numpy as np,soundfile as sf,torch,yaml
import personalize_seed_teacher as personal
BASE=personal.BASE;OLD=personal.OUT;DIAG=Path('D:/总进度/目标人物分析/自然度与鼻音排查_2026-10-04')
OUT=Path('D:/总进度/目标人物分析/声学生成改进_2026-10-04');OUT.mkdir(exist_ok=True)
read=personal.read;save=personal.save;sha=personal.sha
def feedback():
 d=read(DIAG/'decision.json');d.update(status='human_reconstruction_near_original_conversion_not_accepted',
  hearing_result='reconstruction_much_better_near_original',human_component_feedback='这个好很多，已经很接近了',
  human_component_feedback_date='2026-10-04',subjective_acceptance=False,
  component_interpretation='Native target mel reconstruction much better; prioritize acoustic generator. Not source-to-target success and does not exonerate vocoder on generated mel.',
  next_step='Keep frozen BigVGAN; test additional target acoustic adaptation, no envelope correction.');save(DIAG/'decision.json',d)
 save(OUT/'component_feedback.json',dict(date='2026-10-04',feedback='这个好很多，已经很接近了',
  applies_to='Target9 waveform to native mel to BigVGAN only',conversion_accepted=False,
  next_hypothesis='Acoustic generator and target adaptation are priorities, cause not fully confirmed.'))
 heading='## 最新：原声重建接近，转向声学生成改进（2026-10-04）'
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 if heading not in s:
  t=heading+'\n\n用户对12秒“目标原声→同原声仅声码器重建”反馈“这个好很多，已经很接近了”。这是组件重建的积极反馈，不能当他人→目标人物转换验收。原生目标频谱能较好重建，优先检查声学转换模型生成频谱及人物适配；仍不能排除声码器在生成频谱上的失真。停止额外包络强度调节，保持BigVGAN不变，隔离测试个人300步模型再进行700步目标声学适配（权重从300初始化，优化器/调度器重置，非完整训练状态续训），保存累计600/1000步两个节点，固定相同4个普通输入和Track6前8秒参考直接转换。训练仅Track5—8，Track9只作反复诊断，无源人注册或新补录。电脑处理进行中，无需板卡上电，实时/7020目标仍未实现。此条覆盖历史待重建试听状态。\n\n'
  s=s.replace('## 最新：两版均有不自然鼻音，',t+'## 最新：两版均有不自然鼻音，',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');heading='## Latest: native target reconstruction near original; acoustic adaptation control — 2026-10-04'
 if heading not in s:
  first,rest=s.split('\n',1);s=first+'\n\n'+heading+'\n\nUser reports target-only reconstruction much better/near original. This is NOT conversion acceptance; prioritize acoustic generation while retaining frozen vocoder, not proven to be sole cause. Additional700 official target-only steps initialized from personal300, optimizer/scheduler reset (not full-state resumption); save cumulative600/1000. Same4 prepared ordinary sources/ref; no envelope correction/source enrollment/Track9 training/new recording/board action. PC control in progress; supersedes pending reconstruction question.\n'+rest;p.write_text(s,encoding='utf-8')
def train_control():
 split=read(OLD/'training_split.json')
 for r in split['train_segments']+split['train_originals']:assert sha(r['path'])==r['sha256']
 assert {Path(r['path']).name for r in split['train_originals']}=={f'Track {n}.wav' for n in range(5,9)}
 save(OUT/'training_split.json',split)
 cfg=yaml.safe_load((OLD/'personal_strong_config.yml').read_text(encoding='utf-8'));cfg['log_dir']=str(OUT/'runs')
 config=OUT/'acoustic_control.yml';config.write_text(yaml.safe_dump(cfg,allow_unicode=True),encoding='utf-8')
 assets,paths,get=personal.pinned_loaders();import train
 train.load_custom_model_from_hf=get;train.Trainer.build_vocoder=lambda self,device,config:setattr(self,'vocoder_fn',None)
 ckpt=next(r for r in read(OLD/'training_run.json')['checkpoints'] if r['step']==300);assert sha(ckpt['path'])==ckpt['sha256']
 random.seed(20261004);np.random.seed(20261004);torch.manual_seed(20261004)
 trainer=train.Trainer(str(config),ckpt['path'],str(OLD/'training_audio'),'additional700_from300',batch_size=1,num_workers=0,
  steps=700,max_epochs=1000,device='cuda:0')
 trainer.whisper_model.eval().requires_grad_(False);trainer.campplus_model.eval().requires_grad_(False)
 trainer.tone_color_converter.model.eval().requires_grad_(False)
 state=torch.load(ckpt['path'],map_location='cpu',weights_only=True)['net'];counts={}
 for name,net in trainer.model.items():
  for key,p in net.named_parameters():assert torch.equal(p.detach().cpu(),state[name][key]),name+'/'+key
  counts[name]=sum(p.numel() for p in net.parameters());net.train()
 del state
 ov=torch.load(paths[('myshell-ai/OpenVoiceV2','converter/checkpoint.pth')],map_location='cpu',weights_only=True)['model']
 for name,p in trainer.tone_color_converter.model.named_parameters():assert name in ov and ov[name].shape==p.shape
 del ov
 assert all(not trainer.optimizer.optimizers[n].state for n in trainer.optimizer.keys)
 started=time.perf_counter();rows=[];checkpoints=[];torch.cuda.reset_peak_memory_stats()
 try:
  while len(rows)<700:
   for batch in trainer.train_dataloader:
    batch=[b.to(trainer.device) for b in batch];loss=trainer.train_one_step(batch)
    assert np.isfinite(loss);step=len(rows)+1;rows.append(dict(additional_step=step,cumulative_step=300+step,loss=loss))
    if step%25==0:
     save(OUT/'training_progress.json',dict(status='running',additional_steps=step,cumulative_steps=300+step,last_loss=loss))
     print('TRAIN',step,'/700 loss',round(loss,5),flush=True)
    if step in {300,700}:
     for net in trainer.model.values():assert all(torch.isfinite(p).all() for p in net.parameters())
     dest=OUT/f'personal_total{300+step}.pth'
     torch.save(dict(net={name:{k:v.detach().cpu() for k,v in net.state_dict().items()} for name,net in trainer.model.items()}),dest)
     checkpoints.append(dict(step=300+step,additional_steps=step,path=str(dest),sha256=sha(dest)))
    if len(rows)>=700:break
  torch.cuda.synchronize()
  save(OUT/'training_run.json',dict(status='complete',initial_checkpoint=ckpt,additional_steps=700,cumulative_steps=1000,
   optimizer_scheduler_reset=True,full_state_resume=False,learning_rate=1e-5,batch_size=1,training_seed=20261004,
   loss='unchanged official train.Trainer.train_one_step',precision='FP32',source_revision='51383efd921027683c89e5348211d93ff12ac2a8',
   checkpoints=checkpoints,training_rows=rows,wall_seconds=time.perf_counter()-started,parameter_counts=counts,
   peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),config=str(config),config_sha256=sha(config),assets=assets,
   source_validation_used_for_training=False,track9_used_for_training=False,source_speaker_enrollment=False,
   vocoder_adapted=False,original_checkpoint_preserved=sha(ckpt['path'])==ckpt['sha256'],audio_uploaded=False,
   subjective_acceptance=False,board_deployed=False))
  save(OUT/'training_progress.json',dict(status='complete',additional_steps=700,checkpoints=checkpoints))
 except Exception as e:
  save(OUT/'training_progress.json',dict(status='failed',additional_steps=len(rows),error=repr(e)));raise
 print('ACOUSTIC TRAINING COMPLETE',flush=True)
def infer_control():
 personal.pinned_loaders();import inference
 run=read(OUT/'training_run.json');rows=read(Path('D:/总进度/目标人物分析/局部音色包络校正/smoothed_items.json'))
 loader=inference.load_models;records=[]
 for ckpt in run['checkpoints']:
  assert sha(ckpt['path'])==ckpt['sha256']
  kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,auto_f0_adjust=False,
   semi_tone_shift=0,checkpoint=ckpt['path'],config=run['config'],fp16=True)
  loaded=loader(SimpleNamespace(**kwargs));inference.load_models=lambda _:loaded
  group='acoustic_total'+str(ckpt['step']);folder=OUT/group;folder.mkdir(exist_ok=True)
  for r in rows:
   assert sha(r['prepared_source_path'])==r['prepared_source_sha256'] and sha(r['source_path'])==r['source_sha256']
   source=Path(r['prepared_source_path']);ref=Path(r['reference_path']);torch.manual_seed(20261003)
   torch.cuda.synchronize();started=time.perf_counter()
   inference.main(SimpleNamespace(**kwargs,source=str(source),target=str(ref),output=str(folder)))
   torch.cuda.synchronize();elapsed=time.perf_counter()-started
   dest=folder/f'vc_{source.stem}_{ref.stem}_1.0_30_0.3.wav';y,sr=sf.read(dest)
   assert np.isfinite(y).all() and np.sqrt(np.mean(y*y))>1e-6 and np.max(np.abs(y))<.999
   row=dict(r,label=group+'_'+r['test_name'],group=group,path=str(dest),sha256=sha(dest),checkpoint=ckpt,
    amount=0,cepstral_correction_applied=False,causal_envelope_ema_seconds=None,fp16=True,diffusion_steps=30,cfg=.3,
    seed=20261003,seconds=len(y)/sr,offline_file_seconds=elapsed,reference_sha256=sha(ref),
    human_feedback=None,subjective_acceptance=False,causal_streaming=False)
   records.append(row);save(OUT/'conversion_items.json',records);print('OUTPUT',row['label'],flush=True)
  inference.load_models=loader;del loaded;torch.cuda.empty_cache()
 save(OUT/'inference_run.json',dict(status='complete',conversions=len(records),files=records,subjective_acceptance=False,
  target_reconstruction_included=False,board_deployed=False,script_sha256=sha(__file__)))
 print('ACOUSTIC INFERENCE COMPLETE',flush=True)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='infer':infer_control()
 else:feedback();train_control()
