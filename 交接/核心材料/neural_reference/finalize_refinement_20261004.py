from pathlib import Path
from math import gcd
import json,hashlib,shutil
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from finalize_post_rejection_phase import summaries
BASE=Path(__file__).resolve().parent;OLD=Path('D:/总进度/目标人物分析/局部音色包络校正');OUT=OLD/'2026-10-04_校正细化'
V2=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 old=read(OLD/'smoothed_items.json');new=read(OUT/'conversion_items.json');items=old+new
 groups,metrics=summaries(read(OUT/'refinement_cross_eval.json'),read(OUT/'refinement_content_eval.json'),items)
 pairs=[]
 for name in [r['test_name'] for r in old]:
  a=next(r for r in metrics if r['test_name']==name and r['group']=='smoothed_envelope_0.2')
  b=next(r for r in metrics if r['test_name']==name and r['group']=='smoothed_envelope_0.3')
  pairs.append(dict(test_name=name,baseline=a,candidate=b,delta=dict(cosine=b['cosine']-a['cosine'],
   predicted_mos=b['predicted_mos']-a['predicted_mos'],asr_cer=b['asr_cer']-a['asr_cer'])))
 save(OUT/'matched_comparison.json',dict(groups=groups,pairs=pairs,metrics_are_not_human_acceptance=True))
 checks=[]
 for r in items:
  assert sha(r['path'])==r['sha256'] and sha(r['source_path'])==r['source_sha256']
  x,sr=sf.read(r['path']);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6 and np.max(np.abs(x))<.999
  checks.append(dict(label=r['label'],sha256=r['sha256'],seconds=len(x)/sr,rms=float(np.sqrt(np.mean(x*x))),peak=float(np.max(np.abs(x))),clipped_fraction=0,source_verified=True))
 save(OUT/'audio_integrity.json',checks)
 repro=read(OUT/'baseline_reproductions.json');assert all(r['max_sample_error']==0 for r in repro)
 selected=next(r for r in new if r['test_name']=='zm_010');pair=next(r for r in pairs if r['test_name']=='zm_010')
 assert pair['delta']['asr_cer']<=.02,'Male content regression: do not audition automatically'
 # Reuse the exact already-heard improved baseline preview as new clip2.
 p1=OUT/'1_目标原声_6秒.wav';p2=OUT/'2_刚才好一些的版本_6秒.wav'
 shutil.copy2(V2/'1_目标人物原声_6秒.wav',p1);shutil.copy2(OLD/'3_音色校正实验_6秒.wav',p2)
 x,sr=sf.read(selected['path'],dtype='float32');x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000))[:144000]
 assert len(x)==144000;x*=min(.04/float(np.sqrt(np.mean(x*x))),.95/float(np.max(np.abs(x))))
 x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120)
 p3=OUT/'3_适度加强校正_6秒.wav';sf.write(p3,x,24000,subtype='PCM_16')
 previews=[];provenance=[]
 for order,label,p in [(1,'目标人物原声',p1),(2,'刚才好一些的平滑0.2版本',p2),(3,'同模型适度加强为平滑0.3',p3)]:
  x,sr=sf.read(p,dtype='float32');assert sr==24000 and len(x)==144000;previews.append(x)
  provenance.append(dict(order=order,label=label,path=str(p),sha256=sha(p),seconds=6))
 gap=np.zeros(4800,dtype='float32');audition=OUT/'18秒对照_目标原声_刚才改善版_加强校正版.wav'
 sf.write(audition,np.concatenate([previews[0],gap,previews[1],gap,previews[2]]),24000,subtype='PCM_16')
 x,sr=sf.read(audition);assert len(x)==441600 and np.isfinite(x).all()
 save(OUT/'audition_provenance.json',dict(path=str(audition),sha256=sha(audition),seconds=18.4,clips=provenance,
  clip2_identical_to_previous_clip3=True,target_original_is_conversion_input=False,same_ordinary_male_input=True,
  same_personal_model=True,same_text=True,manual_pitch_or_speed_change=False,not_word_aligned=True))
 decision=dict(status='awaiting_single_refinement_comparison',human_previous_feedback='好一些，但还是差一点',
  previous_result='partial_improvement_not_accepted',selected=selected,selected_metrics=pair['candidate'],
  hearing_result=None,subjective_acceptance=False,overall_improvement_demonstrated=False,
  audition=str(audition),changes='Only envelope strength 0.2 to 0.3; fixed 40ms EMA, four sources, personal weights and target pool.',
  rejected_v2_kept_rejected=read(V2/'decision.json')['hearing_result']=='rejected',
  original_improved_baseline_preserved=True,baseline_reproductions_sample_exact=True,
  new_conversions=4,additional_baseline_reproductions=4,active_jobs=0,board_deployed=False,causal_streaming=False,
  arbitrary_live_speaker_acceptance=False,board_latency_measured=False,audio_uploaded=False,
  limits=['Only human partial improvement on previous male audition, not final acceptance.',
   'Predicted naturalness worsens for two inputs; no uniform overall improvement.',
   'Full WavLM/CFM context is noncausal even though EMA is causal.',
   'Track9 repeatedly diagnosed; not pristine final holdout, and excluded from training/target pool.',
   'No pitch-only conversion, target recording used as source or source speaker registration.'])
 save(OUT/'decision.json',decision)
 table='\n'.join(f"|{r['test_name']}|{r['baseline']['cosine']:.4f} → {r['candidate']['cosine']:.4f}|{r['baseline']['predicted_mos']:.3f} → {r['candidate']['predicted_mos']:.3f}|{r['baseline']['asr_cer']:.4f} → {r['candidate']['asr_cer']:.4f}|" for r in pairs)
 report=f'''# 局部校正细化：有改善，尚未验收

日期：2026-10-04。用户对上一版平滑0.2明确反馈“好一些，但还是差一点”。该版保存为局部改善的新比较基线，未达到最终目标音色；完整V2仍保持拒绝。此前待0.2试听的历史条目已过时。

## 本次实际改动

固定个人V1第300步/CFG0.3、原普通输入、原生成频谱、Track5—8固定目标单位库、DCT1—16残差、幅度上限0.8及40ms EMA，仅将校正强度0.2提高至0.3。利用已保存中间频谱生成4个新转换，额外复现4个0.2版本，四组逐采样误差均0且SHA一致。原声、基线、权重均未替换；没有重新训练、增加目标素材或输入说话人注册。

## 相同输入逐对诊断

|输入|中文声纹原始余弦|自然度预测|ASR字符错误率|
|---|---:|---:|---:|
{table}

原始余弦不是相似度百分比，自然度预测不是中文听众意见，ASR错误包含识别器错误。两种普通合成声与两段真实中文录音不能称四名已确认不同的真人。部分输入自然度预测下降，没有一致的整体进步证据。男声内容检查未显示明显新增识别错误，只将其用于一次强度辨别试听，不宣布新版本更好。

## 一次短对照

`{audition}`，共18.4秒：①目标原声6秒 → ②刚才被评价“好一些”的0.2版本6秒 → ③同输入、同人物模型、0.3版本6秒。注意本次②直接复用上次③的预览，已不是最早未校正的②。前两段文件直接复制，SHA固定；第三段仅做相同音量匹配、24k重采样、5ms端点淡入淡出，没有变调、变速或改写文本，各段6秒末尾不逐词对齐。目标原声只作对照，不作为转换输入。

## 当前工程状态

所有输出和原输入SHA、有限值、非静音、削波、时长核查完成，记录见audio_integrity.json、generation_manifest.json及baseline_reproductions.json。全部任务结束，无后台作业或音频上传，SD及板卡未修改，无须上电。完整模型使用整段/未来上下文，仅EMA本身因果；没有任意人实时转换、7020运行或真实端到端延迟验收。学习线不变。当前只需判断③是否比②更接近①，并留意自然度是否变差；若不进步，保留0.2而不强推0.3。
'''
 (OUT/'本轮细化与对照说明.md').write_text(report,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 oldline='电脑细化中，用户暂不需要上电、接线或补录。完成后保存评估与一次短对照；'
 newline='电脑细化已完成：4条0.3转换＋4条0.2逐采样复现，完整性与两套自动诊断已保存。未证明整体改进。一次18.4秒对照：①目标原声、②刚才有改善的0.2版本（复用上次③）、③加强至0.3，文件`'+str(audition)+'`。用户仅需试听，无须上电、接线或补录。全部作业结束；'
 assert oldline in s;s=s.replace(oldline,newline,1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');s=s.replace('PC refinement in progress; historical pending 0.2 audition is superseded.',
  'Completed four strength0.3 conversions and four sample-exact0.2 reproductions, frozen integrity and matched diagnostics. No overall improvement established. Single18.4s original→just-improved0.2→new0.3 audition awaits judgment; clip2 is previous clip3, copied exactly. All jobs finished. Artifacts: D:\\总进度\\目标人物分析\\局部音色包络校正\\2026-10-04_校正细化. Historical pending0.2 audition superseded.',1);p.write_text(s,encoding='utf-8')
 print('FINALIZED',str(audition),flush=True)
if __name__=='__main__':main()
