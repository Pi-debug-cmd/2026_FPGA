"""Freeze controlled adaptation results; audition actual source-to-target only."""
from pathlib import Path
from math import gcd
import sys,json,shutil
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from finalize_post_rejection_phase import summaries
from personalize_seed_teacher import read,save,sha,BASE,PINNED
OUT=Path('D:/总进度/目标人物分析/声学生成改进_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/局部音色包络校正');V2=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
def main(group):
 items=[r for r in read(OUT/'evaluation_items.json') if r['group']!='input_controls']
 groups,metrics=summaries(read(OUT/'acoustic_cross_eval.json'),read(OUT/'acoustic_content_eval.json'),items)
 checks=[]
 for r in items:
  for key,hkey in [('path','sha256'),('source_path','source_sha256'),('prepared_source_path','prepared_source_sha256')]:assert sha(r[key])==r[hkey]
  x,sr=sf.read(r['path']);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6 and np.max(np.abs(x))<.999
  checks.append(dict(label=r['label'],path=r['path'],sha256=r['sha256'],seconds=len(x)/sr,peak=float(np.max(np.abs(x))),clipped_fraction=0))
 save(OUT/'audio_integrity.json',checks)
 train=read(OUT/'training_run.json');assert train['status']=='complete' and train['additional_steps']==700 and train['optimizer_scheduler_reset']
 for r in train['checkpoints']+[train['initial_checkpoint']]:assert sha(r['path'])==r['sha256']
 for r in read(OUT/'training_split.json')['train_segments']:assert sha(r['path'])==r['sha256']
 asset=next(r for r in read(PINNED/'strong_manifest.json') if r['repository']=='nvidia/bigvgan_v2_22khz_80band_256x')
 for r in asset['files']:assert sha(r['path'])==r['sha256']
 save(OUT/'matched_summary.json',dict(groups=groups,files=metrics,perceptual_nasality_not_measured=True))
 selected=next(r for r in read(OUT/'conversion_items.json') if r['group']==group and r['test_name']=='zm_010')
 selected_score=next(r for r in metrics if r['label']==selected['label'])
 old_score=next(r for r in metrics if r['group']=='raw_v1_fp16_steps30' and r['test_name']=='zm_010')
 assert selected_score['asr_cer']<=old_score['asr_cer']+.04,'Content regression too large; no audition'
 p1=OUT/'1_目标人物原声_6秒.wav';p2=OUT/'2_原人物模型无额外校正_6秒.wav'
 shutil.copy2(V2/'1_目标人物原声_6秒.wav',p1);shutil.copy2(V2/'2_上次未通过的转换_6秒.wav',p2)
 x,sr=sf.read(selected['path'],dtype='float32');x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000))[:144000]
 assert len(x)==144000;x*=min(.04/float(np.sqrt(np.mean(x*x))),.95/float(np.max(np.abs(x))))
 x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120)
 p3=OUT/'3_人物声学模型继续适配_真实转换_6秒.wav';sf.write(p3,x,24000,subtype='PCM_16')
 clips=[];prov=[]
 for n,label,p in [(1,'目标原声',p1),(2,'原个人300步模型、无额外校正的普通男声转换',p2),(3,'继续目标人物声学训练，普通男声输入的转换',p3)]:
  x,sr=sf.read(p,dtype='float32');assert sr==24000 and len(x)==144000;clips.append(x)
  prov.append(dict(order=n,label=label,path=str(p),sha256=sha(p),seconds=6))
 gap=np.zeros(4800,dtype='float32');audition=OUT/'18秒对照_目标原声_旧转换_新转换.wav'
 sf.write(audition,np.concatenate([clips[0],gap,clips[1],gap,clips[2]]),24000,subtype='PCM_16')
 x,sr=sf.read(audition);assert sr==24000 and len(x)==441600 and np.isfinite(x).all()
 save(OUT/'audition_provenance.json',dict(path=str(audition),sha256=sha(audition),seconds=18.4,clips=prov,
  selected=selected,target_reconstruction_is_not_conversion=True,new_clip_is_ordinary_source_to_target_conversion=True,
  target_original_used_as_conversion_source=False,same_ordinary_male_source_as_prior=True,same_source_text=True,
  first_two_previews_copied_exactly=True,baseline_and_candidate_both_no_envelope_correction=True,
  matched_raw_acoustic_models_only=True,manual_pitch_or_speed_change=False,comparison_not_word_aligned=True))
 decision=dict(status='awaiting_acoustic_adaptation_hypothesis_audition',component_feedback='这个好很多，已经很接近了',
  component_feedback_applies_to='Target-only native-mel reconstruction, not conversion success',selected=selected,
  selected_metrics=selected_score,group_summaries=groups,selection_purpose='One acoustic-adaptation hypothesis test, not claimed winner; automatic MOS/cosine do not confirm nasal repair.',
  hearing_result=None,subjective_acceptance=False,overall_improvement_demonstrated=False,arbitrary_live_speaker_acceptance=False,
  board_deployed=False,causal_streaming=False,board_latency_measured=False,audio_uploaded=False,active_jobs=0,new_conversions=8,
  vocoder_unchanged=True,envelope_strength_sweep_stopped=True,optimizer_scheduler_reset=True,additional_target_training_steps=700,
  audition=str(audition),next_if_unlike='Do not promote. Revisit acoustic representation/training strategy; target reconstruction remains diagnostic only.',
  limitations=['Two neural generic presets and two real recordings, not four identified distinct people.',
   'Automatic naturalness not calibrated for nasal percept, human judgments have contradicted scores.',
   'Track9 excluded from training/conditioning, repeatedly diagnostic; not pristine final holdout.',
   'Full teacher is noncausal offline PC pipeline; training gain not board feasibility.',
   'No source-speaker enrollment or source-validation training; vocoder untouched.'])
 save(OUT/'decision.json',decision)
 table='\n'.join(f"|{r['group']}|{r['count']}|{r['mean_cosine']:.4f}|{r['mean_predicted_mos']:.3f}|{r['mean_cer']:.4f}|" for r in groups)
 report=f'''# 保留声音重建模块，继续人物声学适配

日期2026-10-04。用户对目标原声仅经声码器重建反馈“这个好很多，已经很接近了”。此反馈只支持原生目标频谱重建较好，不能证明任意人转换成功，也不能完全排除生成频谱与声码器之间的匹配问题。用户对0.2/0.3转换的“不自然、有后鼻音、③没改进”仍有效。

## 本轮改变

BigVGAN声音重建模块保持原始冻结权重，停止局部包络校正。在已保存人物300步权重上，用同一Track5—8的99.14秒/25片段，再进行700步官方声学训练。AdamW及调度器重新初始化，因此是“权重初始化后追加训练”，不是完整优化器状态续训。保存累计600/1000两个节点；两套权重分别对原四输入进行无额外校正转换，共8条。参考Track6前8秒，CFM30步/CFG0.3/FP16/随机种子20261003固定。没有把目标原声当转换输入，没有补充源人注册录音或使用源验证数据训练。

官方Trainer.train_one_step损失保持不变；初始化时逐一核对全部可训练参数与300步模型一致，原权重/目标资料/声码器资产SHA保留。训练配置、逐步损失、资产、GPU用量、检查点SHA和优化器重置见training_run.json，损失降低不等于人耳验收。

## 匹配的四输入诊断

|组别|输入数|中文声纹原始余弦均值|自然度预测均值|ASR CER均值|
|---|---:|---:|---:|---:|
{table}

原始余弦不是相似百分比，自然度预测不能检测或确认用户描述的后鼻音，CER包含识别器错误；不能把某条或某组分数改善称作人物声音已通过。选取{group}的普通男声案例，只作为人物声学适配假设的一次听感检验，尚未认定优于旧版。

## 短对照来源

`{audition}`：①目标原声6秒，②原个人300步模型、无额外校正的转换6秒，③人物声学追加训练后、同样无额外校正的普通男声→目标人物转换6秒，间隔0.2秒。①/②直接复用完整V2对照阶段的旧预览；②不是最近0.2校正版，避免移除校正与训练变化混在一起。③确实来自同一普通男声、同一文本的模型转换，完全不同于上一轮只重建目标原声的诊断。③仅在预览做RMS.04/峰值上限.95、24k重采样和5ms端点处理，无变速或手动变调，各段6秒末尾不逐词对齐。全部来源/权重/源音频SHA见audition_provenance.json。

## 工程状态与待办

8条新转换、所有比较基线、输入/准备PCM及原训练资料哈希、有限值、非静音、削波检查完成，声音重建模块权重核对未变。所有作业结束，无后台任务、音频上传、SD或板卡改动。无需上电或补录。完整教师仍非因果、约310M总加载参数，没有7020部署、任意人实时或端到端延迟验收。学习线不变。

当前只需判断③是否减少此前的鼻音、讲话是否更自然，并是否更接近①。上一轮目标原声重建接近不能自动转移为③的验收。若③没有改进，保存失败结果，不推广或进入硬件部署。
'''
 (OUT/'人物声学适配与当前任务.md').write_text(report,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 phrase='电脑处理进行中，无需板卡上电，实时/7020目标仍未实现。'
 replacement='电脑本轮处理已完成：700追加训练、600/1000两个节点各4次真正转换，匹配诊断与完整性已保存。未确认鼻音消失，未推广候选。当前一次18.4秒试听`'+str(audition)+'`：①目标原声、②原300步模型无额外校正的转换、③'+group+'同样无额外校正的普通男声→目标人物转换，①②直接复用完整V2阶段旧预览，②不是最近0.2版；③并非目标原声重建。所有作业结束，无需板卡上电或补录，实时/7020目标仍未实现。详见`'+str(OUT/'人物声学适配与当前任务.md')+'`。'
 assert phrase in s;s=s.replace(phrase,replacement,1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');phrase='PC control in progress; supersedes pending reconstruction question.'
 assert phrase in s;s=s.replace(phrase,'Completed700 additional target-only official steps,600/1000 checkpoints and8 actual ordinary-source conversions; frozen matched diagnostics/integrity. Single18.4s target-original→raw personal300→raw '+group+' ordinary-source conversion pending; neither conversion has envelope correction, clip2 is earlier raw300, NOT recent0.2 or target reconstruction. All jobs done, no nasal repair or candidate acceptance claimed. Artifacts D:\\总进度\\目标人物分析\\声学生成改进_2026-10-04. Supersedes pending reconstruction question.',1);p.write_text(s,encoding='utf-8')
 print('FINALIZED',str(audition),flush=True)
if __name__=='__main__':main(sys.argv[1])
