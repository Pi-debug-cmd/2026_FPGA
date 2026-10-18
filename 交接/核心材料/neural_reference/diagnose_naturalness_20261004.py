"""Record nasal/unnatural human rejection; isolate numerical sampling controls.
No frequency 'nasality score', no accepted conversion and no source registration.
"""
from pathlib import Path
from types import SimpleNamespace
import json,hashlib,time
import numpy as np,soundfile as sf,torch
import personalize_seed_teacher as personal
BASE=personal.BASE;OLD=Path('D:/总进度/目标人物分析/局部音色包络校正')
REFINE=OLD/'2026-10-04_校正细化';OUT=Path('D:/总进度/目标人物分析/自然度与鼻音排查_2026-10-04');OUT.mkdir(exist_ok=True)
read=personal.read;save=personal.save;sha=personal.sha
FEEDBACK='不自然，2，3听起来都有后鼻音的感觉，不像正常自然的讲话，三感觉也差不多，没什么改进'
def record_feedback():
 d=read(REFINE/'decision.json');d.update(status='human_rejected_no_gain_both_unnatural',hearing_result='rejected',
  human_feedback=FEEDBACK,human_feedback_date='2026-10-04',subjective_acceptance=False,
  candidate_promoted=False,next_step='Stop envelope strength tuning; isolate raw acoustic generation and reconstruction.');save(REFINE/'decision.json',d)
 d=read(OLD/'decision.json');d['human_feedback_history']=[dict(feedback='好一些，但还是差一点',scope='0.2 compared with uncorrected V1',result='partial improvement'),
  dict(feedback=FEEDBACK,scope='0.2 and 0.3 compared with natural target',result='both unnatural, no 0.3 gain')]
 d.update(status='relative_gain_but_unnatural_not_accepted',latest_human_feedback=FEEDBACK,
  latest_human_feedback_date='2026-10-04',subjective_acceptance=False,
  preferred_comparison_baseline='Preserve 0.2 as relatively improved but unnatural diagnostic; not accepted teacher',
  next_step='Stop envelope strength tuning; inspect uncorrected synthesis, precision and target-only reconstruction.');save(OLD/'decision.json',d)
 save(OUT/'human_feedback.json',dict(date='2026-10-04',feedback=FEEDBACK,refinement_decision_path=str(REFINE/'decision.json'),
  subjective_acceptance=False,nasal_cause_confirmed=False,no_new_recording_required=True,board_work_required=False))
 heading='## 最新：两版均有不自然鼻音，停止强度微调（2026-10-04）'
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 if heading not in s:
  insert=heading+'\n\n用户最新反馈：“'+FEEDBACK+'”。加强至0.3没有进步，拒绝推广；0.2虽此前相对旧版有改善，但仍不自然、未验收。停止增加包络校正强度，两版均保留作诊断，不能把用户较好评价误写成成功。两版共享V1模型和后处理，仅凭听感不能确定鼻音出在生成模型、声码器或局部校正。先去除额外校正，固定同四输入/权重/参考，测试FP32/30与FP32/120步，结合目标原声仅声码器重建检查。不要把重建目标当任意人转换成果，也不要把自动自然度分数称作人耳确认去鼻音。板卡、SD、学习线不变，无须上电或补录。此条覆盖历史待0.3试听状态。\n\n'
  s=s.replace('## 最新反馈与细化：',insert+'## 最新反馈与细化：',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');heading='## Latest: both envelope outputs unnatural/nasal; 0.3 no gain — 2026-10-04'
 if heading not in s:
  first,rest=s.split('\n',1);s=first+'\n\n'+heading+'\n\nHuman feedback: '+FEEDBACK+'. 0.3 rejected; 0.2 relative gain remains historical but not natural/accepted. Stop envelope-strength sweeps. Nasal cause unconfirmed; isolate no-correction raw V1 FP32/30 and FP32/120, same four prepared sources/checkpoint/reference, alongside target-only reconstruction diagnostics. No source enrollment, recording/hardware action or board/realtime acceptance. Overrides historical pending0.3 audition.\n'+rest;p.write_text(s,encoding='utf-8')
def main():
 record_feedback();print('HUMAN REJECTION SAVED',flush=True)
 personal.pinned_loaders();import inference
 rows=read(OLD/'smoothed_items.json');ckpt=rows[0]['checkpoint'];assert sha(ckpt['path'])==ckpt['sha256']
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,
  auto_f0_adjust=False,semi_tone_shift=0,checkpoint=ckpt['path'],config=str(personal.OUT/'personal_strong_config.yml'),fp16=False)
 loaded=inference.load_models(SimpleNamespace(**kwargs));vocoder=loaded[3];capture={}
 def captured(m):capture['mel']=m.detach().cpu().numpy()[0].copy();return vocoder(m)
 wrapped=(*loaded[:3],captured,*loaded[4:]);inference.load_models=lambda _:wrapped
 records=[];spectral=[]
 for steps in [30,120]:
  group='raw_v1_fp32_steps'+str(steps);folder=OUT/group;folder.mkdir(exist_ok=True)
  for r in rows:
   assert sha(r['prepared_source_path'])==r['prepared_source_sha256'] and sha(r['source_path'])==r['source_sha256']
   source=Path(r['prepared_source_path']);ref=Path(r['reference_path']);torch.manual_seed(20261003);capture.clear()
   torch.cuda.synchronize();started=time.perf_counter()
   inference.main(SimpleNamespace(**dict(kwargs,diffusion_steps=steps),source=str(source),target=str(ref),output=str(folder)))
   torch.cuda.synchronize();elapsed=time.perf_counter()-started
   dest=folder/f'vc_{source.stem}_{ref.stem}_1.0_{steps}_0.3.wav';x,sr=sf.read(dest)
   assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6 and np.max(np.abs(x))<.999
   m=capture['mel'];np.savez_compressed(OUT/(group+'_'+r['test_name']+'_mel.npz'),generated_mel=m)
   original=np.load(OLD/(r['test_name']+'_mel_diagnostics.npz'))['baseline_mel'];assert original.shape==m.shape
   spectral.append(dict(label=group+'_'+r['test_name'],mel_rmse_to_raw_fp16_30=float(np.sqrt(np.mean((m-original)**2))),
    diagnostic_only=True,nasal_cause_not_confirmed=True))
   record=dict(r,label=group+'_'+r['test_name'],group=group,path=str(dest),sha256=sha(dest),amount=0.,
    cepstral_correction_applied=False,causal_envelope_ema_seconds=None,fp16=False,diffusion_steps=steps,cfg=.3,
    seed=20261003,seconds=len(x)/sr,offline_file_seconds=elapsed,reference_sha256=sha(ref),
    human_feedback=None,subjective_acceptance=False)
   records.append(record);save(OUT/'conversion_items.json',records)
   print('OUTPUT',record['label'],flush=True)
 save(OUT/'precision_sampling_diagnostics.json',spectral)
 save(OUT/'generation_manifest.json',dict(status='complete',script_sha256=sha(__file__),new_conversions=8,
  changed_factors=['CFM FP16 to FP32','Euler sampling 30 to 120 at FP32'],training_performed=False,
  no_envelope_correction=True,causal_streaming=False,board_deployed=False,audio_uploaded=False,nasal_cause_confirmed=False))
 print('PRECISION/SAMPLING CONTROLS COMPLETE',flush=True)
if __name__=='__main__':main()
