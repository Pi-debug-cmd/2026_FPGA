"""V1 cause isolation: vocoder round-trip, reference prompt, fixed mean style.
Target reconstruction is diagnostic ONLY, never source-to-target conversion.
"""
from pathlib import Path
from types import SimpleNamespace
import json,time,hashlib
import personalize_seed_teacher as personal
import torch,numpy as np,soundfile as sf,torchaudio
from scipy.signal import resample_poly
from math import gcd
BASE=personal.BASE;OUT=Path('D:/总进度/目标人物分析/V1音色来源排查');OUT.mkdir(parents=True,exist_ok=True)
REVIEW=Path('D:/总进度/目标人物分析/音色与自然度复查')
read=personal.read;save=personal.save;sha=personal.sha
def main():
 assets,paths,get=personal.pinned_loaders();import inference
 ckpt=next(r for r in read(personal.OUT/'training_run.json')['checkpoints'] if r['step']==300)
 assert sha(ckpt['path'])==ckpt['sha256']
 config=personal.OUT/'personal_strong_config.yml'
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,
  auto_f0_adjust=False,semi_tone_shift=0,checkpoint=ckpt['path'],config=str(config),fp16=True)
 loaded=inference.load_models(SimpleNamespace(**kwargs));model,semantic,f0,vocoder,camp,mel,args=loaded
 assert args['fmax'] is None and args['sampling_rate']==22050
 inference.load_models=lambda _:loaded
 refs={};styles=[];ref_records=[];diagnostics=[]
 folder=OUT/'references';folder.mkdir(exist_ok=True)
 with torch.no_grad():
  for n in range(5,10):
   original=Path(f'D:/总进度/目标人物语音/Track {n}.wav');x,sr=sf.read(original,dtype='float32');x=x.mean(axis=1)
   seconds=15 if n==9 else 8;x=x[:int(sr*seconds)]
   x=resample_poly(x,22050//gcd(sr,22050),sr//gcd(sr,22050)).astype('float32')
   x*=.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
   target=folder/f'track{n}_{seconds}s.wav';sf.write(target,x,22050,subtype='PCM_24');refs[n]=target
   wave=torch.from_numpy(x).unsqueeze(0).to('cuda');m=mel(wave)
   y=vocoder(m).squeeze().cpu().numpy();assert np.isfinite(y).all()
   dest=OUT/f'诊断专用_目标原声仅声码器重建_track{n}.wav';sf.write(dest,y,22050,subtype='PCM_24')
   diagnostics.append(dict(label='vocoder_roundtrip_track'+str(n),group='vocoder_roundtrip_diagnostic',test_name='track'+str(n),
    path=str(dest),sha256=sha(dest),source_path=str(target),source_sha256=sha(target),
    role='Target waveform->mel->vocoder only; NOT any-to-one conversion or model acceptance',
    source_seconds=len(x)/22050,output_seconds=len(y)/22050,board_deployed=False))
   ref_records.append(dict(path=str(target),sha256=sha(target),original=str(original),original_sha256=sha(original),
    start_seconds=0,seconds=seconds,role='reference' if n<9 else 'diagnostic only; excluded from conditioning'))
   if n<9:
    w16=torchaudio.functional.resample(wave,22050,16000)
    fbank=torchaudio.compliance.kaldi.fbank(w16,num_mel_bins=80,dither=0,sample_frequency=16000)
    styles.append(camp((fbank-fbank.mean(dim=0,keepdim=True)).unsqueeze(0)).detach())
 mean=torch.stack(styles).mean(0)
 torch.save(dict(raw_mean=mean.cpu(),members=[v.cpu() for v in styles]),OUT/'fixed_target_mean_style.pt')
 save(OUT/'reference_manifest.json',dict(references=ref_records,mean_style_reference_tracks=[5,6,7,8],
  individual_norms=[float(v.norm()) for v in styles],raw_mean_norm=float(mean.norm()),
  track9_used_for_conditioning=False,learned_weights_overwritten=False,assets=assets,checkpoint=ckpt,
  mel_args=args,mel_matches_vocoder_config=True))
 save(OUT/'roundtrip_items.json',diagnostics)
 # Also retain input references for exactly matched evaluator preprocessing.
 save(OUT/'roundtrip_evaluator_items.json',diagnostics+[
  dict(label='vocoder_input_track'+str(n),group='vocoder_diagnostic_inputs',test_name='track'+str(n),path=str(p),sha256=sha(p))
  for n,p in refs.items()])
 sources=read(REVIEW/'neural_control_manifest.json')['files']
 sources += [r for r in read(BASE/'public_chinese_validation/validation_manifest.json')['files']
  if r['label'] in ['validation_source_BAC009S0004W0121','validation_source_fleurs_test_row3_id1852']]
 original_forward=camp.forward;records=[]
 conditions=[('reproduce_clip2',Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav'),False),
  ('prompt_track5',refs[5],False),('prompt_track8',refs[8],False),
  ('prompt_track6_mean_style',Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav'),True)]
 for condition,target,average in conditions:
  if average:camp.forward=lambda features,*a,**kw:mean.expand(features.shape[0],-1)
  else:camp.forward=original_forward
  folder=OUT/condition;folder.mkdir(exist_ok=True)
  for row in sources:
   name=row.get('voice',row['label'].removeprefix('validation_source_'))
   if condition=='reproduce_clip2' and name!='zm_010':continue
   assert sha(row['path'])==row['sha256']
   x,sr=sf.read(row['path'],dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
   x*=.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
   inp=OUT/'inputs';inp.mkdir(exist_ok=True);source=inp/(name+'.wav');sf.write(source,x,sr,subtype='PCM_24')
   torch.manual_seed(20261003);started=time.perf_counter()
   inference.main(SimpleNamespace(**kwargs,source=str(source),target=str(target),output=str(folder)))
   dest=folder/f'vc_{name}_{target.stem}_1.0_30_0.3.wav'
   record=dict(label=condition+'_'+name,group=condition,test_name=name,path=str(dest),sha256=sha(dest),
    source_path=row['path'],source_sha256=sha(row['path']),expected_text=row['expected_text'],text_origin=row['text_origin'],
    reference_path=str(target),reference_sha256=sha(target),fixed_target_mean_style=average,checkpoint=ckpt,
    diffusion_steps=30,cfg=.3,seed=20261003,offline_file_seconds=time.perf_counter()-started,
    source_speaker_enrollment=False,board_deployed=False,causal_streaming=False,audio_uploaded=False)
   if 'voice' in row:record['same_text_target']='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'
   records.append(record);save(OUT/'conditioning_items.json',records)
   if condition=='reproduce_clip2':
    old=next(r for r in read(REVIEW/'seed_neural_items.json') if r['label']=='seed_personal300_cfg03_zm_010')
    y,ysr=sf.read(dest,dtype='float32');z,zsr=sf.read(old['path'],dtype='float32')
    assert ysr==zsr and y.shape==z.shape
    error=float(np.max(np.abs(y-z)));save(OUT/'baseline_reproduction.json',dict(old_path=old['path'],old_sha256=old['sha256'],
     new_path=str(dest),new_sha256=sha(dest),sample_rate=ysr,max_absolute_error=error,byte_identical=sha(dest)==old['sha256']))
    if error>2/32768:raise RuntimeError('Baseline reproduction differs; do not attribute to conditioning')
 camp.forward=original_forward
 save(OUT/'run_status.json',dict(status='complete',conversions=len(records),roundtrip_diagnostics=len(diagnostics),
  subjective_acceptance=False,board_deployed=False))
 print('V1 CONDITION ISOLATION COMPLETE',flush=True)
if __name__=='__main__':main()
