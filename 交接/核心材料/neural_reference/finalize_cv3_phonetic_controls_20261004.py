from pathlib import Path
import json,hashlib
from run_rvc_pilot import settings
settings()
import soundfile as sf,numpy as np
P=Path('D:/总进度/目标人物分析/官方拼音发音控制对照_2026-10-04');Q=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[Q/'cv3_hanzi_asr_fleurs.wav',P/'fleurs_bie_hint.wav'];chunks=[];records=[]
for i,p in enumerate(paths):
 x,sr=sf.read(p,dtype='float32');assert sr==24000 and x.ndim==1
 gain=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8));x*=gain
 n=int(sr*.005);x[:n]*=np.linspace(0,1,n);x[-n:]*=np.linspace(1,0,n)
 if i:chunks.append(np.zeros(int(.4*sr),dtype='float32'))
 chunks.append(x);records.append(dict(order=i+1,source_path=str(p),source_sha256=sha(p),whole_audio_used=True,seconds=len(x)/sr,extra_rms_gain=gain))
out=P/'原③与别字拼音控制_约10秒对照.wav';sf.write(out,np.concatenate(chunks),24000,subtype='PCM_16')
d=dict(status='supported_phonetic_controls_complete_await_specific_human_comparison',cases_generated=3,original_clip2_kept_as_user_accepted_likeness_naturalness_baseline=True,human_clip3_not_fully_accepted=True,selected_audition='Old clip3 versus minimally changed bie-only control; not machine-chosen best.',all3_hint_duration_seconds=5.92,bie_only_duration_seconds=4.64,old_duration_seconds=4.68,all_hanzi_screening_edit_distances=0,known_blindspot_prevents_machine_phone_acceptance=True,other_male_zhe_zhuo_warning_persists=True,polyphone_context_handling_not_implemented=True,diagnostic_lexicon_not_general_solution=True,candidate_promoted=False,quality_accepted=False,board_deployed=False,source_speaker_enrollment=False,target_retraining=False,active_jobs=0,audition_path=str(out),audition_sha256=sha(out),audition_seconds=len(np.concatenate(chunks))/24000,audition_segments=records)
(P/'decision.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
(P/'对照说明.md').write_text('''# 官方拼音控制诊断与待确认听感

原②已被用户认可音色和自然度，保持原音频。原③仍有咬字问题，没有把ASR匹配改成通过。

本轮只测试官方明确支持的拼音特殊单位，参考音频、人物、随机种子和原来的真实输入识别文字保持一致，无源人注册、无新训练。

- FLEURS只指定别的[b][ié]：4.64秒。
- FLEURS指定这/是/别的[zh][è]/[sh][ì]/[b][ié]：5.92秒，节奏明显改变；不是自动优选。
- 另一真实男声的“别让我空着手回去”，只指定别：2.16秒；仍有zhe/zhuo诊断差异，未隐藏。

旧FLEURS4.68秒和新版本整句Hanzi/Pinyin识别均匹配。但检查器此前对人耳认为不对的别也识别bie2，无法据此判断改善。

约9.72秒完整句对照先原③，后只指定别的控制版，保持内容和近似音量，没有变速、换字或拼接替代字。这是最小干预对照，不声称最佳版本；是否更清楚、自然度有没有损失需要一次听感比较。三个字都控制的更慢版不加入本次试听。

当前是固定文本上的发音字典诊断。别等多音字需上下文判断，未实现通用字典，不能直接对所有用户讲话无条件替换。电脑生成与7020现场低延迟仍是独立未完成事项。无需开板、换卡或补录。
''',encoding='utf8')
header='## 最新待确认（2026-10-04）\n\n②已获用户音色和自然度认可并原样保留。完成3个官方拼音控制诊断：只提示别的版本4.64秒，与原③4.68秒接近；同时提示这/是/别版本5.92秒，不作为自动优选。识别器新旧都匹配，不能据此说咬字已修好。当前需听约9.72秒对照（先原③、后别字指定拼音版）确认是否更清楚及自然度损失。未推广候选、未部署板卡、所有作业完成。音频：`D:\\总进度\\目标人物分析\\官方拼音发音控制对照_2026-10-04\\原③与别字拼音控制_约10秒对照.wav`。缓存/流式测量已完成，见下一条；无需开板或补录。\n\n'
for file in [Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/PROJECT_STATUS.md')]:
 file.write_text(header+file.read_text(encoding='utf8'),encoding='utf8')
print(json.dumps(dict(path=str(out),seconds=d['audition_seconds'],sha256=d['audition_sha256']),ensure_ascii=True))
