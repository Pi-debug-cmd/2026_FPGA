from pathlib import Path
import copy
import json
import ast
import tempfile
from pronunciation_review_gate import digest, assess, annotate_report, REGISTRY

BASE=Path(__file__).resolve().parent
OUT=REGISTRY.parent
REAL=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
CLARITY=Path('D:/总进度/目标人物分析/真实输入轻度清晰度检查_2026-10-04')
DIAG=Path('D:/总进度/目标人物分析/真实声母错误定位_2026-10-04')
ABLATION=Path('D:/总进度/目标人物分析/别字后处理拆分对照_2026-10-04')
FEEDBACK='别字还是不对，你的比对结果是什么样的，判断出来是没问题的吗，我感觉你的审核比对模型出问题了'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
 OUT.mkdir(exist_ok=True)
 d=read(ABLATION/'decision.json');enhanced=read(CLARITY/'conversion_item.json')
 prior=read(DIAG/'decision.json')
 assert prior['affected_clip_numbers']==[4]
 fourth=prior['clips'][3]
 reviews=[]
 for path,scope,feedback in [
  (enhanced['path'],'User identified old diagnostic clip4 (first4s); corresponding complete parent waveform, no claim about unlistened remainder.',prior['latest_feedback']+'；定位回复：4'),
  (fourth['path'],'Exact first4s of current enhanced conversion',prior['latest_feedback']+'；定位回复：4'),
  (d['audio_path'],'Composite matched2x2 audition; latest feedback does not identify every individual failed condition.',FEEDBACK)]:
  reviews.append(dict(audio_path=path,audio_sha256=digest(path),result='failed',
   date='2026-10-04',reviewer='human user',feedback=feedback,listening_scope=scope,
   issue='别字不清楚/不对，未标注精确替代音素',error_reproduced_by_validated_phone_model=False))
 save(REGISTRY,dict(version=1,date='2026-10-04',reviews=reviews,
  prior_stage_examples=['shi perceived as xi','zhe perceived as jie'],
  examples_are_human_reports_not_gold_time_aligned_phone_labels=True,
  cannot_infer_all_four_conditions_failed=True))
 # Meaningful regression checks: very high scores/exact ASR cannot override a known failure.
 item=dict(path=enhanced['path'],sha256=enhanced['sha256'],
  target_centroid_cosine=.999,utmos_predicted=5.,asr_text='别',asr_character_error_rate=0.)
 assert assess(item,reviews)['status']=='failed_human_review'
 unknown=dict(item,path=d['clips'][1]['full_source_path'],sha256=d['clips'][1]['full_source_sha256'])
 assert assess(unknown,reviews)['status']=='not_assessed'
 assert not assess(unknown,reviews)['can_auto_approve']
 changed=dict(item,sha256='0'*64)
 try:assess(changed,reviews)
 except ValueError:pass
 else:raise AssertionError('Changed audio must not inherit a review')
 # Passed specific listener scope still cannot become automatic whole-system acceptance.
 passed=[dict(reviews[0],result='passed')]
 assert assess(item,passed)['status']=='passed_specific_human_review_only'
 assert not assess(item,passed)['can_auto_approve']
 for name in ['pronunciation_review_gate.py','automatic_voice_evaluation.py','cross_evaluate_voice.py']:
  ast.parse((BASE/name).read_text(encoding='utf-8'))
 save(OUT/'审核门控检查.json',dict(high_scores_and_zero_cer_cannot_override_human_failure=True,
  unreviewed_audio_remains_unassessed=True,changed_hash_cannot_inherit_review=True,
  specific_listener_pass_cannot_auto_approve_full_system=True,
  changed_scripts_syntax_valid=True,new_neural_phone_detector_validated=False))
 # Original numeric reports stay frozen. Annotate copies without rerunning or inventing scores.
 for original,new in [(CLARITY/'clarity_content_eval.json','内容评估_附发音状态.json'),
                      (CLARITY/'clarity_cross_eval.json','音色自然度评估_附发音状态.json')]:
  report=read(original);annotate_report(report)
  save(OUT/new,report)
  save(OUT/(new+'.来源.json'),dict(original_path=str(original),original_sha256=digest(original),
   scores_recomputed=False,original_not_modified=True,new_fields_only='pronunciation_review and pronunciation_audit'))
 current=read(ABLATION/'evaluation_items.json')
 report=dict(files=current,metrics_not_computed_in_this_ablation=True)
 annotate_report(report);save(OUT/'拆分对照_发音审核状态.json',report)
 d.update(status='human_reports_bie_still_wrong_pronunciation_not_approved',
  latest_feedback=FEEDBACK,hearing_result='别字仍不对；发音审核漏检受到质疑',
  subjective_acceptance=False,candidate_promoted=False,root_cause_confirmed=False,
  known_evaluator_blindspot='Word ASR/identity/MOS are not phone correctness; cannot verify b/ie or shi/xi/zhe/jie.',
  phonetic_approval=False,no_more_eq_or_strength_auditions=True,
  next_action='Validate independent Mandarin phone-sensitive assessment against known confusions before new enhancement auditions; keep retained baseline, not accepted.')
 save(ABLATION/'decision.json',d)
 policy=read(REAL/'evaluation_policy.json')
 policy.update(version='2026-10-04_after_human_phonetic_failure',
  automatic_phonetic_detector_validated=False,
  asr_word_match_does_not_validate_phones=True,
  human_phone_errors_block_acceptance=True,
  integrity_pass_is_not_pronunciation_pass=True,
  review_registry=str(REGISTRY),
  required_before_relying_on_new_phone_checker='Test known human-reported confusions and independently labelled positive/negative phone controls; forced alignment of prescribed phones alone is insufficient.',
  next_input_control='Paused small EQ/envelope listening loop; fix phonetic audit before another candidate audition.')
 for value in ['correct consonants/vowels/word boundaries','absence of audible phone substitution']:
  if value not in policy['scoring_cannot_confirm']:policy['scoring_cannot_confirm'].append(value)
 save(REAL/'evaluation_policy.json',policy)
 report='''# 发音审核漏检：实际结果与修正范围

2026-10-04。用户反馈“别字还是不对”，质疑自动审核。此前另有人耳报告shi听成xi、zhe听成jie。这些听感问题仍未解决，发音不通过；少量自然度/清晰度相对进步不代表整体音色或发音验收。

## 之前自动比对实际测了什么

真实男声原0.2包络校正版与轻度增强版：WeSpeaker Mandarin原始音色余弦0.9066417→0.9063183，UTMOS预测自然度4.0185355→4.0065584。数字几乎不变、没有提升，不能写为90.6%像目标或发音合格。ASR两个版本均把句首识别为“这并不是告别”，全文CER0.173913；全文源男声的CER也相同，主要“篇章→偏僵”识别误差。识别得到“别”不能证明b和ie实际正确。模型可能借语言上下文输出正确字，声母韵母错误不会必然出现在文本里。

最新2×2后处理拆分未重跑声学/识别模型，做的是SHA、有限值、采样数、时长、削波、响度匹配和旧增强逐字节复现。这些只能说明控制一致、波形可播放，不能说明别字正确。旧记录subjective_acceptance和candidate_promoted一直False，未曾整体批准，但流程持续以词级识别和全句评分筛选，未检出用户的音素问题。这是审核适用性与流程缺口；尚无证据证明评估权重文件损坏。

## 已完成的修正与局限

在两个自动报告生成器加入独立pronunciation_review字段：已绑定SHA的人耳失败显示failed_human_review；没有发音证据显示not_assessed；相同ASR、高音色或MOS不会令其自动通过。已核对四个关键情形：高分/零CER不能盖过人耳失败，未听音频保持未审核，SHA改变不能继承原审核，某次人耳通过不提升为全系统通过。现有数字报告未改，另存附发音状态副本；新的2×2无评分仍不伪造评分。

这只是修正状态和决策依据，不是新增了能自动听懂拼音的模型，也没有修好声音。尚未实现/验证逐音素比较、精确定位或可靠的发音评分器。原声与目标的音色本来不同，普通频谱距离也不能自动区分shi和xi。将来独立音素工具需先通过带已知错误的正反对照；把正确拼音强制对齐到音频本身也不能证明真的念对。

停止继续均衡/强度小变体试听，不再让用户为没有可靠发音证据的细调反复试听。下一步优先建立有已知正确/错误对照的独立中文音素检查，再处理有定位依据的内容保留问题；保留当前基线，不验收、不部署板卡。最新别字究竟涉及2×2的哪些个体条件仍未知，不能把全部四项自动判成坏或单独证明音色校正是根因。

本轮无新音频转换、训练、声音上传、板卡/SD更改，作业全部结束。7020核心、任意人无需注册与低延迟目标保持。
'''
 (OUT/'发音审核核对结果.md').write_text(report,encoding='utf-8')
 for p,heading,body in [
  (Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),
   '## 最新：别字仍错；自动审核未检出音素错误，修正发音状态（2026-10-04）',
   '用户质疑审核模型。核对：旧包络/增强版原始音色余弦约0.9066/0.9063、预测MOS4.019/4.007，无提升；ASR写出别、CER均0.1739，不能验证声母韵母。最新2×2只核对控制完整性，未重跑发音评分。审核存在适用性盲点，未证明权重损坏。两个评估报告生成器已加入按SHA绑定的独立发音审核状态；人耳错误失败、未测保持未审核、高分/ASR相同不得批准。回归检查四项通过，旧数字报告保留。尚无新自动音素模型，也没有修复声音。停止均衡/强度反复试听，先验证中文音素敏感检查，再修有依据的内容保留；未验收/未上板。详见 '+str(OUT/'发音审核核对结果.md')+'。全部作业结束，无新音频/训练/板卡或SD修改。'),
  (BASE.parent/'PROJECT_STATUS.md',
   '## Latest: bie still wrong; ASR/identity audit missed phone errors — 2026-10-04',
   'Human challenges audit. Prior0.2/enhanced Mandarin cosine.90664/.90632 and predictedMOS4.01854/4.00656 no improvement; ASR writes bie and CER.1739 both, not phone validation. Latest2x2 only control-integrity checked. Added pronunciation_review_gate to both evaluators: SHA-bound human failures block, unassessed stays unassessed, high scores/zeroCER cannot approve. Four meaningful gate checks and script syntax pass; annotated copies preserve original scores. Not a newly validated phone detector or speech repair; no evidence evaluator weights corrupt. Stop small EQ/envelope auditions; validate independent phone-sensitive checker with labelled positive/negative controls before new weak candidate auditions. Human pronunciation failure remains, root cause unproved. No new conversion/training/board/SD action; jobs done. Audit artifacts '+str(OUT)+'.')]:
  s=p.read_text(encoding='utf-8')
  if heading not in s:
   first,rest=s.split('\n',1);p.write_text(first+'\n\n'+heading+'\n\n'+body+'\n\n'+rest,encoding='utf-8')
 save(OUT/'run_status.json',dict(status='complete',validation_checks=4,phonetic_model_validated=False,
  phonetic_failure_resolved=False,subjective_acceptance=False,active_jobs=0,
  patched_scripts=[str(BASE/name) for name in ['pronunciation_review_gate.py','automatic_voice_evaluation.py','cross_evaluate_voice.py']]))
 print('AUDIT COMPLETE: pronunciation remains failed; no automatic phone detector validated.',flush=True)

if __name__=='__main__':main()
