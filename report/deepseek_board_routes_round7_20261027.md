# Deepseek 模拟播放路由验证（第7轮，2026-10-27）

任务 `LOCAL-PS-20261027-01`；基准 `b599173`。操作者本轮明确“准备好了，开始”。

## 结果

停止 world-voice 后，保存 mixer，显式打开 `Left Output Mixer PCM`、`Right Output Mixer PCM`、`Headphone Playback ZC`，设置 Headphone127/Playback255。播放一遍原始男声 PCM16 WAV、两遍由修复版 ARM 文件转换生成并降幅0.3的原生S24_LE语音。三个播放命令均exit0，未报underrun。

用户原话：**“原声和转换语音都听到了”**。

本轮工程判定：已有文件的板端模拟语音输出通过。前6轮的静音来自停止基线服务后恢复PCM路由关闭的状态，测试流程当时遗漏了重新启用路由。不能把这些失败当成模型音质问题。Deepseek原始程序另有S24_LE移位错误，主机与板端修复证据见前述报告，两类问题需要分别处理。

结束时 alsactl restore 返回0（仍有UCM配置警告），原world-voice服务start返回0。未改PL、设备树、启动分区或持久mixer配置。原始机器证据见 `deepseek_board_routes_round7_20261027.json`。

## 边界

仅验证固定已有语音的文件转换与模拟出声；这不是完整身份/泄漏/UTMOS/CER客观门或真人音色验收。此前8秒录音电平偏低；该会话只做文件处理，没有播放或上传新语音。未验证本候选现场实时流、p95端到端延迟、长期稳定性或PL路径。

复现顺序：world-voice stop → alsactl store → 左右PCM on/ZC on → 设置播放音量 → aplay S24_LE/32k/2ch → alsactl restore → world-voice start。每轮播放前仍需询问操作者是否准备好。
