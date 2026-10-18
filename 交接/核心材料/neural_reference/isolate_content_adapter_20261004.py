"""Fixed2x2 pretrained/personal module intervention, no extra training or EQ."""
from pathlib import Path
from types import SimpleNamespace
import time,json
import personalize_seed_teacher as personal
import torch,numpy as np,soundfile as sf,torchaudio
BASE=personal.BASE
OUT=Path('D:/总进度/目标人物分析/内容保持模块隔离_2026-10-04')
read=personal.read;save=personal.save;sha=personal.sha
def main():
 OUT.mkdir(exist_ok=True);inputs=OUT/'inputs';inputs.mkdir(exist_ok=True)
 old=read(Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04/evaluation_items.json'))
 raw=next(r for r in old if r.get('checkpoint') and 'amount' not in r)
 public=read(Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04/public_audio_manifest.json'))
 literal=read(Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04/literal_word_samples.json'))
 new_male=next(r for r in public['files'] if r['id']=='SSB0316_bie2')
 new_female=next(r for r in literal['files'] if r['target_character']=='这' and r['gender']=='female')
 sources=[dict(label='fleurs1906',path=raw['source_path'],sha256=raw['source_sha256'],text=raw['expected_text'],
  prepared=raw['prepared_source_path'] if 'prepared_source_path' in raw else str(personal.OUT/'test_inputs/fleurs_test_row0_id1906.wav')),
  dict(label='public_male_bie',path=new_male['path'],sha256=new_male['sha256'],text=new_male['text'],pinyin=new_male['pinyin'],speaker=new_male['speaker']),
  dict(label='public_female_zhe',path=new_female['path'],sha256=new_female['sha256'],text=new_female['text'],pinyin=new_female['pinyin'],speaker=new_female['speaker'])]
 target=Path(raw['reference_path']);assert sha(target)==raw['reference_sha256']
 assets,paths,get=personal.pinned_loaders();import inference
 original_path=Path(paths[('Plachta/Seed-VC','DiT_seed_v2_uvit_whisper_small_wavenet_bigvgan_pruned.pth')])
 original=torch.load(original_path,map_location='cpu',weights_only=True)['net']
 original={name:{key.removeprefix('module.'):value for key,value in net.items()} for name,net in original.items()}
 assert sha(raw['checkpoint']['path'])==raw['checkpoint']['sha256']
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,auto_f0_adjust=False,
  semi_tone_shift=0,checkpoint=raw['checkpoint']['path'],config=str(personal.OUT/'personal_strong_config.yml'),fp16=True)
 loaded=inference.load_models(SimpleNamespace(**kwargs));model=loaded[0];vocoder=loaded[3];mel=loaded[5]
 personal_states={name:{k:v.detach().cpu().clone() for k,v in net.state_dict().items()} for name,net in model.items()}
 assert set(personal_states)<=set(original)
 compatibility={}
 for name,network in model.items():
  learned={k for k,_ in network.named_parameters()};state=original[name]
  assert learned<=set(state),('Missing learned weights',name,learned-set(state))
  missing=set(personal_states[name])-set(state);extra=set(state)-set(personal_states[name])
  assert not (missing & learned)
  compatibility[name]=dict(deterministic_buffer_fills=sorted(missing),unused_checkpoint_keys=sorted(extra))
  original[name]={k:state[k] if k in state else personal_states[name][k] for k in personal_states[name]}
 original={name:original[name] for name in model}
 differences={}
 for name in original:
  num,den=0.,0.;maximum=0.
  for k,_ in model[name].named_parameters():
   v=original[name][k]
   delta=(personal_states[name][k]-v).float();num+=float(delta.square().sum());den+=float(v.float().square().sum());maximum=max(maximum,float(delta.abs().max()))
  differences[name]=dict(relative_l2=(num/max(den,1e-20))**.5,max_abs=maximum)
 cases=[('personal_both','personal','personal'),('base_content_personal_voice','base','personal'),
        ('personal_content_base_voice','personal','base'),('base_both','base','base')]
 save(OUT/'experiment_before_inference.json',dict(status='prepared',sources=sources,cases=cases,
  pretrained_path=str(original_path),pretrained_sha256=sha(original_path),personal_checkpoint=raw['checkpoint'],target_path=str(target),target_sha256=sha(target),
  model_module_drift=differences,checkpoint_nonlearned_compatibility=compatibility,seed=20261003,steps=30,cfg=.3,fp16=True,
  sole_interventions='2x2 learned length_regulator and CFM weights; semantic encoder, vocoder, target prompt, source, seed, CFG and steps fixed.',
  source_training_or_registration=False,new_training=False,postprocessing=False,model_is_offline_noncausal=True,board_deployed=False))
 source_records=[];records=[];captured={}
 def capture(m):captured['mel']=m.detach().cpu().numpy().copy();return vocoder(m)
 inference.load_models=lambda _:(*loaded[:3],capture,*loaded[4:])
 for source in sources:
  assert sha(source['path'])==source['sha256']
  if 'prepared' not in source:
   x,sr=sf.read(source['path'],dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
   x*=.04/max(float(np.sqrt(np.mean(x*x))),1e-8);p=inputs/(source['label']+'.wav');sf.write(p,x,sr,subtype='PCM_24');source['prepared']=str(p)
  source['prepared_sha256']=sha(source['prepared']);source_records.append(source)
  x,sr=sf.read(source['prepared'],dtype='float32')
  wave=torchaudio.functional.resample(torch.from_numpy(x).unsqueeze(0),sr,22050).to('cuda')
  with torch.inference_mode():native=vocoder(mel(wave)).squeeze().cpu().numpy()
  native*=min(.04/max(float(np.sqrt(np.mean(native*native))),1e-8),.95/max(float(np.max(np.abs(native))),1e-8))
  p=OUT/(source['label']+'_native_vocoder.wav');sf.write(p,native,22050,subtype='PCM_24')
  records.append(dict(label=source['label']+'_native_vocoder',group='native_vocoder',test_name=source['label'],path=str(p),sha256=sha(p),
    expected_text=source['text'],text_origin='Publisher real-speech transcript',source_path=source['path'],source_sha256=source['sha256'],role='diagnostic only; source identity retained'))
  for label,adapter,decoder in cases:
   for name,network in model.items():
    choice=adapter if name=='length_regulator' else decoder
    state=dict((original if choice=='base' else personal_states)[name])
    current=network.state_dict();learned={k for k,_ in network.named_parameters()}
    for key,value in state.items():
     if value.shape!=current[key].shape:
      assert key=='estimator.input_pos' and key not in learned
      assert torch.equal(value.cpu(),current[key].cpu()[:len(value)])
      state[key]=current[key] # Runtime positional cache grows under CFG; preserve it.
    network.load_state_dict(state,strict=True);network.eval()
   folder=OUT/label;folder.mkdir(exist_ok=True);torch.manual_seed(20261003);torch.cuda.synchronize();start=time.perf_counter()
   inference.main(SimpleNamespace(**kwargs,source=source['prepared'],target=str(target),output=str(folder)))
   torch.cuda.synchronize();elapsed=time.perf_counter()-start
   p=folder/f'vc_{Path(source["prepared"]).stem}_{target.stem}_1.0_30_0.3.wav'
   x,sr=sf.read(p,dtype='float32');assert np.isfinite(x).all() and float(np.sqrt(np.mean(x*x)))>1e-6
   np.savez_compressed(folder/(source['label']+'_generated_mel.npz'),mel=captured['mel'])
   reproduction=None
   if source['label']=='fleurs1906' and label=='personal_both':
    oldx,oldsr=sf.read(raw['path'],dtype='float32');assert oldsr==sr and oldx.shape==x.shape
    reproduction=float(np.max(np.abs(oldx-x)));assert reproduction==0,reproduction
   records.append(dict(label=label+'_'+source['label'],group=label,test_name=source['label'],path=str(p),sha256=sha(p),
     expected_text=source['text'],text_origin='Publisher real-speech transcript',source_path=source['path'],source_sha256=source['sha256'],
     content_module_origin=adapter,voice_module_origin=decoder,reference_path=str(target),reference_sha256=sha(target),
     seconds=len(x)/sr,rms=float(np.sqrt(np.mean(x*x))),peak=float(np.max(np.abs(x))),clipped_fraction=float(np.mean(np.abs(x)>=.999)),
     inference_seconds=elapsed,exact_baseline_reproduction_error=reproduction,
     subjective_acceptance=False,causal_streaming=False,board_deployed=False,source_speaker_enrollment=False))
   save(OUT/'evaluation_items.json',records);save(OUT/'source_manifest.json',source_records)
   print('DONE',source['label'],label,round(elapsed,2),'sec',flush=True)
 save(OUT/'run_status.json',dict(status='complete',cases=len(cases),sources=len(sources),new_target_conversion_count=12,new_training=False,active_jobs=0))
 print('CONTENT INTERVENTION COMPLETE',flush=True)
if __name__=='__main__':main()
