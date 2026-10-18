# 2026-10-11 原声确认、10分钟稳定性与注册接入

用户要求17秒对照重新播放，并明确以后现场测试必须先问是否准备好。已询问本轮准备状态，等待明确回复后才重播；此前对照听感尚未确认。此要求适用于后续所有需用户配合的试听/录音/现场测试。

用户随后明确“准备好了，开始”，已完成本轮重播，返回0、mixer恢复，目录 `/tmp/codex_pl_control_20261011/comparison_5698459714364`，日志 `board_voice_comparison_repeat1_20261011.log`。等待本轮三段可听性及音色接近程度反馈；尚未开始下一轮现场测试。

> 最新：输入者15秒录音已完成，F0约116.413Hz、有效有声覆盖4.32秒；源/目标真实配方ratio≈1.658966、Q16=108722已生成并通过双格式实板数值检查。注册后出现播放无声（参考音乐也无声，数字输入输出非零），重新初始化音频驱动与WM8960后参考音乐恢复；最后20秒实时复测用户确认可听、延迟几乎感觉不到、无杂音颤动。音频恢复根因尚未唯一定位，不算完整重复启停可靠性通过。以下等待输入者录音等为历史进度。

用户确认升降调明显、声音正常；重新20秒原声测试正常、延迟很小。主观听感通过，尚未做端到端延迟数值测量。

## 10分钟板测

控制版Q16=86856、32kHz S24_LE双声道、DMA块256，连续600秒成功结束，capture_overruns=0、playback_underruns=0，处理无报错。两路DMA中断最终各81044，相比开始前6044增加75000，等于600×32000/256块。结束后PCM采集closed；全状态补充核对见后续快照。

背景测试实际shell PID28174，启动命令输出的28173为父shell，已通过cmdline核对记录正确PID，未使用全局kill。脚本只清理自己进程并恢复mixer。

证据 `board_control_stability600_start_20261011.log`、`board_control_stability600_pid_20261011.log`、`board_control_stability600_progress1_20261011.log`、`board_control_stability600_progress2_20261011.log`、`board_control_stability600_progress3_20261011.log`。不等于30分钟稳定性或完整启动复现通过。

## 目标录音

用户提供 `voice_src` 并确认 `src_1` 的Track5～9属于同一位说话人的纯讲话。五段均为48kHz、PCM24双声道，20～29秒，左声道未检出削波；分别通过有效F0覆盖检查。

Track5～8用于目标F0注册，Track9保留用于后续评价，不参与注册统计。目标档案 `data/profiles/target.json`，F0中位数约193.125Hz，累计有效有声帧覆盖53.10秒。原始音频保持不变；质量与SHA `report/target_audio_quality_20261011.json`，执行入口 `python -m build.analyze_target_audio`。F0注册不是完整声纹或音色模型。

## 已接入的软件流程

- `src/ps/profile_recipe.py`使用stdlib把源/目标F0档案转换为比例配方，保存原档案SHA、检查质量/范围，错误时不覆盖旧配方。
- `board/run_registered_pitch.py`再次验证配方，调用PL有限时录放及配置/复位；`--check-only`不会启动音频。
- 新试验脚本支持第三参数TAG，避免相同比例/时长复测覆盖；板端新版 `/tmp/codex_pl_control_20261011/live_pitch_control_trial_v2.sh`。
- `board/capture_registration.sh`有限时采集输入者/目标声，开始前要求录放closed，保存恢复mixer；录音期间关闭PCM输出，保存native S24原始数据。
- `board/pack_registration_audio.py`明确低24位左通道、符号扩展、floor至PCM16，打包32kHz单声道WAV/gzip并保存源削波率和SHA。
- 22项Python测试通过。合成160/240Hz测试录音→档案→配方Q16=98306，在板端check-only通过，验证配方读取；**该合成夹具未用于真人注册或实际声线验收。**

## 当前待办

已询问用户是否准备好录15秒输入者校准，等待“准备好了”后才开始。目标已注册，输入者档案与实际配方尚未生成；真人录音→配方→PL现场转换闭环待验证。

当前控制版PL保留，原厂监听PID549暂停，旧视频/GPIO等外设解绑；600秒测试结束，后续先检查PCM关闭和mixer恢复。暂存目录 `/tmp/codex_pl_control_20261011`。全外设恢复仍采用冷启动，避免已知摄像头热绑定卡住。

## 真人注册与实际配方验证

用户准备后录15秒，native S24_LE stereo共480000帧，未削波/无采集overrun。明确解码左通道并floor至PCM16单声道32kHz WAV。下载gzip740719字节，原压缩SHA与解压WAV SHA全符；归档 `data/registrations/source_20261011`，输入者档案 `data/profiles/source.json`。目标F0约193.125Hz，输入者约116.413Hz，真实配方 `data/profiles/current_recipe.json` ratio1.6589663510807164/Q16=108722。

`sim/generate_registered_vectors.py`生成当前比例的两种格式黄金结果；板上 `verify_dma_control_v4.py`通过2组各8195帧结果及连续状态/错误接口检查，之后实际配方CLI执行20秒实时流并成功配置/复位。日志 `board_registered_ratio_golden_20261011.log`。

## 无声异常与恢复

用户报告注册重复轮无声，不能因零xrun认定声音正常。添加独立 `pitch_dma_stream_meter`，其实际比例黄金结果保持一致。诊断轮640000帧，input_peak32757、output_peak30709，RMS能量非零，零xrun，但用户确认参考音乐和讲话都无声且供电/接线正常。

软件时钟约12.2856MHz、音量寄存器和数字数据有正常值，这些不能证明模拟端已出声。执行 `board/reinitialize_audio.py`：确认PCM关闭，保存mixer/绑定，仅解绑重探测声卡/Formatter/I2S/动态时钟和WM8960，不重配置PL、不触及DMA或摄像头。重初始化返回0、PL operating、DMA保留，后续5秒原厂参考音乐用户确认听到。

随后注册比例20秒带参考音乐复测，最后重复轮用户确认“听到了，延迟几乎感觉不到，杂音和颤动没有”。该轮640000帧、零xrun、input_peak32757/output_peak30709。恢复只验证了这次故障可通过音频重探测恢复，根因和长期重复启停仍待追查；`reinitialize_audio.py`用audio_reset1目录锁，仅为本次恢复入口，不能直接再次运行覆盖旧状态。

证据 `board_registered_live20_repeat1_20261011.log`、`board_registered_meter_live20_20261011.log`、`board_registered_silence_diagnostics_retry_20261011.log`、`board_audio_reinitialize_20261011.log`、`board_factory_after_codec_reset_repeat1_20261011.log`、`board_registered_after_audio_reset20_repeat1_20261011.log`。

## F0量化结果与下一项音色比较

对归档15秒源录音以相同整数参考核、32kHz、Q16=108722做离线预测，处理后F0中位数197.022Hz（有效覆盖4.50秒），与目标193.125Hz相差约2.02%。这是离线参考结果，不是物理PL输出录音，不能据此声称端到端模拟输出F0已实测。指标 `report/registered_f0_prediction_20261011.json`。

预备公平音量的17秒听辨文件：目标留出Track9片段5秒→停1秒→原声5秒→停1秒→离线参考处理原声5秒。原声与处理后使用同一文本/时间段，目标文本不同，音色判断仍有内容混杂；不是正式盲评。文件 `data/registrations/source_20261011/target_source_calibrated_comparison.wav`，SHA/增益/选段位置见同目录 `comparison_manifest.json`。第三段是离线参考处理，不冒充物理PL输出录音；目标音色模型尚未实现。

对比文件已在板端完整播放，脚本返回0且恢复mixer，日志 `board_voice_comparison_20261011.log`；等待用户确认三段是否可听、参考变调是否比原声更像目标。该反馈决定下一步音色候选研发，不能把离线F0误差2%等同于音色相似度。

2026-10-11最新音色结论：用户确认三段均可听，但旧变调音色不像目标、接近单独升调且轻微颤动，目标音色验收失败。新增WORLD离线谱包络候选；25项Python测试通过；候选F0约193Hz、无削波；仍未上板实时转换，待用户本轮准备确认后试听23秒四段。根目录project_guide.md和report/world_timbre_progress_20261011.md记录恢复入口；重复启停无声的根因仍未定位。