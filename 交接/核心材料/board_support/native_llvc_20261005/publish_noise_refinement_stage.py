from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent
project=r.parents[1]
phase1=json.loads((project/'board_budget_20261005/small96_noise_training/decision.json').read_text(encoding='utf-8'))
phase2=json.loads((project/'board_budget_20261005/small96_noise_refinement/decision.json').read_text(encoding='utf-8'))
checks=json.loads((r/'noise9200_deployment_check.json').read_text(encoding='utf-8'))
snapshot=json.loads((r/'noise9200_first_live_status.json').read_text(encoding='utf-8'))
report={
 'date':'2026-10-05','scope':'Noise/volume isolation and live noise audition, not final VC acceptance',
 'human_prior_neural_feedback':'明显杂音、电流音，人声相对很小',
 'human_calibrated_original_feedback':'安静时基本无杂音，人声够大',
 'human_current_neural_feedback_pending':True,
 'original_isolation_settings':{'Capture':43,'Headphone':95,'Playback':222,'digital_gains':1},
 'current_settings':{'Capture':35,'Capture_db':9,'Headphone':101,'Headphone_db':-20,'Playback':222,'Playback_db':-16.5,'digital_input_gain':1,'digital_output_gain':1},
 'gain_change_reason':'Original accepted level logs included RMS0.395901 and peak0.75 windows; reduced capture6dB, added headphone6dB for headroom. No assertion of ADC clipping from S16 clip counter.',
 'first_noise_training':{'steps':1600,'total_steps':8000,'checkpoint':str(project/'board_budget_20261005/small96_noise_training/checkpoint_step1600.pt'),'quiet_loss_weight':3,'validation_edits':22},
 'second_noise_training':{'steps':1200,'total_steps':9200,'checkpoint':str(project/'board_budget_20261005/small96_noise_refinement/checkpoint_step1200.pt'),'quiet_loss_weight':18,'validation_edits':27},
 'both_geometry':{'E':96,'D':48,'parameters':173456,'rate':16000,'chunk_samples':208,'lookahead_samples':16},
 'training_only_sources':48,'test_speaker_status':'Earlier heldout now diagnostic, never weight updates',
 'runtime_noise_gate_added':False,'source_speaker_enrollment':False,'user_audio_recorded':False,
 'new_weight_sha256':phase2['weights_sha256'],'new_weight_bytes':740939,
 'synthetic_checks':checks,'first_live_snapshot':snapshot,
 'pids':{'capture':24958,'convert':24959,'playback':24960},
 'startup_underrun_ms_observed':234.891,'acoustic_latency_measured':False,
 'board_temperature_raw_first_snapshot':2743,'board_temperature_c_first_snapshot':64.473364257616,
 'neural_runs_in':'PS dual Cortex-A9 NEON; PL is existing vendor audio interface, custom accelerator not deployed',
 'start':'LLVC_INPUT_GAIN=1 LLVC_OUTPUT_GAIN=1 sh /home/root/native_llvc_trial_20261005/board_neural_noise.sh start',
 'stop':'sh /home/root/native_llvc_trial_20261005/board_neural_noise.sh stop',
 'accepted_original_restore':'sh /home/root/native_llvc_trial_20261005/board_bridge_bypass.sh start; amixer sset Capture 43,43 cap; amixer sset Headphone 95,95; amixer sset Playback 222,222',
 'board_live_noise_quality_accepted':False,'target_voice_quality_accepted':False,
 'content_regression_not_resolved':True,'next':'Real microphone noise/volume feedback, then recover content/pronunciation and target identity without undoing noise suppression.'}
(r/'noise_refinement_stage_evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
p=r/'realtime_stage_evidence.json';d=json.loads(p.read_text(encoding='utf-8'))
d['stage']='Noise-refined9200 model in live noise/volume audition; content regression27/152 vs22/152, NOT final quality approval'
d['current_diagnostic']['active']=False
d['human_live_feedback']['calibrated_original_capture43']='安静时基本无杂音，人声够大'
d['human_live_feedback']['noise9200']='尚待现场音量/杂音反馈'
d['live_actual_output_running']=True;d['latest_live_status']=snapshot
d['current_noise_refined_student']=report
d['target_quality_accepted']=False
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
doc=Path(r'D:\总进度\7020实时小模型工程续接_2026-10-05.md')
marker='## 噪声隔离完成，9200步抗噪模型已上板作限定试听'
text=f'''

{marker}

用户对原声对照（Capture43/+15dB，Headphone95/-26dB，Playback222/-16.5dB，S16/16k经同一格式桥）明确反馈“安静时基本无杂音，人声够大”。这说明音箱接线与本格式桥的基本音量/噪声可以达到可用状态；此前严重杂音主要在模型路径增加。不能据此认定所有环境完全无硬件噪声，更不能把原声对照当目标转换。

标量原声文件bypass_capture43_level_windows.jsonl全SHA核验4248089fab52c71c7139995092af6e638213497dce1832cef1c3ac6d767e8db2，只有标量，没有用户波形。部分窗口出现RMS0.395901/peak0.75；S16 clips0只是没到±1，不能证明ADC/前级没有削波。为保留采集余量，当前模型用Capture35/+9dB，比原声对照低6dB；Headphone改101/-20dB补6dB，Playback仍222。已向用户解释采集余量与播放音量分开调整。此组合仍需现场反馈，不能直接继承原声对照的验收结论。

第一轮抗噪训练从旧6400步模型续1600步，总8000：脚本neural_reference/train_board_noise_robust_20261005.py，目录board_budget_20261005/small96_noise_training。每批2条语音加1条合成非语音；只有原48条训练语音更新权重，源gain0.10–1.35，60%语音加24–42dB SNR合成噪声；合成非语音有全零、白噪声、低通噪声、50/100/150Hz、带直流混合，RMS0.00005–0.006，目标严格零。目标语音仍为既有源时序CV3教师，无变速/相位声码器/逐人登记。loss为5谱+6ContentVec+1.5声纹+3静音项（meanabs/.005+meansquare/.0001），400步后有.25GAN+1feature matching。保持173456参数E96/D48结构，FP32，lr3e-5，不添加运行时硬门。

第一轮权重SHA55e9ce14c1777abba4717af5432f4d7509be8901d51257c82479e1a1439f0191。固定合成白噪声RMS0.001时输出由0.00731154降到0.00341189，但仍放大，因此没有让用户试听此版。8条固定验证音频中文自动识别仍22/152，声纹均值0.68636（训练用过，不能作为独立相似度审批）。

第二轮从8000续1200步，总9200：train_board_noise_refine_20261005.py，目录small96_noise_refinement，lr5e-5，静音项权重18，其余结构和主损失相同；最终固定checkpoint_step1200.pt，没有用测试集挑选中间点。训练约236.39秒；上一轮约328.98秒，均不包含后续流式导出。中间checkpoint总步数元数据曾因生成文本替换偏高，已修正400/800/1200对应8400/8800/9200；checkpoint_metadata_repair.json核对所有模型tensor SHA未改变，原始导出权重未变。源脚本也修正为8000+step+1。

最终权重small96_noise_step9200.f32仍740939字节，SHA {phase2['weights_sha256']}。CPU合成信号检查noise9200_robustness.json：全零最后1秒RMS0.00002419（旧0.00039263，降低24.21dB）；同一RMS0.001白噪声输出0.00085519（旧0.00731154，降低18.64dB）；RMS0.002/0.004白噪声输出0.001141/0.002611，没有在这些固定条件下增强到超过输入RMS。正常公开语音RMS0.04输出0.0349426（旧0.0411183，下降1.41dB）；弱语音RMS0.002输出0.0088915。这些是电脑上合成/公开输入，不是现场录回，不能宣布电流音已解决。全零最初启动peak仍0.00396，稳定静音与初始化瞬态须区分。

重要退步：第二轮8条同一验证音频自动识别27/152，比旧版和第一轮22/152增加5处；teacher9/152、source5/152。声纹均值0.68206，仍不是独立感知验收。overall_quality_passed=false，content_regression=true，目标自然度/中文清晰度没有验收。已明确向用户说明“减少噪声但中文识别有退步”，当前上板范围仅为真实麦克风的音量与杂音试听；不能将此版当整体升级或已完成项目。

安装包noise_refine_candidate_bundle.tar.gz683334字节，UART230400全SHA核验03a540401fadebd181cd25c987816a58f1f655431f02ed1471b8bcb0542be952，恢复115200。未换算子程序，仅使用已验证meter二进制加载独立9200权重；旧6400及其helper保留。板上1秒真实公开float输入推理0.8596秒/77块，平均11.1548ms、max12.526、RSS2784KiB；实际ARM与Torch同新checkpoint流式输出NRMSE2.10297e-5、maxabs4.7963e-8。结果noise9200_deployment_check.json，实际ARM输出SHAca7a32934db47b59a565415b5983b80d21181b578c0d5591682ee7659834b95f。文件算数与吞吐验证通过不代表听感或发音通过。

当前现场已切回真正神经转换（不再是原声）：LLVC_INPUT_GAIN=1 LLVC_OUTPUT_GAIN=1 sh /home/root/native_llvc_trial_20261005/board_neural_noise.sh start。PID capture24958、convert24959、playback24960。helper默认Capture35、Headphone101、Playback222，数字增益均1。首次1309块snapshot：输入272288、输出272272，mean11.298177ms、max15.835074、29块超过13ms；输入窗口RMS0.001543/peak0.033386，模型输出RMS0.003070/peak0.103372，输出clips0。需要用户实际反馈，不宣称所有窗口无ADC削波/所有13ms块按时。启动一次underrun234.891ms；本记录未验证长时零欠载。温度raw2743约64.47℃。仍是PS双核NEON神经推理，PL为既有官方音频链，未部署自研HLS加速核，没有声学端到端延迟实测。

已请用户先安静5秒再距嘴10cm读同一句“我的校园很美，走近大门就能看见宽阔的操场。”，仅验收人声大小和电流音/杂音，反馈尚待。若还吵，要针对真实低电平/非平稳背景检查模型输出；若噪声改善则下一步恢复中文内容/字边界，保留静音约束，不能忽略27/152的退步。不要用硬门吞声母、原声替换或声纹分数来证明改进。后续目标音色、陌生说话人、中文正确性、测量端到端延迟、自研PL核心均仍未完成。

停止当前：sh /home/root/native_llvc_trial_20261005/board_neural_noise.sh stop。
恢复已接受的同格式桥原声诊断：sh /home/root/native_llvc_trial_20261005/board_bridge_bypass.sh start；随后amixer sset Capture 43,43 cap；amixer sset Headphone 95,95；amixer sset Playback 222,222。该恢复不是目标声音转换。当前新helper没有开机自启，没有修改SD分区/boot bitstream/野火原件。旧voice-live.sh start bypass是另一条44.1k原声路径，也不能冒充目标转换。

本阶段机器证据noise_refinement_stage_evidence.json及realtime_stage_evidence.json已更新，代码和产物均在D盘。此节覆盖前文“原声直通仍在运行”“用户原声噪声未反馈”的状态。
'''
if marker not in doc.read_text(encoding='utf-8'):
    with doc.open('a',encoding='utf-8') as f:f.write(text)
print('Published noise refinement, Chinese regression, active prototype, and recovery evidence.')
