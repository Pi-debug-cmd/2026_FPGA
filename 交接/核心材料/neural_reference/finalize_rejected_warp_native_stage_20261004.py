from pathlib import Path
import json,hashlib,shutil
from run_rvc_pilot import settings
settings()
import soundfile as sf,numpy as np
PROJECT=Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020')
OUT=Path('D:/总进度/目标人物分析/原台词_模型直接转换检查_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/固定原台词_分开试听_2026-10-04')
PILOT=PROJECT/'board_budget_20261004/phasefree_student_pilot'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

d=read(OUT/'decision.json');before=read(OUT/'before_inference.json');screen=read(OUT/'screening.json')
assert screen['native_pinyin_matches_ordinary_input'] and screen['native_hanzi_matches_ordinary_input']
assert abs(d['seconds']-d['source_seconds'])<.001
a=OUT/'A_目标人物原声.wav';b=OUT/'B_普通男声输入.wav';c=OUT/'C_新直接转换结果.wav'
shutil.copy2(OLD/'①目标人物原声.wav',a)
x,sr=sf.read(before['cropped_source'],dtype='float32')
gain=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8))
sf.write(b,x*gain,sr,subtype='PCM_24');shutil.copy2(d['path'],c)
clips=[]
for label,path in [('A_original_target',a),('B_generic_male_input',b),('C_native_conversion',c)]:
    x,sr=sf.read(path);assert x.ndim==1 and np.isfinite(x).all() and np.max(np.abs(x))<1
    clips.append(dict(label=label,path=str(path),sha256=sha(path),seconds=len(x)/sr))
assert clips[0]['sha256']==read(OLD/'decision.json')['clips'][0]['sha256'] and clips[2]['sha256']==d['sha256']
audition=dict(status='ready_for_one_same_text_separate_human_review',text=before['text'],clips=clips,
    source_gain_only=gain,separate_files_not_concatenated=True,prior_warped_clip3_rejected=True,
    previous_accepted_synthesis_unchanged=True,source_is_generic_synthetic_male_not_target=True,
    model_native_conversion_not_text_synthesis=True,full_source_audio_tokens_used=True,
    no_waveform_time_warp=True,no_mel_speed_interpolation=True,speed=1.,target_reference_sha256=before['target_reference_sha256'],
    target_track9_diagnostic_only=True,not_student_model=True,offline_teacher_only=True,
    not_causal_microphone_or_7020_demo=True,source_enrollment=False,
    human_acceptance=False,pronunciation_accepted=False)
save(OUT/'audition_manifest.json',audition)
d['status']='native_teacher_same_text_await_human_naturalness_and_identity';d['audition_manifest']=str(OUT/'audition_manifest.json')
save(OUT/'decision.json',d)
p=read(PILOT/'decision.json');s=read(PILOT/'heldout_screening.json')
p['status']='optimization_feasibility_only_not_quality_accepted';p['quality_screening_passed']=False
p['candidate_promoted']=False;p['issue']='38 heldout characters: baseline6 vs candidate5 edits, one8-character utterance worsens4->5; mean target cosine .1780->.1718. Not compelling improvement.'
p['no_human_audition_requested_for_weak_student']=True
save(PILOT/'decision.json',p)
evidence=PROJECT/'board_budget_20261004/stream_gemm_alignment_stage_evidence.json';e=read(evidence)
e['human_waveform_warp_rejection']=read(OLD/'human_feedback_rejected_timing.json')
e['supervision_alignment_pilot']['status']='waveform_warp_route_abandoned_after_human_rejection'
e['human_alignment_acceptance']=False;e['training_pairs_approved']=False
e['phasefree_optimization_pilot_checkpoint']=p['checkpoint_sha256'];e['phasefree_optimization_quality_accepted']=False
e['target_student_trained']=True;e['target_student_training_scope']='Only20 experimental steps on2 development utterances; not a production or accepted model.'
e['target_student_identity_approved']=False;e['next_required_user_action']='Listen separately to A actual target, B generic male input, C native CV3 conversion, unchanged same Chinese sentence. Assess C clarity, naturalness, identity; no old warped3 retry.'
e['current_audition_manifest']=str(OUT/'audition_manifest.json');e['current_audition_manifest_sha256']=sha(OUT/'audition_manifest.json');e['running_jobs']=0
save(evidence,e)
report='''# 拒绝节奏拉伸，改为模型直接转换参照

用户明确拒绝旧③：“不不不，三完全不行，变糊跟拖字还是比较明显的”。已按精确音频SHA写入人工失败登记；机器汉字/拼音一致不覆盖失败。旧②合成基准原样保留，旧③淘汰，不用于训练。公共两段未试听波形不伪称人工失败，但对应波形拉伸路线整体放弃。

审计官方CosyVoice3的speed开关：实现是对生成mel做linear interpolate后送HiFT，并非学到的时长控制。没有做新的speed扫参。尝试只对训练监督的频谱特征索引对齐、保留教师WAV，2名真人开发集20步LLVC试训有限/梯度正常，训练损失均下降；4名未登记保留说话人共38字，原模型6编辑、试训5编辑，但其中8字句4→5编辑，平均音色诊断.1780→.1718，没有可推荐的质量提升，不请求该学生试听、不上板。bulk/stream差异一段诊断NRMSE约.00036，不能把这个很小的差异当作质量失败根因。2句话/20步也不能据此断言整个架构不可行。

## 新的一次必要试听

仍使用原台词：“我的校园很美，走近大门就能看见宽阔的操场。”

- A_目标人物原声.wav：此前原声4.08004秒，逐字节复用，仅作留出诊断。
- B_普通男声输入.wav：固定普通Kokoro zm_010合成男声4.32秒，同一句；试听只匹配音量。不是目标人物声音，没有源人登记/训练。
- C_新直接转换结果.wav：同一普通男声经过原生CosyVoice3输入语音token→固定Track6前8秒目标条件→flow/HiFT，4.32秒。未把目标人物原声当转换输入，没有文字再合成、相位声码器拉伸、mel语速插值、手动升降调或EQ。

旧SAPI男声输入的自由拼音把“见”读成xian4（可能是源发音或检测误差，未做人耳定论），警告已保存；因此本测试改用早已固定的普通Kokoro录音，前19个自由拼音与原台词一致，没有重新改字或定制源人。新输入/输出自由Hanzi、拼音一致。Mandarin WeSpeaker相对诊断：原人物.8829、旧认可合成.8978、普通输入.1085、新转换.9026；这些数值不是百分比，不代替人耳验收。

这次C属于电脑离线教师直接转换，尚不是小模型/现场麦克风/7020输出。完整输入文件前端仍非因果，4.32秒离线耗时3.55秒不能当实际端到端延迟。需要用户确认C相比A是否接近目标声音、相对B是否清楚自然；若通过，再用这个保持输入时序的原生教师准备真实多说话人训练对。原TTS②基准仍保留。全部文件分别播放，没有拼接，也没有变更台词。

当前所有作业已结束，板卡/SD未改，不需上电或补录。工程与学习总目标不变。
'''
(OUT/'结果与独立试听说明.md').write_text(report,encoding='utf8')
header='''## 最新：旧③节奏拉伸被拒绝，新同台词直接转换待试听（2026-10-04）

用户：“不不不，三完全不行，变糊跟拖字还是比较明显的”。旧同文本节奏③精确SHA人工失败已登记，ASR/拼音一致不能覆盖。②认可的同文本TTS基准原样保留，波形时间拉伸路线淘汰，不再调强度/不做speed扫参，不把拉伸参照用于训练。官方CV3 speed只是生成mel线性插值，不是天然的时长控制。

完成阶段性LLVC目标试训：2名真人开发集、20步，只改变频谱损失对齐索引，天然教师WAV未改；梯度有限、训练损失下降。4名未训练说话人38字机器错误6→5、单句4→5、平均音色诊断.1780→.1718，学生没有合格改善，不请求试听、不部署、不以少量数据证明架构成败。bulk/stream差异一段NRMSE.00036，不能归为主因。此前“目标学生没训练”已过时，现在仅有未认可的极小试验检查点；FPGA算子通过并不代表该学生音质/实板通过。

改查无需时间拉伸的原生CV3转换教师：普通Kokoro zm_010同台词男声→固定Track6前8秒条件→flow/HiFT；输入/输出都是4.32秒，Hanzi/pinyin一致，目标音色诊断.9026（非人耳验收）。不是把目标原声塞进模型，也不是识别文字再TTS；源人未注册/训练。旧SAPI输入见/xian4警告保留，未当作人工发音金标准。这个教师仍电脑离线、输入非因果，未在7020或麦克风实时运行。

需要用户一次同文本独立试听：D:\\总进度\\目标人物分析\\原台词_模型直接转换检查_2026-10-04 中 A_目标人物原声.wav（旧原声逐字节复用4.08s）、B_普通男声输入.wav（4.32s）、C_新直接转换结果.wav（4.32s）。仍是“我的校园很美，走近大门就能看见宽阔的操场”。不拼接、不换台词，C不是旧失败③；需判断C的清晰度、自然度和目标相似度，尚无自动音质/咬字验收。若通过再用原生教师的时序准备多说话人监督，不能直接沿用旧波形拉伸对。

详见该目录结果与独立试听说明.md、audition_manifest.json、screening.json，以及工程board_budget_20261004/phasefree_student_pilot。所有作业结束、板卡/SD未变，不需要开板/新录音。官方2022.2/安装2018.3音频整合兼容与完整实时预算仍未解决。当前任务：审核保持输入时序的新原生转换教师。

'''
for path in [PROJECT/'PROJECT_STATUS.md',Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md')]:
    path.write_text(header+path.read_text(encoding='utf8'),encoding='utf8')
print('REJECTION AND PILOT OUTCOME RECORDED;3 separate same-text previews verified; no live jobs',flush=True)
