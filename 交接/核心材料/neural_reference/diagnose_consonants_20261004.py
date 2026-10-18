"""Matched actual-input articulation control. No new conversion/model tuning."""
from pathlib import Path
from types import SimpleNamespace
from math import gcd
import numpy as np, soundfile as sf, torch
from scipy.signal import resample_poly, stft
import personalize_seed_teacher as personal

BASE=personal.BASE
OUT=Path('D:/总进度/目标人物分析/真实声母错误定位_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
CLARITY=Path('D:/总进度/目标人物分析/真实输入轻度清晰度检查_2026-10-04')
SNAPSHOT=Path('D:/总进度/目标人物分析/自然真实输入基线_2026-10-04')
read=personal.read;save=personal.save;sha=personal.sha
FEEDBACK='咬字还是不对，拼音拼不对，有些地方错的很明显，shi会念成xi，zhe会念成jie，但是相比于2，3有一点点进步'

def prepare_preview(source,dest):
 x,sr=sf.read(source,dtype='float32')
 if x.ndim==2: x=x.mean(axis=1)
 x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000)).astype('float32')[:96000]
 assert len(x)==96000
 x*=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8))
 x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120)
 sf.write(dest,x,24000,subtype='PCM_16')

def inspection(path):
 x,sr=sf.read(path,dtype='float32')
 if x.ndim==2: x=x.mean(axis=1)
 x=resample_poly(x,22050//gcd(sr,22050),sr//gcd(sr,22050)).astype('float32')
 assert np.isfinite(x).all() and np.max(np.abs(x))<.999
 frequencies,times,spectrum=stft(x,fs=22050,nperseg=512,noverlap=402,boundary=None,padded=False)
 power=np.abs(spectrum)**2
 # Preserve time-frequency evidence; frame bands are not phoneme labels.
 masks=[(frequencies>=a)&(frequencies<b) for a,b in [(300,1500),(1500,3000),(3000,5500),(5500,8000)]]
 bands=np.stack([power[m].sum(axis=0) for m in masks])
 np.savez_compressed(OUT/(Path(path).stem+'_spectral_diagnostic.npz'),times=times,band_power=bands,
  band_limits_hz=np.array([[300,1500],[1500,3000],[3000,5500],[5500,8000]]))
 return dict(path=str(path),sha256=sha(path),seconds=len(x)/22050,nonfinite_samples=0,
  peak=float(np.max(np.abs(x))),rms=float(np.sqrt(np.mean(x*x))),
  caveat='Different speaker spectral shapes are expected. No labeled-phone alignment or evidence proving shi/xi, zhe/jie substitution from these bands alone.')

def main():
 OUT.mkdir(exist_ok=True)
 previous=read(CLARITY/'decision.json')
 previous.update(status='small_relative_gain_but_clear_phone_errors_not_accepted',
  hearing_feedback=FEEDBACK,hearing_date='2026-10-04',human_relative_clarity_gain='slight',
  reported_consonant_errors=['shi perceived as xi','zhe perceived as jie'],
  subjective_acceptance=False,candidate_promoted=False,no_demonstrated_clarity_gain=False,
  clarification='Human reports slight relative gain, but marked errors remain; ASR agreement failed to detect them.')
 save(CLARITY/'decision.json',previous)
 m=read(SNAPSHOT/'baseline_manifest.json')
 m.update(latest_feedback=FEEDBACK,consonant_errors_reported=True,subjective_acceptance=False,
  nature_of_feedback='Prior naturalness progress remains partial; words/phonetic content not accepted.')
 save(SNAPSHOT/'baseline_manifest.json',m)
 for name in ['decision.json','architecture_choice.json']:
  m=read(OLD/name);m.update(latest_hearing_feedback=FEEDBACK,consonant_errors_reported=True,
   subjective_acceptance=False,candidate_promoted=False,latest_status='phonetic_content_not_accepted')
  save(OLD/name,m)
 save(OUT/'human_feedback.json',dict(date='2026-10-04',text=FEEDBACK,
  naturalness_progress_not_revoked=True,phone_content_not_accepted=True,
  root_cause_unknown=True,asr_equal_does_not_prove_phone_identity=True,
  stop_eq_sweeps=True,subjective_acceptance=False))
 manifest=read(OLD/'real_input_manifest.json')
 source=manifest['source']
 raw=next(r for r in read(OLD/'evaluation_items.json') if r.get('checkpoint') and 'amount' not in r)
 enhanced=read(CLARITY/'conversion_item.json')
 for r in [source,raw,enhanced]: assert sha(r['path'])==r['sha256']
 prepared=Path(enhanced['prepared_source_path'])
 assert sha(prepared)==enhanced['prepared_source_sha256']
 assets,paths,get=personal.pinned_loaders()
 import inference
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,
  auto_f0_adjust=False,semi_tone_shift=0,checkpoint=raw['checkpoint']['path'],
  config=str(personal.OUT/'personal_strong_config.yml'),fp16=True)
 assert sha(raw['checkpoint']['path'])==raw['checkpoint']['sha256']
 loaded=inference.load_models(SimpleNamespace(**kwargs))
 vocoder,mel=loaded[3],loaded[5]
 x,sr=sf.read(prepared,dtype='float32'); assert x.ndim==1
 x=resample_poly(x,22050//gcd(sr,22050),sr//gcd(sr,22050)).astype('float32')
 with torch.inference_mode():
  y=vocoder(mel(torch.from_numpy(x).unsqueeze(0).to('cuda'))).squeeze().cpu().numpy()
 assert np.isfinite(y).all()
 y*=min(.04/max(float(np.sqrt(np.mean(y*y))),1e-8),.95/max(float(np.max(np.abs(y))),1e-8))
 reconstructed=OUT/'诊断专用_真实男声仅声码器重建.wav'
 sf.write(reconstructed,y,22050,subtype='PCM_24')
 native=dict(label='actual_male_vocoder_only_diagnostic',path=str(reconstructed),sha256=sha(reconstructed),
  source_path=str(prepared),source_sha256=sha(prepared),expected_text=source['expected_text'],
  role='Same actual male input -> native mel -> vocoder. No semantic conversion, target voice, retrieval envelope or high-shelf. Not any-to-one evidence.',
  board_deployed=False,subjective_acceptance=False)
 rows=[dict(source,label='actual_male_source'),native,dict(raw,label='actual_male_raw_vc'),
  dict(enhanced,label='actual_male_current_enhanced')]
 save(OUT/'diagnostic_items.json',rows)
 evidence=[inspection(r['path']) for r in rows]
 clips=[];provenance=[]
 labels=['原始男声','原始男声只经声码器重建（不是人物转换）','人物转换，未加包络校正或清晰度增强','刚才增强后的转换']
 for i,(r,label) in enumerate(zip(rows,labels),1):
  dest=OUT/(str(i)+'_'+label+'_4秒.wav')
  prepare_preview(r['path'],dest)
  x,sr=sf.read(dest,dtype='float32');clips.append(x)
  provenance.append(dict(order=i,label=label,path=str(dest),sha256=sha(dest),seconds=4,
   full_source_path=r['path'],full_source_sha256=r['sha256'],start_seconds=0))
 gap=np.zeros(4800,dtype='float32')
 samples=[]
 for i,x in enumerate(clips):
  if i: samples.append(gap)
  samples.append(x)
 dest=OUT/'16秒声母定位_原男声_重建_未校正转换_当前转换.wav'
 sf.write(dest,np.concatenate(samples),24000,subtype='PCM_16')
 x,sr=sf.read(dest);assert sr==24000 and len(x)==398400 and np.isfinite(x).all()
 record=dict(date='2026-10-04',status='matched_articulation_diagnostic_ready',human_feedback=FEEDBACK,
  new_conversion_count=0,new_vocoder_only_diagnostics=1,new_training=False,source_enrollment=False,
  original_preserved=True,inspection=evidence,clips=provenance,
  audition_path=str(dest),audition_sha256=sha(dest),seconds=16.6,
  same_actual_source_all_clips=True,same_start_time_not_forced_phone_aligned=True,
  root_cause_confirmed=False,subjective_acceptance=False,board_deployed=False,
  causal_streaming=False,active_jobs=0,
  next_action='Listener identifies where shi/xi or zhe/jie first appears: original, vocoder reconstruction, raw conversion, or enhanced current conversion. Avoid score-only phonetic conclusions.')
 save(OUT/'decision.json',record)
 report='''# 真实声母错误定位

用户指出“shi会念成xi，zhe会念成jie”，轻度清晰度版③相比②只有一点进步。此前“字基本正确”的判断已被此更具体反馈补充：自然度部分进步仍保留，但发音内容未通过；两个转换版本均不是最终合格结果。停止进一步加重均衡、堆叠增强或盲目追加训练。

此前源与转换的ASR文字相同，也没显示这些声母差异。识别器能依靠上下文猜词，因此“识别文字不变”不能证明声母正确；人声相似度和预测MOS也不是发音正确性的证据。错误可能已在原输入存在，或来自特征/声学生成、声码器、局部包络校正；本轮不预判根因。

只新增一个同真实男声的原生mel→声码器重建诊断，不运行新人物转换、不训练。它用于分离波形重建与人物转换，保留男声，绝不是生成目标人物的成果。全部原文件SHA核对，试听使用同一输入的前4秒，RMS匹配，无变速变调。声码器重建与输出存在帧边界长度差异，不声称按音素精确对齐；频带轨迹仅保留声学检查依据，尚未给这些帧标注shi/xi或zhe/jie。

16.6秒顺序：①原男声；②原男声仅声码器重建；③未加包络校正或均衡的人物转换；④刚才轻度增强后的转换。只需判断发音错误首先在哪一段出现。①也错则更换/核查真实输入，②开始错则优先声码器/预处理，②对③错则优先人物转换特征与声学生成，③对④错则隔离包络校正后处理。听感是定位线索，不自动证明某一个内部模块是唯一根因。

作业已结束，无板卡、SD、音频上传或后台工作。完整教师仍电脑离线非因果，未部署7020。后续修复必须保留输入发音信息，源人无需注册，低延迟与7020核心要求不变。
'''
 (OUT/'声母定位说明.md').write_text(report,encoding='utf-8')
 p=CLARITY/'结果与下一步.md';s=p.read_text(encoding='utf-8')
 note='## 最新听感（覆盖下文待确认状态）\n\n'+FEEDBACK+'。只有轻微相对进步，发音仍明显错误，不验收、不作为最终默认方案。ASR相同未检出声母问题，停止均衡扫参；下一步见 '+str(OUT/'声母定位说明.md')+'。\n\n'
 if '## 最新听感' not in s:
  first,rest=s.split('\n',1);p.write_text(first+'\n\n'+note+rest,encoding='utf-8')
 for p,heading,body in [
  (Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),
   '## 最新：shi→xi、zhe→jie；仅轻微清晰度进步，发音未通过（2026-10-04）',
   '用户最新反馈：'+FEEDBACK+'。部分自然度进步保留，但发音内容不合格，停止均衡调参，不能用识别文字相同证明声母正确。只新增同真实男声的原生mel/声码器重建诊断，无新转换/重训。准备16.6秒原男声→同男声仅声码器重建→未校正人物转换→当前增强转换，同输入同前4秒、响度匹配；等待判断错误首先出现的段落，尚无根因证明。详见 '+str(OUT/'声母定位说明.md')+'。作业结束、无板卡/SD更改，仍电脑离线非因果，不验收7020实时或任意说话人。'),
  (BASE.parent/'PROJECT_STATUS.md',
   '## Latest: audible shi/xi and zhe/jie errors; isolate phone loss — 2026-10-04',
   'Human reports obvious consonant substitutions, only slight relative clarity gain. Partial naturalness feedback remains, phonetic content not accepted. ASR agreement failed to detect errors; stop EQ sweeps. One same-source native-mel/vocoder reconstruction added, no new VC/training/source enrollment. Prepared16.6s source -> native roundtrip (not target VC) -> raw VC without envelope/EQ -> current enhanced VC. Same actual input, first4s, RMS matched. Await localization; no root cause proved or model acceptance. All jobs done, board/SD unchanged, offline noncausal teacher. Artifacts '+str(OUT)+'.')]:
  s=p.read_text(encoding='utf-8')
  if heading not in s:
   first,rest=s.split('\n',1);p.write_text(first+'\n\n'+heading+'\n\n'+body+'\n\n'+rest,encoding='utf-8')
 print('CONSONANT DIAGNOSTIC COMPLETE '+str(dest),flush=True)

if __name__=='__main__':main()
