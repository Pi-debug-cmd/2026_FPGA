"""Chosen next check: existing genuine male directly into fixed VC, no ASR/TTS."""
from pathlib import Path
import shutil
from math import gcd
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from run_knn_controls import read,save,sha,BASE
OUT=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
V2=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
REPLY='这两种最终目的都是我的目标，刚才应该是一直在做第一种吧，可以试试第二种，因为第一种怎么做都不自然，感觉第二种可能会改善一些'
def preview(source,dest):
 x,sr=sf.read(source,dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
 x=resample_poly(x,24000//gcd(sr,24000),sr//gcd(sr,24000))[:144000];assert len(x)==144000
 x*=min(.04/float(np.sqrt(np.mean(x*x))),.95/float(np.max(np.abs(x))))
 x[:120]*=np.linspace(0,1,120);x[-120:]*=np.linspace(1,0,120);sf.write(dest,x,24000,subtype='PCM_16')
def main():
 manifest=read(OUT/'real_input_manifest.json');source=manifest['source'];converted=manifest['corrected']
 assert sha(source['path'])==source['sha256'] and sha(converted['path'])==converted['sha256']
 assert manifest['raw_reproduction_max_sample_error']==0 and not manifest['source_registration']
 p1=OUT/'1_目标人物原声_6秒.wav';p2=OUT/'2_现有真实男声输入_6秒.wav';p3=OUT/'3_真实男声直接转换_6秒.wav'
 shutil.copy2(V2/'1_目标人物原声_6秒.wav',p1);preview(source['path'],p2);preview(converted['path'],p3)
 clips=[];provenance=[]
 for n,label,p in [(1,'目标人物原声，音色参照',p1),(2,'真实男声录音，FLEURS元数据male',p2),(3,'同真实男声直接转换，固定原300+0.2',p3)]:
  x,sr=sf.read(p,dtype='float32');assert sr==24000 and len(x)==144000 and np.isfinite(x).all();clips.append(x)
  provenance.append(dict(order=n,label=label,path=str(p),sha256=sha(p),seconds=6))
 gap=np.zeros(4800,dtype='float32');dest=OUT/'18秒直接转换_目标原声_真实男声_转换声.wav'
 sf.write(dest,np.concatenate([clips[0],gap,clips[1],gap,clips[2]]),24000,subtype='PCM_16')
 save(OUT/'direct_audition_provenance.json',dict(path=str(dest),sha256=sha(dest),seconds=18.4,clips=provenance,
  source=source,converted=converted,input_kind='genuine recorded waveform, not synthesized input',
  asr_or_ordinary_tts_in_conversion_chain=False,asr_used_only_for_independent_content_evaluation=True,
  target_original_used_as_source=False,target_clip_has_different_text=True,
  second_third_same_content=True,comparison_not_word_aligned=True,manual_pitch_or_speed_change=False,
  no_new_training_or_strength_changes=True,offline_pc_not_live_board=True))
 save(OUT/'architecture_choice.json',dict(date='2026-10-04',user_reply=REPLY,both_routes_can_serve_overall_goal=True,
  next_route='genuine speech directly to voice-conversion features/model and fixed target waveform',
  correction_of_prior_assumption='Previous teacher conversions were already direct VC with synthetic and real test sources; full ASR->ordinaryTTS->VC never implemented.',
  user_reply_does_not_accept_previous_outputs=True,source_speaker_enrollment=False,
  current_audition=str(dest),hearing_result=None,subjective_acceptance=False,
  causal_streaming=False,board_deployed=False,active_jobs=0))
 d=read(OUT/'decision.json');d.update(status='awaiting_genuine_input_direct_conversion_check',
  chosen_next_route='direct real speech, no ASR/TTS',audition=str(dest),hearing_result=None,subjective_acceptance=False,
  interpretation='Different input test, no claimed repaired model; direct VC was also previous architecture.')
 save(OUT/'decision.json',d)
 p=Path('D:/总进度/声音链路澄清_2026-10-04.md');s=p.read_text(encoding='utf-8')
 insert='''## 已收到的选择（优先于下文旧待确认状态）

用户答复：“'''+REPLY+'''”。两种路线都可以服务总目标，用户希望先验证第二种。必须同时纠正其“此前一直第一种”的理解：此前代码确实是第二种直接语音特征转换，多次试听以普通TTS为测试源，完整ASR→普通声→VC未实现，不能把输入类型与处理链路混为一谈。此事实已在聊天中说明。

已使用现有FLEURS中文真实男声直接输入固定保留300步模型＋0.2校正，之前已完成的文件不再重训或调强度；新准备18.4秒对照：①目标人物原声（不同文本，仅音色参照）、②真人输入、③同真人输入的直接转换。转换内无ASR或普通TTS，ASR只是独立内容核查。文件：`'''+str(dest)+'''`。尚未确认鼻音改善；此为电脑离线测试，不是板卡实时链路或验收成功。真实用户录音可继续用于测试，不建立源人物模型；核心在7020、低延迟、任意人无注册要求不变。全部任务结束，无后台工作。

'''
 s=s.replace('## 当前实际实现',insert+'## 当前实际实现',1);p.write_text(s,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 heading='## 最新选择：先验证真实讲话直接转换，纠正链路误解（2026-10-04）'
 insert=heading+'\n\n用户表示两种路线都能服务目标，希望先试第二种。必须纠正：此前电脑教师一直直接读取语音特征进行人物转换，多个试听以TTS普通声为测试源，完整识别文字→普通声合成→变声链没有搭建；不能称已完成第一种，也不能把第二种说成刚换的新模型路线。此事实已解释。当前只换成真实讲话输入，固定保留300+0.2方案，无新训练、无源人注册。已准备18.4秒`'+str(dest)+'`：①目标原声（不同内容，只作音色参照）、②FLEURS真人男声、③同真人男声直接转换；②③内容一致，未变速变调，仍待听感检查。自动分数不确认成功，旧失败反馈全部保留；此为电脑离线，不是板卡实时。详见 D:\总进度\声音链路澄清_2026-10-04.md 及同阶段architecture_choice.json。作业全部结束，无SD/板卡改动。本文以下待架构答复状态过时，其他路线仍可研究但不擅自替换总目标。\n\n'
 if heading not in s:s=s.replace('## 最新：先澄清普通文本录音的含义与最终链路',insert+'## 最新：先澄清普通文本录音的含义与最终链路',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');heading='## Latest choice: genuine-input direct VC; correct ASR/TTS misconception — 2026-10-04'
 if heading not in s:
  first,rest=s.split('\n',1);s=first+'\n\n'+heading+'\n\nUser says both routes suit overall goal, wants direct route next, mistakenly thought previous tests were fullASR->ordinaryTTS->VC. Corrected: teacher was always direct features->voice, several inputs synthesized; full first route never implemented. Prepared18.4s target-reference(different text)->genuine male input->same male direct fixed300+0.2 output; no new training or claimed improvement. ASR only independent evaluator, no source enrollment. Pending one genuine-input listening check, all jobs done; no board/realtime acceptance. Architecture clarification under D:\\总进度\\声音链路澄清_2026-10-04.md; original low-latency7020/any-speaker requirements unchanged.\n'+rest;p.write_text(s,encoding='utf-8')
 print('DIRECT REAL INPUT AUDITION READY',str(dest),flush=True)
if __name__=='__main__':main()
