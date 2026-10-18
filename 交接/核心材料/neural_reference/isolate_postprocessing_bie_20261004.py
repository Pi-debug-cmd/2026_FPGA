"""Close the matched 2x2 envelope/EQ ablation, using existing conversions."""
from pathlib import Path
import shutil
import numpy as np
import soundfile as sf
from scipy.signal import lfilter
from run_knn_controls import read, save, sha, BASE
from gentle_clarity_20261004 import shelf
from diagnose_consonants_20261004 import prepare_preview

OLD=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
DIAG=Path('D:/总进度/目标人物分析/真实声母错误定位_2026-10-04')
CLARITY=Path('D:/总进度/目标人物分析/真实输入轻度清晰度检查_2026-10-04')
OUT=Path('D:/总进度/目标人物分析/别字后处理拆分对照_2026-10-04')

def apply_filter(source,dest):
 x,sr=sf.read(source); assert sr==22050 and x.ndim==1
 b,a=shelf(sr)
 assert np.max(np.abs(np.roots(a)))<1
 y=lfilter(b,a,x)
 scale=min(float(np.sqrt(np.mean(x*x))/np.sqrt(np.mean(y*y))),.95/float(np.max(np.abs(y))))
 y*=scale
 sf.write(dest,y,sr,subtype='PCM_24')
 reread,rs=sf.read(dest)
 assert rs==sr and len(x)==len(reread) and np.isfinite(reread).all()
 assert np.max(np.abs(reread))<.999 and abs(np.sqrt(np.mean(x*x))-np.sqrt(np.mean(reread*reread)))<1e-6
 return dict(b=b.tolist(),a=a.tolist(),rms_scale=scale)

def main():
 OUT.mkdir(exist_ok=True)
 d=read(DIAG/'decision.json')
 d.update(affected_clip_numbers=[4],clip_localization_reply='4',
  status='bie_issue_localized_to_current_processed_clip_pending_envelope_vs_eq',
  root_cause_confirmed=False,
  interpretation='User names clip4 for unclear bie. Clip3 lacks both envelope and EQ; clip4 has both. This local hearing clue does not prove all prior phone errors repaired or independently identify either operation.',
  next_action='Matched envelope-off/on x EQ-off/on control; preserve model and raw input.')
 save(DIAG/'decision.json',d)
 f=read(DIAG/'最新别字反馈.json');f.update(affected_clip_numbers=[4],reply='4',waiting_for=None,
  next_step='Separate envelope and EQ, no acoustic training or source enrollment.');save(DIAG/'最新别字反馈.json',f)
 raw=next(r for r in read(OLD/'evaluation_items.json') if r.get('checkpoint') and 'amount' not in r)
 env=read(OLD/'real_input_manifest.json')['corrected']
 both=read(CLARITY/'conversion_item.json')
 for row in [raw,env,both]: assert sha(row['path'])==row['sha256']
 # Identical filter recipe: prove reproduction on old corrected parent before raw control.
 reproduced=OUT/'核对专用_原增强版逐样本复现.wav'
 recipe=apply_filter(env['path'],reproduced)
 assert sha(reproduced)==both['sha256']
 new=OUT/'人物转换_保留清晰度增强_关闭音色包络校正.wav'
 raw_recipe=apply_filter(raw['path'],new)
 eq=dict(raw,label='raw_vc_only_clarity2dB',group='postprocess_ablation',path=str(new),sha256=sha(new),
  parent_conversion_path=raw['path'],parent_conversion_sha256=raw['sha256'],
  amount=0,high_shelf_gain_db=2,high_shelf_fc_hz=2400,
  model_changed=False,source_speaker_enrollment=False,subjective_acceptance=False,
  board_deployed=False,causal_streaming=False)
 rows=[dict(raw,label='raw_vc_env_off_eq_off',envelope_on=False,eq_on=False),
       dict(eq,envelope_on=False,eq_on=True),
       dict(env,label='raw_vc_env_on_eq_off',envelope_on=True,eq_on=False),
       dict(both,label='raw_vc_env_on_eq_on',envelope_on=True,eq_on=True)]
 checks=[]
 for r in rows:
  x,sr=sf.read(r['path']);assert sr==22050 and len(x)==228864 and np.isfinite(x).all()
  assert np.max(np.abs(x))<.999 and sha(r['source_path'])==r['source_sha256']
  assert r['source_sha256']==raw['source_sha256'] and r['checkpoint']==raw['checkpoint']
  checks.append(dict(label=r['label'],path=r['path'],sha256=r['sha256'],samples=len(x),sr=sr,
   rms=float(np.sqrt(np.mean(x*x))),peak=float(np.max(np.abs(x))),no_clipping=True))
 save(OUT/'evaluation_items.json',rows)
 save(OUT/'integrity.json',dict(checks=checks,old_both_eq_byte_exact_reproduction=True,
  reproduction_path=str(reproduced),reproduction_sha256=sha(reproduced),new_filter_recipe=raw_recipe,
  old_filter_recipe=recipe,no_new_model_inference=True,no_new_training=True))
 clips=[];provenance=[]
 names=['未经两项处理','只加清晰度增强','只加音色校正','两项都加_刚才第四段']
 for i,(r,name) in enumerate(zip(rows,names),1):
  p=OUT/(str(i)+'_'+name+'_4秒.wav')
  if i==1:shutil.copy2(DIAG/'3_人物转换，未加包络校正或清晰度增强_4秒.wav',p)
  elif i==4:shutil.copy2(DIAG/'4_刚才增强后的转换_4秒.wav',p)
  else:prepare_preview(r['path'],p)
  x,sr=sf.read(p,dtype='float32');assert sr==24000 and len(x)==96000
  clips.append(x);provenance.append(dict(order=i,label=name,path=str(p),sha256=sha(p),
   seconds=4,full_source_path=r['path'],full_source_sha256=r['sha256'],envelope_on=r['envelope_on'],eq_on=r['eq_on']))
 gap=np.zeros(4800,dtype='float32')
 parts=[]
 for i,x in enumerate(clips):
  if i:parts.append(gap)
  parts.append(x)
 dest=OUT/'16秒别字拆分_无处理_仅增强_仅校正_两项都加.wav'
 sf.write(dest,np.concatenate(parts),24000,subtype='PCM_16')
 x,sr=sf.read(dest);assert sr==24000 and len(x)==398400 and np.isfinite(x).all()
 decision=dict(date='2026-10-04',status='matched_postprocessing_ablation_ready',
  previous_feedback=d['latest_feedback'],previous_clip_localization_reply='4',
  diagnostic_scope='Unclear bie on previous clip4; not global phone/model acceptance.',
  audio_path=str(dest),audio_sha256=sha(dest),seconds=16.6,clips=provenance,
  new_audio_controls=1,new_model_conversions=0,new_training=False,
  original_waveforms_preserved=True,old_fourth_clip_byte_exact_reused=True,
  previous_third_now_first_byte_exact_reused=True,rms_matched_previews=True,
  input_and_model_identical=True,root_cause_confirmed=False,
  hearing_result=None,subjective_acceptance=False,candidate_promoted=False,
  no_objective_phone_accuracy_gain_claim=True,
  board_deployed=False,causal_streaming=False,active_jobs=0,
  next_action='Identify which of four matched clips has unclear bie, especially only-EQ2 versus only-envelope3. If only-envelope worsens and only-EQ remains clear, drop envelope provisionally and validate full speech/identity; do not call final any-speaker/board acceptance.')
 save(OUT/'decision.json',decision)
 report='''# “别”字：拆分音色校正与清晰度增强

2026-10-04。用户对上一轮四段（原男声、仅声码器重建、未校正人物转换、当前增强转换）反馈“整体感觉还好，别不清晰”，进一步明确是④。这是当前短段落的定位线索：③没有音色包络校正和高架增强，④同时有这两项；不能从此直接断言某一项是唯一根因、此前shi/zhe已全面修复，或模型已合格。

在固定相同人物模型、输入、参考和随机种子的既有转换上，完成匹配2×2。三项完整输出已存在，只新增“原转换只加2400Hz/+2dB清晰度增强”波形控制。不再执行人物转换或训练、不调强度、不拼贴指定字、不建立源人模型。原处理参数全部固定；在原音色校正父文件上相同滤波方法复现旧增强文件，SHA逐字节一致。全部原文件SHA、有限值、采样数、时长和削波检查通过，预览响度匹配。

新16.6秒顺序①未经两项处理的人物转换（上一轮③逐字节复用）；②只加清晰度增强，关闭音色包络校正；③只加音色包络校正，不增强；④两项都加（上一轮④逐字节复用）。都是同一输入的前4秒，台词相同。只有一个新对照，根因仍待听感确认；ASR相同不是发音正确性的证据。

若②清楚③不清楚，优先移除音色校正，再核查完整真实讲话的音色和自然度；若③清楚②不清楚，优先移除增强；若仅④差，检查两项组合效应；若①也差，不能仅处理后处理。听感线索支持下一步，不证明单一模块为所有错误根因。保留原基线，未提升任何版本为默认方案或最终验收。

作业全部结束，没有板卡、SD或上传操作。完整教师仍电脑离线非因果、未部署7020。后续必须验证其他真实说话人、流式与PS/PL预算，任意讲话者无需注册与低延迟要求保持。
'''
 (OUT/'拆分结果与下一步.md').write_text(report,encoding='utf-8')
 p=DIAG/'声母定位说明.md';s=p.read_text(encoding='utf-8')
 note='## 已定位到上一轮④\n\n用户答复“4”，指上一轮当前增强转换的“别”不清晰。③与④同时差两项操作，尚未分辨音色校正和清晰度增强。已关闭输入/声码器重复试听，完成一个匹配2×2后处理对照，见 '+str(OUT/'拆分结果与下一步.md')+'。旧等待编号状态过时，不推断全句或此前shi/zhe均已修复。\n\n'
 if '## 已定位到上一轮④' not in s:
  first,rest=s.split('\n',1);p.write_text(first+'\n\n'+note+rest,encoding='utf-8')
 for p,heading,body in [
  (Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),
   '## 最新：“别”问题在上一轮④，拆分两项后处理（2026-10-04）',
   '用户明确“4”。上一轮③未经校正、④含音色包络校正和清晰度增强，因此只定位到后处理分支，尚未确认单一根因或此前shi/zhe全面修复。固定输入/模型，在三个既有输出基础上只新增“原转换仅增强”一个波形对照；相同滤波逐字节复现旧增强文件，无新转换/重训/调强度。16.6秒新顺序：①两项都不加（旧③）②只增强③只音色校正④两项都加（旧④），前4秒相同台词、预览响度匹配。等待②③别字差异，未提升版本或验收。详见 '+str(OUT/'拆分结果与下一步.md')+'。作业结束，无板卡/SD更改；仍电脑离线非因果，7020低延迟任意说话人目标未变。'),
  (BASE.parent/'PROJECT_STATUS.md',
   '## Latest: bie blur localized to prior clip4; split envelope and EQ — 2026-10-04',
   'User replied4. Previous raw clip3 lacked envelope and EQ; previous clip4 had both, so single-operation root cause is unconfirmed. Completed matched2x2 with3 immutable prior outputs and1 new raw+same2dB shelf waveform. Same filter byte-exact reproduces old enhanced output; hashes/length/finite/no-clipping and RMS-matched previews verified. No new VC/training/strength sweep.16.6s new order raw/no ops(old3), EQ-only, envelope-only, both(old4). Await which bie is unclear; no final phone/identity acceptance or default promotion. All jobs done; board/SD unchanged; offline noncausal teacher. Artifacts '+str(OUT)+'.')]:
  s=p.read_text(encoding='utf-8')
  if heading not in s:
   first,rest=s.split('\n',1);p.write_text(first+'\n\n'+heading+'\n\n'+body+'\n\n'+rest,encoding='utf-8')
 print('POSTPROCESS ABLATION COMPLETE '+str(dest),flush=True)

if __name__=='__main__':main()
