from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent
p=r/'realtime_stage_evidence.json';d=json.loads(p.read_text(encoding='utf-8'))
d['human_live_feedback']['speaker_wiring_confirmed']='USB给音箱供电接电脑，3.5毫米音频接板子绿色接口'
d['human_live_feedback']['gain4_output2_playback222']='有杂音，很明显，还有电流音，我的声音相比之下很小'
d['human_live_feedback']['same_bridge_original_capture35']='还是比较小，相比于音乐播放声；用户尚未明确原声噪声情况'
d['live_level_diagnosis']['human_adjusted_listening_pending']=False
d['live_level_diagnosis']['adjustment_accepted']=False
d['live_level_diagnosis']['current_pids']=None
d['live_level_diagnosis']['active']=False
d['stage']='Noise isolation: neural conversion stopped after failed volume trial; original passthrough active, NOT conversion'
d['live_actual_output_running']=False
d['low_level_robustness']=json.loads((r/'low_level_robustness.json').read_text())
d['training_input_level_summary']={k:v for k,v in json.loads((r/'training_input_level_diagnosis.json').read_text()).items() if k!='rows'}
d['current_diagnostic']={
 'mode':'Original PCM passthrough through same neural ALSA capture/play bridge, NOT voice conversion',
 'actual_arm_public_pcm_sha256_parity':'f9889e70a671612d4da013d67b5cec6faab2e995db9e936f050e97d3a2dce464',
 'host_check':'bypass_verification.json',
 'binary':'pcm_bridge_bypass_arm','binary_sha256':hashlib.sha256((r/'pcm_bridge_bypass_arm').read_bytes()).hexdigest(),
 'helper':'board_bridge_bypass.sh','helper_sha256':hashlib.sha256((r/'board_bridge_bypass.sh').read_bytes()).hexdigest(),
 'pids':{'capture':24744,'passthrough':24745,'playback':24746},
 'capture_mixer':43,'capture_db':15,'baseline_capture_mixer':35,'baseline_capture_db':9,
 'playback_mixer':222,'playback_db':-16.5,'headphone_mixer':95,'headphone_db':-26,
 'microphone_input_boost':1,'microphone_boost_db':13,
 'digital_input_output_gain':1,
 'start':'sh /home/root/native_llvc_trial_20261005/board_bridge_bypass.sh start; amixer sset Capture 43,43 cap; amixer sset Playback 222,222',
 'stop':'sh /home/root/native_llvc_trial_20261005/board_bridge_bypass.sh stop',
 'boot_changed':False,'user_audio_saved':False,
 'pending':'5seconds quiet then same sentence twice; distinguish silent hiss and speech volume',
 'target_quality_accepted':False}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
with Path(r'D:\总进度\7020实时小模型工程续接_2026-10-05.md').open('a',encoding='utf-8') as f:
 f.write('''

## 明显杂音反馈后撤回增益，正在原声隔离测试（最新状态）

用户确认USB插电脑给音箱供电、3.5毫米音频插板子绿色接口；同接线音乐正常。此前数字input4/output2+Playback222的调整被用户否定：“有杂音，很明显，还有电流音，我的声音相比之下很小”。已恢复Playback210并停止神经转换，保留gain4_failed_status.json、gain4_failed_playback.log于板上。最后该模型16324块平均11.413396ms/max19.224295ms/169块超13ms；播放日志仍只有启动300.829ms，没有发现持续新增underrun。因此不能把听感杂音直接解释成持续播放欠载，也不能认定USB电脑供电是主因。

新增pcm_bridge_bypass.cpp/arm与board_bridge_bypass.sh，同一个neural_capture/neural_play ALSA格式桥及相同208样本/832缓冲/39ms启动配置，但转换段逐字节传递S16单声道16000Hz，不经过模型，无数字增益，不存用户波形。明确告知用户这是原声诊断，不是变声。Host0/1/207/208/224/16000样本逐字节匹配且208样本输入在EOF前输出；实际ARM用公开fleurs_full.s16验证完整输入输出SHA均f9889e70a671612d4da013d67b5cec6faab2e995db9e936f050e97d3a2dce464。第一次tar脚本CRLF启动错误已通过LF小文件重新上传修复，最终helper SHA1f8729208aefd33cb22596e61e773ea99836af0225a9764ba74e0ba35ce10709；没有把失败启动当成功。

原声初始Capture35/+9dB、Playback210/-22.5dB、Headphone95/-26dB时，用户仅反馈“还是比较小，相比于音乐播放声”，尚未明确原声噪声情况。窗口输入RMS0.002481/peak0.008240，输出与输入相同，无clip；日志没有underrun。不能就此宣称原声无噪声。

目前仍运行原声直通：capture24744、passthrough24745、playback24746。当前临时Capture43/+15dB（比35提高6dB，注意Capture每档0.75dB，不是1.5dB），Playback222/-16.5dB（提高6dB），Headphone95/-26dB、LINPUT1boost1/+13dB；无模型增益。已请用户安静5秒再麦克风距嘴10cm读两遍固定台词，分别反馈静音时杂音和人声大小。此反馈尚待；不要把“音乐响”与麦克风原始电平一致混为一谈。sample_live_levels.py重新只采标量600秒，当前24775，文件live_level_windows.jsonl。

独立电脑诊断check_low_level_robustness.py，使用部署一致step6400权重（SHA dbe07...），只有合成信号与公开FLEURS，不是录制用户：全零稳定输出RMS0.00039263/DC0.00033846；RMS0.001合成白噪声输出RMS0.00731154（约7.3倍），steady0.00750069/peak0.048205；50Hz/RMS0.001合成输入输出RMS0.00043599。公开语音整段RMS0.002时输出0.009767/peak0.291769；同源RMS0.04时输出0.041118/peak0.684646。结果low_level_robustness.json。说明模型对部分弱噪声确有增强调制与非零静音输出问题，不代表已测定现场噪声频率或只需50Hz陷波，更不代表除噪自然度验证通过。

训练输入实查48个文件未经源RMS归一化，整文件RMS最小0.014531、median0.042263、最大0.104352，源随机gain0.35–1.35。实际窗口常约0.001–0.003，与典型训练电平存在差距；整文件与1秒窗口非严格同等指标。结果training_input_level_diagnosis.json。后续须先校准实际麦克风/噪声基线，再加入低电平、静音和噪声稳健训练；不能靠同时放大所有信号/噪声或硬门切断字头证明解决，也不能用原声假装目标音色。

当前停止：sh /home/root/native_llvc_trial_20261005/board_bridge_bypass.sh stop。helper重启默认Capture35/Playback210，保留当前调整须显式追加Capture43/Playback222。神经模型当前已经停止，原声对照不是最终成果。未更改开机/SD/bitstream。
''')
print('Recorded failed gain trial, measured synthetic-noise issue, and active original-audio isolation state.')
