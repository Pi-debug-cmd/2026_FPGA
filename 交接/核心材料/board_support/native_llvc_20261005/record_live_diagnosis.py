from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent
p=r/'realtime_stage_evidence.json'
d=json.loads(p.read_text(encoding='utf-8'))
d['stage']='Experimental native small96 live chain; human reports quiet output and noise; NOT quality accepted'
d['human_live_feedback']={'initial':'声音很小，也有杂音','meter_trial_gain1':'有声音，但还是很小','speaker_baseline':'用户说明同样USB供电接线播放音乐音量正常','quality_accepted':False}
d['live_level_diagnosis']={
 'scalar_metrics_only':True,'user_microphone_waveform_saved':False,
 'candidate_binary':'native_llvc_small96_meter_arm',
 'candidate_sha256':hashlib.sha256((r/'native_llvc_small96_meter_arm').read_bytes()).hexdigest(),
 'default_gain_stream_parity':'meter_adapter_verification.json',
 'gain1_windows':'live_level_windows_gain1.jsonl',
 'gain1_max_one_second_input_rms':0.002997,
 'gain1_max_one_second_input_rms_window_peak':0.142883,
 'gain1_same_window_output_rms':0.008901,
 'gain1_same_window_output_peak':0.257058,
 'interpretation':'Low measured input/output levels; input does respond to speech. Noise origin not established; music with same speaker wiring was normal.',
 'adjusted_input_gain':4,'adjusted_output_gain':2,
 'playback_mixer_after':222,'playback_mixer_db_after':-16.5,
 'headphone_mixer':95,'headphone_mixer_db':-26,
 'adjusted_sample_window':{'input_rms':0.001316,'input_peak':0.007477,'raw_model_rms':0.011211,'raw_model_peak':0.130551,'output_rms':0.022421,'output_peak':0.261103,'output_clips':0},
 'adjusted_mean_compute_ms':11.462777,'adjusted_max_compute_ms':18.718884,
 'adjusted_missed_compute_deadlines':36,'adjusted_chunks':1386,
 'startup_underrun_report_ms':300.829,
 'human_adjusted_listening_pending':True,
 'no_noise_cure_claim':True,
 'current_pids':{'capture':24625,'convert':24626,'playback':24627},
 'start_command':'LLVC_INPUT_GAIN=4 LLVC_OUTPUT_GAIN=2 sh /home/root/native_llvc_trial_20261005/board_neural_meter.sh start; amixer sset Playback 222,222',
 'stop_command':'sh /home/root/native_llvc_trial_20261005/board_neural_meter.sh stop',
 'restart_defaults':'helper resets mixers to Playback210 and default gains1 unless specified',
 'next':'Human volume/noise feedback; if noise persists, compare declared original passthrough through same ALSA bridge to isolate interface vs neural artifacts. No automatic quality approval.'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
doc=Path(r'D:\总进度\7020实时小模型工程续接_2026-10-05.md')
with doc.open('a',encoding='utf-8') as f:
 f.write('''

## 现场首次人工反馈与电平诊断（2026-10-05续）

用户首次反馈“声音很小，也有杂音”，随后加检测程序后仍反馈“有声音，但还是很小”。这是明确的负面现场反馈，声音质量未验收；前文“用户试听尚待反馈”已被本节覆盖。用户另外说明同样USB接电脑供电、同样音箱接线播放音乐音量正常，因此不能把电脑USB供电当作已经查明的主因；优先排查实时电平、模型输出与格式桥。用户连接确认问题待答，不要要求盲目换线。

新增独立native_llvc_small96_meter.cpp/arm，由make_meter_build.py生成；支持LLVC_INPUT_GAIN（0.125至8）、LLVC_OUTPUT_GAIN（0.125至4），默认1。每77块约1秒记录原始输入、原始模型输出、放大后输出的RMS/峰值/削波计数，只保存标量，不保存麦克风波形。输出clips针对放大后输出；输入clips仍针对原始输入，不是放大后输入，因此不能将输入放大后的削波认定为已单独计数。原始完整模型与原stream程序保留。

verify_meter_adapter.py验证0、224、16000样本默认增益下PCM与原stream逐字节一致，224样本输入RMS独立算术核对；结果meter_adapter_verification.json。安装包722506字节，UART230400全SHA核验67a4efba58cb4c1f46f3b9ebef6d44418789fa99f5ccb88aef03ed066c44f6b4并恢复115200。

默认增益现场标量live_level_windows_gain1.jsonl：记录窗口中最大输入RMS0.002997、该窗口输入peak0.142883，输出RMS0.008901/peak0.257058；部分窗口输入约0.001而输出有较大瞬时峰。曾观测输入全零但模型输出RMS0.000393的窗口；此时用户是否保持安静没有严格标注，不能据此认定麦克风损坏或界定全部底噪原因。随后确认输入非零、随讲话变化。

当前临时实时配置：LLVC_INPUT_GAIN=4 LLVC_OUTPUT_GAIN=2 sh /home/root/native_llvc_trial_20261005/board_neural_meter.sh start；随后amixer sset Playback 222,222（-16.5dB，比原210/-22.5dB提高6dB），Headphone仍95/-26dB。这是电平校准，不能声称训练模型音色或发音已经改善。当前PID capture24625/convert24626/playback24627。一次调整后窗口inputRMS0.001316/peak0.007477，rawmodelRMS0.011211/peak0.130551，最终outputRMS0.022421/peak0.261103，窗口输出clips0；不是所有讲话已确认无削波。当前1386块平均11.462777ms、max18.718884ms、36块超13ms；启动播放日志报一次300.829ms underrun，需继续检查是否持续新增。温度raw2757约66.2℃。

调整后的主观音量与杂音反馈尚待用户；没有宣称解决杂音。若仍有杂音，应明确告知后，用同一neural ALSA格式桥做原声对照，区分接口噪声与模型伪影；不要偷偷把原声当转换成果。还应标注讲话/安静窗口，检查输入输出信噪变化；增益会放大噪声，不能作为音色矫正完成证明。

停止：sh /home/root/native_llvc_trial_20261005/board_neural_meter.sh stop。原board_neural_live.sh stop也管理同一个RUN。meter helper重启会重置Playback210且默认增益1，恢复调整配置要显式写入上述环境变量与mixer命令。原始直通恢复仍为/usr/local/bin/voice-live.sh start bypass，不是目标转换。额外sample_live_levels.py仅采标量600秒，PID保存在试验目录sample_live_levels.pid，不改变开机配置。
''')
print('Updated engineering handoff and evidence with negative listening feedback and current trial configuration.')
