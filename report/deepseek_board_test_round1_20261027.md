# Deepseek 独立板端测试轮 1（2026-10-27）

任务 `LOCAL-PS-20261027-01`，源码基准 `40e4292`，板卡 COM4 / Zynq-7020 / Linux 5.15.0-xilinx；无 PL 重载、设备树或启动项改动。操作者明确确认本轮录放准备。模型和程序逐件 SHA 见 JSON。

## 结果

- 5,429,740 B 传输归档 SHA `03b384585bc13508477b5c56c8854d438795a0f2b42378ae371f8fa460894265`，双端一致；工具归档 387,966 B SHA `ec425cc1f03556c4eb6ce9f21930d7ee01964bd61bdb733425cf60706959720c`，双端一致。
- 同一 4 秒浮点输入、同一 O64 模型：交付 ELF（VC_PL=0）、GCC13.4 格式修复版和 Windows 主机输出 SHA 均 `80489b1e805f5a5325f6542381df855ccf27da6b1d6d7411fc0efa32e501aeb4`，64,000 float 样本逐字节相同。
- 两份 ARM 程序 wall 3.2902/2.9390 秒，内部 RTF 0.8103/0.7236；仅为单次文件吞吐，不是公平微优化对照、端到端延迟或实时验收。
- 修复版 native_s24 输入输出 4 秒完整，内部 RTF 0.7772、exit 0。此路径输出 SHA `2ff1ff678f5023962e79953e016a10eeb2ddfa2160399f924af80c201d8d8a33`，与 Windows 主机文件 SHA 不同，尚未逐样本量化差异；不得把浮点路径逐字节一致推广到该路径。
- 低电平 660 Hz/0.7 秒测试音、降幅 0.3 的已有验证语音 4 秒，以及 300 ms 提示音播放均 exit 0；未见 aplay underrun。WM8960 时钟警告仍打印，不能凭该警告断定噪声根因。
- 提示音后等待 150 ms 采集 8 秒；左/右 peak 0.008343/0.006683，RMS 0.000417/0.000335，削顶 0。电平低，未确认是否有足量有效语音；不能作为音色客观门输入。
- 该录音经修复版 native_s24 / 300 ms 分块文件转换：27 块、2,048,000 B、8 秒完整输出，exit 0，wall 5.7579 秒，处理 RTF 0.6964、削顶 0。未播放此新会话转换输出（质量门未建立）。
- 遥测里的逐块 proc_ms 实为累积值，block_rtf 因此也不能当单块耗时；仅使用最终 cum_rtf/rtf，未据该字段计算 p95。
- mixer 已 alsactl restore，返回 0（附 UCM 警告），原 world-voice 服务恢复 pid914、录放 PCM 均 RUNNING，FPGA operating。证据 `deepseek_board_restore_20261027.json`。

## 数据与复现

源为仓库男声标准录音 4，WAV SHA `f4a026e5c97f3bf25447876101dce71a6a160e8ebc81b9b488c7d3a41c62d68c`；PCM16/48k/双声道平均，重采样 16k，取 1–5 秒并峰值归一化 0.35。4 秒输入 SHA `e7fa772cdb701972bea4c6e8f2f946ea7b333756def1bc02a0edaa6b8b45e409`。

在仅包含本轮模型、两个 ELF 与 input.f32 的 `/tmp/codex_deepseek_ds01` 执行 `python3 board/deepseek_file_test.py`（脚本先上传该目录）；原生文件测试为 `./vc_s24fix_arm 4 native_s24 200 --model model.blob --preset live < input_s24.raw > native_output.raw 2> native.log`。现场诊断入口 `board/deepseek_audio_diagnostic.py --capture`，必须先取得该轮准备确认且服务 stop。

原始机器证据：`deepseek_board_file_20261027.json`、`deepseek_board_audio_20261027.json`。新录音及输出只存板上本轮 /tmp 目录，未下载或提交。用户未给听感结论，要求“重新来一遍”；下一轮仅重放现有测试音与验证语音。

## 判定

数值与格式工程诊断部分通过；模拟听感待确认。没有五门音质、PL、端到端实时/延迟或稳定性验收结论。
