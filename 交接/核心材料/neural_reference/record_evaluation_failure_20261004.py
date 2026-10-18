"""Human labels override metrics; stop the rejected tuning branch, prepare optional real input."""
from pathlib import Path
import json
from run_knn_controls import read,save,sha,BASE
COMBO=Path('D:/总进度/目标人物分析/模型与校正组合对照_2026-10-04')
OUT=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04');OUT.mkdir(exist_ok=True)
INPUT=Path('D:/总进度/真实男声测试');INPUT.mkdir(exist_ok=True)
FEEDBACK='没什么改善，还是很差，你比对不出跟原声的区别吗，如果我有实际的男声会不会更好一点，'
def main():
 d=read(COMBO/'decision.json');d.update(status='human_rejected_stop_model_strength_branch',hearing_result='rejected',
  human_feedback=FEEDBACK,human_feedback_date='2026-10-04',subjective_acceptance=False,candidate_promoted=False,
  next_step='Stop this training/strength branch. Audit metric/human disagreement; fixed retained model on actual male input without source enrollment.')
 save(COMBO/'decision.json',d)
 stages=[
  ('原人物V1',Path('D:/总进度/目标人物分析/音色与自然度复查/review_decision.json'),'negative conversion audition'),
  ('完整V2',Path('D:/总进度/目标人物分析/SeedVC完整V2对照/decision.json'),'negative conversion audition'),
  ('旧模型0.2校正',Path('D:/总进度/目标人物分析/局部音色包络校正/decision.json'),'partial timbre gain, still unnatural; not accepted'),
  ('旧模型0.3校正',Path('D:/总进度/目标人物分析/局部音色包络校正/2026-10-04_校正细化/decision.json'),'no gain, both corrected outputs unnatural/nasal'),
  ('追加训练不加校正',Path('D:/总进度/目标人物分析/声学生成改进_2026-10-04/decision.json'),'no gain/nasal on raw-model audition'),
  ('追加训练加0.2校正',COMBO/'decision.json','no gain/still poor on corrected-model audition')]
 ledger=[]
 for label,p,scope in stages:
  stage=read(p);selected=stage.get('selected');ledger.append(dict(label=label,decision_path=str(p),decision_sha256=sha(p),
   scope=scope,selected=selected,metrics=stage.get('selected_metrics'),
   feedback=stage.get('latest_human_feedback',stage.get('human_feedback',stage.get('human_v2_feedback'))),
   subjective_acceptance=False,labels_are_not_independent_speakers=True))
 save(OUT/'human_metric_disagreement_ledger.json',ledger)
 save(OUT/'evaluation_policy.json',dict(version='2026-10-04_after_repeated_human_rejections',
  human_feedback_overrides_scores=True,automatic_identity_or_mos_cannot_promote_candidate=True,
  no_validated_nasal_or_target_likeness_metric=True,
  scoring_can_screen=['nonfinite/silent/clipped output','ASR content changes','relative spectral/identity diagnostics'],
  scoring_cannot_confirm=['natural target timbre','absence of nasal artifact','human acceptance','arbitrary-speaker realtime or7020 feasibility'],
  stopped_branch=['increase envelope strength','repeat personal V1 training on same tiny target material as next default'],
  next_input_control='Existing genuine male recording, fixed retained300+0.2; optional user recording for matched-text/live input checks.',
  real_input_may_help_diagnosis_not_guaranteed_improvement=True,source_speaker_enrollment=False,
  new_recording_required_to_continue=False,no_more_weak_variant_auditions=True))
 instructions='''真实男声只用于测试，不是输入人物注册，不加入目标人物训练。

已有自然男声文件可以直接放在本目录，告诉AI文件名即可，不必重新录。
若新录：手机或现有麦克风均可，安静环境，正常讲话20—30秒，无背景音乐，不做后期变声/变速处理。WAV优先；若是其他格式告诉AI原格式，不要自己反复转换。
不必给每个未来使用者准备这段录音，最终要求仍为任意人直接讲话即可转换。

可选同文本（便于排除不同内容影响；不是必须）：
我的校园很美，走近大门就能看见宽阔的操场，红色跑道围着绿色草坪。教学楼前种着许多花草树木，教室里干净明亮，每天我们在这里听课写字。

这份同文本来自既有机器转写的目标片段，未人工逐字核对；不能当已经确认的精确原稿。任何自然中文内容仍可测试，源文本用于核查内容保持，不作为最终系统必须输入的文本。
'''
 (INPUT/'录音说明.txt').write_text(instructions,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 heading='## 最新：组合仍差，停止同路线调参，复核真实输入与评价（2026-10-04）'
 if heading not in s:
  t=heading+'\n\n用户反馈“'+FEEDBACK+'”。新1000+同0.2校正明确拒绝，停止这条追加训练/校正强度分支，不再按高声纹或MOS分数反复要求试听近似失败候选。旧300+0.2仅保存为相对有少许改善、仍不自然的比较基线，所有阶段均未通过变声验收。\n\n此前自动评价能比较声纹、频谱、内容，却未可靠捕捉用户鼻音/自然度/人物音色判断；已建立`'+str(OUT/'human_metric_disagreement_ledger.json')+'`与evaluation_policy.json，人的拒绝优先，不能用高分推翻。多数失败对照使用同一普通合成男声，不能把多个版本当多个独立用户样本。原生目标声重建“很好、接近”的反馈只适用于重建，仍不是转换成果。\n\n下一步固定保留模型，以已有真实男声作输入对照，检查合成源的影响。此前测试过公开真实男声，不能断言此前全是合成输入，也不能保证换真人就变好。用户可任选已有/新录20—30秒男声放`'+str(INPUT)+'`，只用于验证，不加入目标训练，不需每个新用户注册；这不是继续工作的硬性前置条件。板卡/SD不变，无需上电；学习线及任意人低延迟7020目标不变。此条覆盖上次待组合试听状态。\n\n'
  s=s.replace('## 最新：追加训练未改善，',t+'## 最新：追加训练未改善，',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');heading='## Latest: combination rejected; metric mismatch and real-input audit — 2026-10-04'
 if heading not in s:
  first,rest=s.split('\n',1);s=first+'\n\n'+heading+'\n\nHuman rejects1000+same0.2 as still poor/no gain. Stop same personal-training/envelope-strength branch. Old300+0.2 remains partially improved but unacceptable diagnostic, no candidate promoted. Human/metric ledger and evaluation_policy.json forbid score-only promotion or calling cosine percent likeness. Genuine male recordings were already in automated controls; now isolate input with fixed retained model. Optional user20-30s actual male file under D:\\总进度\\真实男声测试, diagnostic only, no source enrollment/training or prerequisite to progress. Existing real source used independently. Board/SD unchanged; no acceptance/realtime claim. Artifacts D:\\总进度\\目标人物分析\\真实输入与评价复核_2026-10-04.\n'+rest;p.write_text(s,encoding='utf-8')
 print('HUMAN FAILURE/POLICY SAVED',flush=True)
if __name__=='__main__':main()
