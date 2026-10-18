from pathlib import Path
import json

OUT=Path('D:/总进度/目标人物分析/真实声母错误定位_2026-10-04')
FEEDBACK='现在感觉还好，别这个字还有点问题，感觉不清晰'

def main():
 p=OUT/'decision.json';m=json.loads(p.read_text(encoding='utf-8'))
 m.update(latest_feedback=FEEDBACK,latest_feedback_date='2026-10-04',
  latest_feedback_audition=m['audition_path'],
  unclear_word_reported='别',affected_clip_numbers=None,
  root_cause_confirmed=False,subjective_acceptance=False,
  status='partial_positive_hearing_with_bie_unclear_clip_localization_pending',
  previous_consonant_substitution_feedback_superseded=False,
  interpretation='User says overall feels okay and bie unclear, without identifying which clips. Do not infer all prior shi/zhe errors repaired or all four clips accepted.',
  next_action='Clarify which of clips1/2/3/4 has unclear bie before dependent repair; preserve existing waveform/model.')
 p.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'最新别字反馈.json').write_text(json.dumps(dict(date='2026-10-04',text=FEEDBACK,
  audition_path=m['audition_path'],affected_clip_numbers=None,
  prior_reported_errors=['shi perceived as xi','zhe perceived as jie'],
  prior_errors_confirmed_resolved=False,no_new_audio_or_model_changes=True,
  waiting_for='Which clips have unclear bie; original1, vocoder-only2, rawVC3, enhancedVC4'),ensure_ascii=False,indent=2),encoding='utf-8')
 p=OUT/'声母定位说明.md';s=p.read_text(encoding='utf-8')
 heading='## 最新反馈：整体感觉还好，“别”仍不清晰'
 note=heading+'\n\n用户反馈：“'+FEEDBACK+'”。未指定①②③④哪些段落不清晰，不能确认此前shi/zhe错误已经修复，也不能确认输入、声码器、转换或后处理为根因。已请求用户说明受影响编号；等待定位期间保存全部原文件和此前反馈，无新增调参、转换、训练或板卡更改。当前任务：定位“别”字的清晰度问题。\n\n'
 if heading not in s:
  first,rest=s.split('\n',1);p.write_text(first+'\n\n'+note+rest,encoding='utf-8')
 for p,heading,body in [
  (Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),
   '## 最新：整体感觉还好，“别”仍不清晰，待明确段落（2026-10-04）',
   '最新反馈：“'+FEEDBACK+'”。该评价指向16.6秒四段声母定位试听，但受影响编号未知，不能视为此前shi/zhe错误全部解决或整体音色/发音验收。已询问①原男声、②仅声码器重建、③未经校正人物转换、④当前增强转换中哪些“别”字不清晰，等待定位后再进行相关修复；保留所有原音频与失败反馈，无新增转换/训练/板卡或SD操作。当前任务：定位“别”字的清晰度问题。'),
  (Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/PROJECT_STATUS.md'),
   '## Latest: overall sounds okay, bie unclear; affected clips unknown — 2026-10-04',
   'Latest human feedback: overall feels okay, bie unclear. Affected clips1/2/3/4 unspecified; do not infer shi/zhe errors resolved or final acceptance. Asked clip localization on existing16.6s source/vocoder-only/rawVC/enhancedVC diagnostic. No new audio, tuning, training or board/SD operation. Preserve baseline and prior feedback; root cause unconfirmed. Next dependent action waits for clip identification.')]:
  s=p.read_text(encoding='utf-8')
  if heading not in s:
   first,rest=s.split('\n',1);p.write_text(first+'\n\n'+heading+'\n\n'+body+'\n\n'+rest,encoding='utf-8')
 print('Saved latest feedback; clip localization remains pending.')

if __name__=='__main__':main()
