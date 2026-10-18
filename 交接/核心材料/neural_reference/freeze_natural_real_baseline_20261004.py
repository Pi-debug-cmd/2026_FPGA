"""Preserve partial human naturalness gain; check content without tuning model."""
from pathlib import Path
import shutil
from opencc import OpenCC
from run_knn_controls import read,save,sha,BASE
OLD=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
OUT=Path('D:/总进度/目标人物分析/自然真实输入基线_2026-10-04');OUT.mkdir(exist_ok=True)
FEEDBACK='好像还可以，但是咬字没女声清晰，还挺自然的，但是会差一点点'
def main():
 provenance=read(OLD/'direct_audition_provenance.json');source=provenance['source'];converted=provenance['converted']
 for r in [source,converted]:assert sha(r['path'])==r['sha256']
 assert sha(converted['checkpoint']['path'])==converted['checkpoint']['sha256']
 snapshots=[]
 for role,p in [('real_source',source['path']),('partially_improved_conversion',converted['path']),('heard_audition',provenance['path'])]:
  p=Path(p);dest=OUT/p.name;shutil.copy2(p,dest);assert sha(p)==sha(dest)
  snapshots.append(dict(role=role,original=str(p),snapshot=str(dest),sha256=sha(dest)))
 note=dict(date='2026-10-04',human_feedback=FEEDBACK,hearing_result='partial_naturalness_improvement_not_final_acceptance',
  source=source,converted=converted,heard_scope='first6s conversion in18.4s audition; not full10.38s file acceptance',
  subjective_naturalness_progress=True,subjective_acceptance=False,articulation_shortfall_reported=True,
  articulation_cause_confirmed=False,target_likeness_finally_accepted=False,new_training_performed=False,
  source_speaker_enrollment=False,causal_streaming=False,board_deployed=False,board_latency_measured=False,
  audio_uploaded=False,snapshots=snapshots,old_synthetic_input_rejections_retained=True,
  source_text_differs_from_target_comparator=True,source_as_only_improvement_cause_proven=False)
 save(OUT/'baseline_manifest.json',note)
 for filename in ['architecture_choice.json','decision.json']:
  d=read(OLD/filename);d.update(status='human_partial_naturalness_improvement_clarity_pending',
   hearing_result=note['hearing_result'],human_feedback=FEEDBACK,human_feedback_date='2026-10-04',
   subjective_naturalness_progress=True,subjective_acceptance=False,candidate_promoted=False,
   preserved_comparison_baseline=str(OUT/'baseline_manifest.json'),next_step='Check articulation against actual source; keep fixed model and naturalness. Clarification of blurry consonants vs word errors vs muffling pending.')
  save(OLD/filename,d)
 summary=read(OLD/'real_input_summary.json');a=next(r for r in summary if r['label']=='actual_male_input_fleurs1906')
 b=next(r for r in summary if r['label']=='real_input_retained300_smoothed0.2_fleurs_male')
 cc=OpenCC('t2s')
 def canonical(text):return ''.join(ch for ch in cc.convert(text) if ch.isalnum()).lower()
 content=dict(source_reference_text=source['expected_text'],source_asr=a['asr_text'],conversion_asr=b['asr_text'],
  normalized_source_asr=canonical(a['asr_text']),normalized_conversion_asr=canonical(b['asr_text']),
  same_asr_sequence=canonical(a['asr_text'])==canonical(b['asr_text']),source_asr_cer=a['asr_cer'],conversion_asr_cer=b['asr_cer'],
  example_shared_asr_error='Supplied transcript 篇章 is decoded as 偏僵 on both source and converted recordings.',
  recognizer_output_not_ground_truth=True,no_confirmed_new_conversion_word_error=True,
  does_not_prove_perfect_articulation_or_actual_pronunciation=True,not_a_validated_clarity_measurement=True)
 save(OUT/'content_comparison.json',content)
 report=f'''# 真实输入下自然度有改善，保存基线并检查咬字

日期2026-10-04。用户反馈：“{FEEDBACK}”。这是第一次真实男声直接转换对照的部分积极听感：比较自然，但咬字及目标相似度仍有差距，不能写作全部验收完成。用户听的是输出前6秒，未确认全10.38秒、其他人、实时或板上运行。

人物模型仍是原V1个人300步、CFG0.3、CFM30步、FP16与原0.2/40ms局部包络校正，目标参考Track6前8秒，固定目标库仅Track5—8。真实男声FLEURS1906没有注册、训练或经文字识别再合成。模型未换，输入换成真实录音；由于文本/说话人也不同，不能证明仅合成输入就是唯一根因。全部原输入、完整输出和已试听18秒文件逐字节保存，SHA见baseline_manifest.json。旧合成输入及模型/强度分支的拒绝仍保留。

## 内容核对

真人源原稿：{source['expected_text']}

源录音ASR：{a['asr_text']}

转换录音ASR：{b['asr_text']}

统一简繁和标点后，两者识别序列相同：{content['same_asr_sequence']}。源和转换CER均{a['asr_cer']:.4f}，原稿“篇章”在两者均被识别成“偏僵”。这说明当前识别结果未显示额外内容变化，不能把这个共同识别错误自动归因于人物模型，更不能证明源录音本身读错、没有新增发音差异或转换咬字完全正确。此ASR只是评价器，不在转换主链中。

目标原声与此男声内容不同，用于比较音色；不同文本的发音难度、原男声自己的发音、转换模型和校正处理都可能影响清晰度，目前原因未确定。已询问用户：是字基本正确但声母/边界糊，还是读错/漏字/重复，或整体偏闷/鼻音。待说明前，不提高校正强度、反复追加训练或改变这份相对自然的基线。

## 后续验证

优先在固定人物模型下检查新的真实说话人及实际采集环境，源人不得注册或重训。用户实际男声文件可放D:/总进度/真实男声测试，只作输入验证；同文本有助于排除内容差异，不是最终系统必须读的固定台词。已有公开真人输入也可继续验证，无补录硬性前置条件。

完整教师仍需电脑整段/未来上下文，约310M总加载参数、额外检索模型开销未计入；不能声称已适合7020实时。后续必须单独做流式/模型压缩/PS与PL预算以及真实端到端延迟验收，保留原板卡音频链路的既有验证。本轮无新转换、训练、后台作业、SD或板卡改动。学习线不变。当前任务：定位咬字差距，保住当前真实输入下的自然度。
'''
 (OUT/'基线与咬字核对说明.md').write_text(report,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8');heading='## 最新听感：真实男声直接转换比较自然，咬字仍需核对（2026-10-04）'
 if heading not in s:
  t=heading+'\n\n用户反馈“'+FEEDBACK+'”。固定300+0.2在现有真人男声输入下有部分自然度改善，输出前6秒获“挺自然”评价，但咬字/相似度仍有差距，不能标记完整验收。原输入/完整输出/试听文件逐字节冻结在 D:\总进度\目标人物分析\自然真实输入基线_2026-10-04，模型/目标库SHA固定。未重新训练或注册源人；旧合成源的拒绝仍保持。不同文本/说话人会影响比较，不能仅凭此例确定合成源是唯一原因。\n\n原男声及转换ASR统一简繁后文字序列相同，均把原稿篇章识别成偏僵；这个识别结果不能证明实际发音或咬字正确，也不能直接归因于模型改字。已询问咬字差距是否是声母/边界糊、读错漏字或整体偏闷；等待澄清，暂不改动自然度基线。详情见该目录content_comparison.json和基线与咬字核对说明.md。无新训练/转换、后台任务、板卡/SD改动，仍无任意人实时/7020/延迟验收，学习线不变。本条覆盖前文待真人试听状态。\n\n'
  s=s.replace('## 最新选择：先验证真实讲话直接转换，',t+'## 最新选择：先验证真实讲话直接转换，',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');heading='## Latest: partial naturalness gain on actual male; clarity unresolved — 2026-10-04'
 if heading not in s:
  first,rest=s.split('\n',1);s=first+'\n\n'+heading+'\n\nUser says genuine male direct conversion quite natural/slightly short, articulation less clear than target. Preserve fixed300+0.2 source/output/audition sample-exactly under D:\\总进度\\目标人物分析\\自然真实输入基线_2026-10-04. First6s human scope only, not full clip/final identity/generalization/realtime acceptance. Source vs converted ASR normalized sequence same, both 篇章->偏僵; recognizer output cannot prove phonetic correctness or model fault. Asked blurry consonants vs word errors vs muffled/nasal, awaiting clarification. No new tuning/training or hardware action; source text differs, no sole-cause claim. Previous synthetic-output rejections retained. All jobs done.\n'+rest;p.write_text(s,encoding='utf-8')
 print('PARTIAL NATURAL BASELINE PRESERVED; CONTENT CHECK COMPLETE',flush=True)
if __name__=='__main__':main()
