from pathlib import Path
import shutil
import numpy as np
import soundfile as sf
from opencc import OpenCC
from run_knn_controls import read, save, sha, BASE
from prepare_direct_real_audition_20261004 import preview

OUT=Path('D:/总进度/目标人物分析/真实输入轻度清晰度检查_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
SNAPSHOT=Path('D:/总进度/目标人物分析/自然真实输入基线_2026-10-04')

def main():
 items=read(OUT/'evaluation_items.json')
 cross={r['label']:r for r in read(OUT/'clarity_cross_eval.json')['files']}
 content={r['label']:r for r in read(OUT/'clarity_content_eval.json')['files']}
 cc=OpenCC('t2s')
 checks=[]
 for r in items:
  assert sha(r['path'])==r['sha256']
  x,sr=sf.read(r['path'])
  assert sr==22050 and len(x)==228864 and np.isfinite(x).all()
  assert content[r['label']]['clipped_fraction']==0
  checks.append(dict(label=r['label'],sha256=r['sha256'],samples=len(x),sr=sr,
   rms=float(np.sqrt(np.mean(x*x))),peak=float(np.max(np.abs(x))),
   asr_text=content[r['label']]['asr_text'],cer=content[r['label']]['asr_character_error_rate'],
   mandarin_raw_cosine=cross[r['label']]['wespeaker_raw_cosine_to_centroid'],
   utmos_predicted=cross[r['label']]['utmos_predicted']))
 assert cc.convert(checks[0]['asr_text'])==cc.convert(checks[1]['asr_text'])
 assert abs(checks[0]['rms']-checks[1]['rms'])<1e-6
 p1=OUT/'1_目标人物原声_6秒.wav'
 p2=OUT/'2_刚才较自然的转换_6秒.wav'
 p3=OUT/'3_轻度清晰度增强_6秒.wav'
 shutil.copy2(OLD/'1_目标人物原声_6秒.wav',p1)
 shutil.copy2(OLD/'3_真实男声直接转换_6秒.wav',p2)
 preview(items[1]['path'],p3)
 assert sha(p2)==sha(OLD/'3_真实男声直接转换_6秒.wav')
 clips=[]; provenance=[]
 for i,(p,label) in enumerate([(p1,'目标原声（不同文本，仅音色参照）'),
                              (p2,'刚才相对自然的转换，原预览逐字节复用'),
                              (p3,'同一转换加轻度高频增强')],1):
  x,sr=sf.read(p,dtype='float32')
  assert sr==24000 and len(x)==144000 and np.isfinite(x).all()
  clips.append(x)
  provenance.append(dict(order=i,label=label,path=str(p),sha256=sha(p),seconds=6))
 dest=OUT/'18秒咬字对比_目标原声_自然基线_轻度增强.wav'
 gap=np.zeros(4800,dtype='float32')
 sf.write(dest,np.concatenate([clips[0],gap,clips[1],gap,clips[2]]),24000,subtype='PCM_16')
 y,sr=sf.read(dest); assert len(y)==441600 and sr==24000 and np.isfinite(y).all()
 record=dict(date='2026-10-04',status='one_control_ready_for_articulation_and_naturalness_check',
  human_feedback='字基本没错，但声母、字与字的边界有点糊',
  preserved_baseline=str(SNAPSHOT/'baseline_manifest.json'),checks=checks,
  asr_canonical_equal=True,source_and_both_outputs_share_asr_errors=True,
  asr_not_articulation_ground_truth=True,no_demonstrated_clarity_gain=True,
  no_demonstrated_likeness_or_naturalness_gain=True,subjective_acceptance=False,
  candidate_promoted=False,model_changed=False,new_controls=1,
  audio_path=str(dest),audio_sha256=sha(dest),clips=provenance,
  target_text_differs=True,second_third_same_source_and_content=True,
  second_clip_equals_previous_third_byte_for_byte=True,
  manual_pitch_or_speed_change=False,preview_rms_matching=True,
  causal_streaming=False,board_deployed=False,active_jobs=0,
  next_action='One short hearing check: clearer consonants/boundaries without harsher or less natural voice. If no benefit, retain baseline and stop EQ tuning.')
 save(OUT/'decision.json',record)
 report='''# 声母与字边界：单次轻度清晰度对照

2026-10-04。用户说明“字基本没错，但声母、字与字的边界有点糊”。上一轮真人男声直接转换被评价比较自然、仍有差距，保存为相对自然的基线，并非最终音色或全系统验收。

人物模型、参考、0.2包络校正与输入均未变；本轮仅在既有完整输出后增加一个2400Hz以上渐进+2dB的稳定高架滤波，响度匹配原音频。它只能帮助某些辅音更易听见，不能恢复模型丢失的发音、修复字边界或证明目标音色已正确。没有重训、变速、主动变调或新增源人注册。

核对：原文件SHA未变，采样数和时长一致，无非有限值或削波，完整文件RMS匹配。ASR统一简繁后相同，CER均0.1739；“篇章→偏僵”错误也出现在真实输入识别中，不能据此断言实际读错或清晰度已改善。Mandarin原始余弦约0.90664→0.90632，预测MOS约4.01854→4.00656：没有自动分数改善，变动很小，也不能代替用户对咬字、音色和自然度的判断。具体结果与滤波系数见本目录JSON。

18.4秒试听顺序：①目标原声6秒（不同文本，仅音色参照）；②刚才比较自然的转换6秒（逐字节复用上一轮③）；③同一转换轻度增强6秒。②③内容相同，预览响度匹配，只需判断③声母/字边界是否更清楚，且是否仍自然、无刺耳感。当前尚无新听感结果，不提升为默认方案；若无帮助，保留自然基线，不继续盲目堆叠均衡。

这仍是电脑离线文件验证，完整教师非因果、未上7020、没有实测板上端到端延迟。本轮无板卡/SD改动，作业全部结束。后续按真实说话人验证与流式小模型、PS/PL预算推进，任意输入者无需注册的要求保持。
'''
 (OUT/'结果与下一步.md').write_text(report,encoding='utf-8')
 p=SNAPSHOT/'基线与咬字核对说明.md'
 s=p.read_text(encoding='utf-8')
 note='## 最新说明\n\n用户已明确：字基本正确，声母和字边界糊。已完成一个轻度+2dB高架滤波对照，人物模型不变，未宣称改善、未替换本基线；新的待确认事项是这一个短试听。详见 '+str(OUT/'结果与下一步.md')+'。下文旧“等待说明”状态已过时，原反馈和原文件保留。\n\n'
 if '## 最新说明' not in s:
  first,rest=s.split('\n',1);p.write_text(first+'\n\n'+note+rest,encoding='utf-8')
 for p,heading,body in [
  (Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),
   '## 最新：字基本正确，声母与边界糊；单次轻度清晰度对照（2026-10-04）',
   '用户明确字基本没错、声母和字边界糊。真实男声固定300+0.2相对自然基线已完整保留，尚非目标音色或最终验收。只新增一个2400Hz/+2dB高架滤波，响度匹配，无模型/源注册/主动音调或语速变化。内容识别一致、有限/时长/削波/SHA检查通过；自动音色与自然度分数无提升，不能声称咬字已改善。仅准备18.4秒：①目标原声（文本不同）②上一轮较自然转换（原③逐字节复用）③同输出轻度增强。待一次听感确认③是否清楚且自然；无帮助保留基线并停止均衡调参。详见 '+str(OUT/'结果与下一步.md')+'。全部作业结束，无板卡或SD修改，教师仍电脑离线非因果、未上7020。以下等待清晰度分类的状态已过时，旧失败反馈仍有效。'),
  (BASE.parent/'PROJECT_STATUS.md',
   '## Latest: consonant/word-boundary blur; one gentle clarity control — 2026-10-04',
   'User confirms words mostly correct but consonants/boundaries blurry. Preserve natural real-input fixed300+0.2 baseline, not final acceptance. One waveform high-shelf2400Hz/+2dB control, RMS matched; no training/source registration/pitch or speed adjustment. Full audio SHA, duration, finite/clipping checks pass. Canonical ASR equal, CER .1739 both (same recognition errors as input); Mandarin cosine .90664→.90632 / predictedMOS4.01854→4.00656. No measured improvement or candidate promotion. One18.4s audition: target reference(different text), exact previous natural conversion preview, same waveform gently filtered. Await clarity/naturalness judgment; if no gain stop EQ tuning. All jobs finished, board/SD unchanged, offline noncausal teacher not on7020. Artifacts '+str(OUT)+'. Supersedes old pending clarification; old negative auditions stay valid.')]:
  s=p.read_text(encoding='utf-8')
  if heading not in s:
   first,rest=s.split('\n',1);p.write_text(first+'\n\n'+heading+'\n\n'+body+'\n\n'+rest,encoding='utf-8')
 print('COMPLETE: '+str(dest),flush=True)

if __name__=='__main__': main()
