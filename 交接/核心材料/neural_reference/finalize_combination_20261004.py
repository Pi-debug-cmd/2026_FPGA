from pathlib import Path
from math import gcd
import json,shutil
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from finalize_post_rejection_phase import summaries
from run_knn_controls import read,save,sha,BASE
OUT=Path('D:/总进度/目标人物分析/模型与校正组合对照_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/局部音色包络校正');V2=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
def main():
 items=[r for r in read(OUT/'evaluation_items.json') if r['group']!='input_controls']
 groups,metrics=summaries(read(OUT/'combination_cross_eval.json'),read(OUT/'combination_content_eval.json'),items)
 assert len(groups)==4 and all(r['count']==4 for r in groups)
 integrity=[]
 for r in items:
  for key,hkey in [('path','sha256'),('source_path','source_sha256'),('prepared_source_path','prepared_source_sha256')]:assert sha(r[key])==r[hkey]
  x,sr=sf.read(r['path']);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6 and np.max(np.abs(x))<.999
  integrity.append(dict(label=r['label'],path=r['path'],sha256=r['sha256'],seconds=len(x)/sr,peak=float(np.max(np.abs(x))),clipped_fraction=0))
 assert all(r['max_sample_error']==0 for r in read(OUT/'baseline_reproductions.json'))
 save(OUT/'audio_integrity.json',integrity);save(OUT/'matched_2x2_summary.json',dict(groups=groups,files=metrics,
  no_nasality_measurement=True,diagnostic_not_human_acceptance=True))
 selected=next(r for r in read(OUT/'conversion_items.json') if r['test_name']=='zm_010')
 score=next(r for r in metrics if r['label']==selected['label'])
 oldscore=next(r for r in metrics if r['group']=='smoothed_envelope_0.2' and r['test_name']=='zm_010')
 assert score['asr_cer']<=oldscore['asr_cer']+.04,'Content regression: no audition'
 p1=OUT/'1_目标原声_6秒.wav';p2=OUT/'2_旧模型加0.2校正_6秒.wav';p3=OUT/'3_新模型加同样0.2校正_6秒.wav'
 shutil.copy2(V2/'1_目标人物原声_6秒.wav',p1);shutil.copy2(OLD/'3_音色校正实验_6秒.wav',p2)
 x,sr=sf.read(selected['path'],dtype='float32');x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000))[:144000]
 assert len(x)==144000;x*=min(.04/float(np.sqrt(np.mean(x*x))),.95/float(np.max(np.abs(x))))
 x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120);sf.write(p3,x,24000,subtype='PCM_16')
 clips=[];prov=[]
 for n,label,p in [(1,'目标原声',p1),(2,'旧300模型+原0.2校正',p2),(3,'新1000模型+同样0.2校正',p3)]:
  x,sr=sf.read(p,dtype='float32');assert sr==24000 and len(x)==144000;clips.append(x)
  prov.append(dict(order=n,label=label,path=str(p),sha256=sha(p),seconds=6))
 gap=np.zeros(4800,dtype='float32');audition=OUT/'18秒对照_目标原声_旧模型校正_新模型校正.wav'
 sf.write(audition,np.concatenate([clips[0],gap,clips[1],gap,clips[2]]),24000,subtype='PCM_16')
 x,sr=sf.read(audition);assert len(x)==441600 and sr==24000 and np.isfinite(x).all()
 save(OUT/'audition_provenance.json',dict(path=str(audition),sha256=sha(audition),seconds=18.4,clips=prov,selected=selected,
  clip2_identical_to_original_partial_improvement_preview=True,clip2_not_previous_raw_training_preview=True,
  both_conversions_use_same0_2_recipe=True,same_ordinary_source_and_text=True,target_original_used_as_source=False,
  new_model_residual_recomputed=True,manual_pitch_or_speed_change=False,not_word_aligned=True))
 save(OUT/'decision.json',dict(status='awaiting_single_missing_combination_audition',human_prior_feedback=read(OUT/'human_feedback.json')['feedback'],
  selected=selected,selected_metrics=score,prior_corrected_metrics=oldscore,groups=groups,
  hearing_result=None,subjective_acceptance=False,candidate_promoted=False,overall_improvement_demonstrated=False,
  missing_control_closed=True,new_corrected_conversions=4,raw_reproductions=4,new_training=False,
  audition=str(audition),raw1000_rejection_retained=True,prior0_2_partial_gain_retained_but_not_accepted=True,
  causal_streaming=False,board_deployed=False,board_latency_measured=False,audio_uploaded=False,active_jobs=0,
  purpose='Close the missing new-model+same0.2 cell, not claim quality improvement or further strength sweep.',
  next_if_no_gain='Stop this model/strength branch; retain failure and prior baseline. Revisit conversion method/data strategy rather than asking similar variants again.',
  limitations=['Nasal quality cannot be confirmed from cosine or predicted MOS/CER.',
   'Mean predicted naturalness declines against old0.2, no overall gain claimed.',
   'Track9 diagnostic only, not in training/pool; not pristine holdout.',
   'Full teacher and retrieval noncausal/offline; only EMA causal; no7020 acceptance.']))
 table='\n'.join(f"|{r['group']}|4|{r['mean_cosine']:.4f}|{r['mean_predicted_mos']:.3f}|{r['mean_cer']:.4f}|" for r in groups)
 report=f'''# 补齐同样0.2校正的新旧人物模型对照

日期2026-10-04。用户拒绝上一轮无校正的1000步模型：“{read(OUT/'human_feedback.json')['feedback']}”。该模型保持未通过，不能因为加回校正就自动改写验收。

## 之前有没有加校正

此前用户评价“好一些”的局部校正版使用旧300步模型＋0.2校正；随后0.2/0.3对照也都加了校正，0.3被反馈没进步，两版都有鼻音。上一轮为隔离训练作用，旧300与新1000两段都不加校正。原0.2较好的相对评价仍保留，但不自然的问题也保留。此前不能把单独训练失败理解为全部组合已失败。

现在补齐缺失条件：旧300不加、旧300加0.2、新1000不加、新1000加同样0.2，四输入共16文件。前三组12文件直接复用，唯一新生成4条1000+0.2，另做4条原1000逐采样复现，误差全部0。没有增加强度或新训练。相同固定目标Track5—8库、k4检索、DCT1—16残差、0.8幅度限制与40ms EMA，针对新模型重新计算残差，不能直接套用旧模型的帧残差。完整生成与SHA见generation_manifest.json和baseline_reproductions.json。

## 匹配2×2诊断

|模型/校正|输入数|中文声纹原始余弦均值|自然度预测均值|ASR CER均值|
|---|---:|---:|---:|---:|
{table}

均值不能证明鼻音改善；新组合的平均自然度预测仍低于旧0.2。普通男声某项自然度预测提高不能泛化为整体改进，声纹余弦不是相似百分比。ASR含识别器误差，没有校准鼻音评价指标。本轮不宣布更好，只用于补齐此前缺失的组合对照。

## 一次18秒对照

`{audition}`：①目标原声6秒 → ②旧300模型＋原0.2校正6秒 → ③新1000模型＋同样0.2校正6秒，间隔0.2秒。②直接复用用户曾评价“好一些”、后来确认有鼻音的原预览；不使用上一轮无校正的②。③来自同一普通男声和同一文本的真正转换，目标原声只作对照。③预览仅作相同RMS.04/峰值.95、24k重采样和5ms端点处理，无变速、手动变调或改写文本，各段6秒不逐词对齐。来源与哈希见audition_provenance.json。

## 当前状态

原权重、声音重建模块、原声音资料及SD保留，16文件的SHA、原输入/准备PCM、非静音、有限值和无削波检查完成。所有任务结束，无后台任务、音频上传、上电或补录要求。完整转换仍非因果，仅包络EMA因果，未达到任意人实时、7020或端到端延迟验收。学习线不变。当前只需判断③是否比②自然、是否减轻鼻音并更接近①；若无改善，结束这条训练与强度分支，不重复试听相似候选。
'''
 (OUT/'组合对照与校正说明.md').write_text(report,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8');phrase='电脑组合检查中，无需上电或补录。'
 assert phrase in s;s=s.replace(phrase,'电脑组合检查完成：新1000+0.2四条、原1000逐采样复现四条、匹配2×2诊断及完整性已保存，没有证明整体改善。当前仅一次18.4秒对照`'+str(audition)+'`：①原声、②旧300+0.2（复用之前“好一些”的预览）、③新1000+同样0.2，输入/文本相同。若仍不改善，停止这一训练与校正分支。全部作业结束，无需上电或补录；详见`'+str(OUT/'组合对照与校正说明.md')+'`。',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');phrase='PC combination screen in progress, no acceptance.'
 assert phrase in s;s=s.replace(phrase,'Completed4 new1000+0.2 conversions and4 sample-exact raw1000 reproductions; matched2x2 integrity/diagnostics frozen. No overall gain established. One18.4s original→old300+0.2→new1000+same0.2 audition awaits judgment; clip2 exactly reused original partially improved preview, not prior raw300. All jobs done, no acceptance. Artifacts D:\\总进度\\目标人物分析\\模型与校正组合对照_2026-10-04.',1);p.write_text(s,encoding='utf-8')
 print('FINALIZED',str(audition),flush=True)
if __name__=='__main__':main()
