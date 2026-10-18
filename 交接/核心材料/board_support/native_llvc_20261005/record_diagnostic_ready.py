from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent
p=r/'realtime_stage_evidence.json';d=json.loads(p.read_text(encoding='utf-8'))
d['human_live_feedback']['noise9200']='人声仍小，杂音仍明显：实机试听否定'
d['stage']='Noise9200 real listening failed; muted input/output diagnostic ring ready, waiting for spoken test and dump trigger'
d['live_actual_output_running']=False
d['current_noise_refined_student']['human_current_neural_feedback_pending']=False
d['current_noise_refined_student']['human_current_neural_feedback']='人声仍小，杂音仍明显'
d['current_noise_refined_student']['board_live_noise_quality_accepted']=False
d['current_noise_refined_student']['active']=False
d['active_diagnostic_ring']={
 'binary':'native_llvc_small96_diag_arm','sha256':hashlib.sha256((r/'native_llvc_small96_diag_arm').read_bytes()).hexdigest(),
 'geometry_and_model':'same E96/D48 step9200; new diagnostics binary, no inference algorithm change',
 'input_and_output_ram_keep_samples':319904,'seconds':319904/16000,
 'helper':'board_neural_diag.sh','headphone_mixer_muted':0,'capture_mixer':35,'playback_mixer':222,
 'pids':{'capture':25075,'convert':25076,'playback':25077},
 'trigger':'/run/voice-neural-live/diag_dump.flag',
 'prefix':'/home/root/native_llvc_trial_20261005/mic_diagnostic_20261005a',
 'host_ring_tests':'diagnostic_ring_verification.json',
 'files_dumped_yet':False,'recording_purpose':'User informed: one paired diagnostic after spoken test, not source enrollment nor pre-record delayed demo',
 'requested_speech':'3seconds quiet, same sentence twice, immediately reply说完了',
 'muted_snapshot_input_rms':.000031,'muted_snapshot_output_rms':.000026,
 'mean_compute_ms':11.212790,'max_compute_ms':18.070506,
 'feedback_hypothesis_not_confirmed':'Background input dropped after headphone mute; possible acoustic/analog output feedback, exact cause still unproven',
 'full_vs_stream_public_audit':json.loads((r/'full_vs_stream_audit.json').read_text()),
 'next_on_user_reply':'IMMEDIATELY create trigger while speech remains in20s ring; wait1-2s for manifest, stop stream, gzip archive .input.s16/.output.s16/.json, fetch verify toD, analyze levels/PSD/source and output ASR, compare host same model. Avoid another long task before dump.',
 'stop':'sh /home/root/native_llvc_trial_20261005/board_neural_diag.sh stop'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
q=r/'noise_refinement_stage_evidence.json';z=json.loads(q.read_text(encoding='utf-8'));z['human_current_neural_feedback_pending']=False;z['human_current_neural_feedback']='人声仍小，杂音仍明显';z['live_audition_stopped']=True;z['current_diagnostic_ring']=d['active_diagnostic_ring'];q.write_text(json.dumps(z,ensure_ascii=False,indent=2),encoding='utf-8')
with Path(r'D:\总进度\7020实时小模型工程续接_2026-10-05.md').open('a',encoding='utf-8') as f:
 f.write('''

## 9200步实机仍失败，最新为静音对照诊断待用户讲话

用户明确反馈新版“人声仍小，杂音仍明显”。因此电脑合成弱噪声降低18.6dB没有转化为当前实机验收通过，不能用这些测试替代用户听感。已保存板上noise9200_failed_live_status.json/playback.log并停止吵闹的9200试听，未宣称问题解决。

新增诊断native_llvc_small96_diag.cpp/arm（make_diagnostic_ring_build.py），在RAM保留最近208*1538=319904样本约19.994秒的原始S16输入和模型S16输出，不改变实时处理时序，只在触发flag后按样本编号配对写文件。20秒用于诊断缓存，不是额外播放延迟；文件写出可能造成瞬态等待，仅用于静音诊断。verify_diagnostic_ring.py确认0/224/16000样本PCM与原meter流一致，绕环超过20秒后两份文件与已处理源/输出逐字节对齐，flag触发才保存。测试仅公开FLEURS，没有用户波形。安装包725084字节全SHA11f368c2b9a3a0ddd7b9a8cb70184023c6950c5ab23cd7d30670b887daa880ce，串口230400传后恢复115200。

当前运行board_neural_diag.sh：capture25075/convert25076/playback25077，权重还是step9200。Capture35、Playback222，Headphone0（真正mute），仍在采集计算，音箱无声是主动诊断设置。LLVC_DIAG_TRIGGER=/run/voice-neural-live/diag_dump.flag，LLVC_DIAG_PREFIX=/home/root/native_llvc_trial_20261005/mic_diagnostic_20261005a。还没有触发或保存用户波形文件。已明确告知用户，会保留一段真实讲话的输入/输出作排查，不是每位使用者登记声音，也不是先录后播的最终方案；已请安静3秒读固定台词两遍，读完立即回复“说完了”，尚待。

极重要：收到“说完了”后先立即创建触发flag，避免20秒环形缓存覆盖这次讲话；不要先进行长训练/传输。触发后等1–2秒确认mic_diagnostic_20261005a.json及.input.s16/.output.s16存在、样本数配对，再停流、压缩到该板上试验目录、从串口取到D盘并SHA核验。可用既有serial_fetch_file.py（只允许试验DIR）；只串行操作COM8，exec返回session_id时必须先wait至结束，不能与下一次串口操作重叠。之后分析输入/输出波形电平、频谱、讲话/安静区间，输入与输出各自做不带期望台词约束的ASR，比较主机同模型推理与实际ARM输出。实际源波形只用于诊断，不能成为后续所有说话人的登记依赖。

静音后观测输入RMS0.000031/peak0.000031，模型输出RMS0.000026/peak0.000115；与此前开音箱时输入约0.001–0.003差别很大，提示可能音箱被麦克风拾取、声学回授，或模拟输出耦合。还未排除麦克风偏置/门限等变化，不能直接认定USB供电电流音或断言声学回授已证实。现场输入输出对照是下一步关键，避免继续盲目放大和只训练合成白噪声。

同时审查是否全段训练与小块推理不一致：audit_full_vs_stream.py，固定公开正常语音、同9200checkpoint，丢弃初始512ms后full RMS0.03774135、stream0.03774079、relative diff0.00051756、correlation0.999999866、maxabs0.00046861。结果full_vs_stream_audit.json。这个输入下差异很小，未发现足以解释严重现场杂音的分块错误；不是所有输入均已证明完全一致。旧ARM/Torch单独数值一致结果仍成立。

当前停止：sh /home/root/native_llvc_trial_20261005/board_neural_diag.sh stop。音箱现为静音，之后新helper要主动恢复相应Headphone值，不要把没有声音误认为接线故障。9200噪声、中文27/152与目标音色都未验收；原声对照曾“安静时无明显杂音，人声够大”，但不能替代模型验收。本节覆盖上文9200现场试听仍运行的状态。
''')
print('Recorded real-listening failure and muted diagnostic ready state; no diagnostic trigger issued yet.')
