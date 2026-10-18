from pathlib import Path
import numpy as np,soundfile as sf
from run_knn_controls import read,save,sha,BASE
OUT=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
def main():
 items=read(OUT/'evaluation_items.json');cross={r['label']:r for r in read(OUT/'real_input_cross_eval.json')['files']}
 content={r['label']:r for r in read(OUT/'real_input_content_eval.json')['files']};summary=[];integrity=[]
 for r in items:
  assert sha(r['path'])==r['sha256'];x,sr=sf.read(r['path'])
  assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6 and np.max(np.abs(x))<.999
  c=cross[r['label']];a=content[r['label']]
  summary.append(dict(label=r['label'],path=r['path'],raw_cosine=c['wespeaker_raw_cosine_to_centroid'],predicted_mos=c['utmos_predicted'],
   asr_cer=a['asr_character_error_rate'],asr_text=a['asr_text'],raw_f0=a.get('raw_rmvpe_pitch'),subjective_acceptance=False))
  integrity.append(dict(path=r['path'],sha256=r['sha256'],seconds=len(x)/sr,finite=True,not_silent=True,clipped_fraction=0))
 manifest=read(OUT/'real_input_manifest.json');assert manifest['raw_reproduction_max_sample_error']==0
 save(OUT/'audio_integrity.json',integrity);save(OUT/'real_input_summary.json',summary)
 ledger=read(OUT/'human_metric_disagreement_ledger.json');roundtrip=read(Path('D:/总进度/目标人物分析/V1音色来源排查/diagnosis_decision.json'))
 recon=next(r for r in roundtrip['roundtrip_pairs'] if r['track']=='track9')
 save(OUT/'validity_findings.json',dict(human_negative_entries=len(ledger),not_independent_inputs_or_listeners=True,
  near_original_component=dict(human_feedback='这个好很多，已经很接近了',applies_to='target-only reconstruction',metrics=recon),
  contradictions='Repeated negative target-timbre/naturalness feedback despite high raw speaker similarity; native-target reconstruction accepted as close has lower predicted MOS than several rejected conversions.',
  not_a_calibration_dataset=True,no_perceptual_nasal_detector_claim=True,
  cannot_diagnose_source_as_only_cause=True,source_text_differs_between_real_and_synthetic_controls=True,
  real_input_higher_predicted_mos_not_human_gain=True,recording_optional=True))
 save(OUT/'decision.json',dict(status='real_input_checked_metric_policy_revised_no_candidate_promoted',
  last_combination_rejected=True,same_training_strength_branch_stopped=True,existing_real_male_control_complete=True,
  raw_baseline_reproduced_sample_exactly=True,new_corrected_conversions=1,existing_true_male_sources_previously_tested=True,
  real_input_improvement_confirmed=False,source_root_cause_confirmed=False,subjective_acceptance=False,
  candidate_promoted=False,automatic_ranking_may_not_override_human_feedback=True,
  user_input_folder='D:/总进度/真实男声测试',optional_user_recording=True,source_speaker_enrollment=False,
  source_validation_used_for_training=False,board_deployed=False,causal_streaming=False,
  audio_uploaded=False,active_jobs=0,next_step='If user supplies actual male file, fixed retained model/no source training; inspect content and timbre with matched text when available. Do not keep sweeping same failed models.'))
 table='\n'.join(f"|{r['label']}|{r['raw_cosine']:.4f}|{r['predicted_mos']:.3f}|{r['asr_cer']:.4f}|" for r in summary)
 report=f'''# 真实输入与评价复核

日期：2026-10-04。用户拒绝1000步+0.2校正，明确认为没有改善、仍很差，追问自动比较能力及真实男声是否更好。此拒绝已保存，停止同材料追加训练/强度调节，不再靠微小自动分数要求逐版试听。旧300+0.2仅是相对稍好、仍不自然的诊断基线。

## 自动评价的实际限制

目前能比较声纹向量、频谱、音高、内容识别和信号完整性，但无法可靠确认用户描述的鼻音、自然度和目标人物音色。多条人耳拒绝的转换仍有很高声纹指标；用户评价接近的目标原声重建，预测MOS低于数条失败转换。已建立6个阶段的反馈/指标追踪账本human_metric_disagreement_ledger.json、evaluation_policy.json及validity_findings.json。这些大多复用相同测试输入与同一用户，不是6名独立受试者，不能当充分校准数据。不得把声纹余弦当相似百分比，或用MOS推翻用户否定；没有建立鼻音检测器。

## 固定旧模型的真实男声检查

已有公开FLEURS中文真人男声10.38秒，使用原人物V1第300步/CFG0.3/CFM30步/相同参考；对无校正旧结果逐采样复现误差0，然后加原固定0.2校正，新增1条，未重新训练或调参数。源文件/权重/目标库SHA、有限值、非静音、削波、内容检查已完成。目标库仍只Track5—8，源语音未加入目标训练或人物注册。

|文件|中文声纹原始余弦|自然度预测|ASR CER|
|---|---:|---:|---:|
{table}

真实男声控制的自然度预测高于之前合成男声转换，但其人物相似、鼻音和自然度仍未获人耳确认，不能据此宣布更好。此真人文本与合成男声文本不同，时长/语速/说话人也不同，无法归因于“真人输入”这一因素。此前已有公开真人男声自动测试，并非此前全部输入都是合成声。这里不要求用户再次试听相近候选；保留实际测试文件与诊断以备核查。

## 可选用户录音

目录`D:/总进度/真实男声测试`已建好，录音说明.txt包含可选同文本。已有自然男声文件直接放入即可；新录可用手机/现有麦克风，20—30秒普通话、安静、无背景音乐、不后期变声或变速，WAV优先。其他格式保留原文件并告诉AI格式，不需反复转码。同文本更有利于把内容差异排除，但不是必须，不让项目退化为注册后才可转换。

用户录音只用于固定模型的输入测试，不参与目标人物训练、不建立源人模型；最终仍要求任何未注册者直接讲话可转换。这份录音不是继续工作的硬性条件，已有公开真人数据可继续使用。模型本身目前未通过，真实输入可能让排查更可靠，不能保证声音改善。

## 当前工程状态

本轮任务全部完成，无后台作业、音频上传、板卡/SD更新或上电要求。仍没有任意人实时、因果、7020部署或端到端延迟验收。学习线不变。当前等待的是可选的用户实际男声文件路径，用固定保留模型检查，不再开启同路线强度/训练矩阵。
'''
 (OUT/'真实输入检查与评价修正说明.md').write_text(report,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 phrase='下一步固定保留模型，以已有真实男声作输入对照，检查合成源的影响。'
 replacement='本轮已固定保留300+0.2方案，完成现有FLEURS中文真人男声10.38秒的新校正输出及原无校正逐采样复现（误差0）；信号完整性/内容/自动声纹和自然度已保存，但没有人耳改善确认。该真人与合成男声文本不同，不能认定输入是唯一根因，也不再要求用户听相近的调参版本。评价限制及真实输入记录见`'+str(OUT/'真实输入检查与评价修正说明.md')+'`。本轮全部任务结束，无后台作业。'
 assert phrase in s;s=s.replace(phrase,replacement,1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');phrase='Existing real source used independently.'
 assert phrase in s;s=s.replace(phrase,'Existing FLEURS actual male10.38s control complete: fixed300+0.2 one new output, old raw300 sample-exact reproduction, hashes/integrity/content and diagnostic scores frozen. Higher predictedMOS vs synthetic case does not prove human gain or causality; different text/duration. All jobs done, no new audition requested or candidate promoted. Report under real-input-audit artifacts.',1);p.write_text(s,encoding='utf-8')
 print('REAL INPUT AUDIT FINALIZED',flush=True)
if __name__=='__main__':main()
