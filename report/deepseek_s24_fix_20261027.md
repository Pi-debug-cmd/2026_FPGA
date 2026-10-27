# Deepseek S24_LE 接收与格式修复（2026-10-27）

任务 `LOCAL-PS-20261027-01`；基准 `7d44033`。本轮为用户指定 Deepseek 工程接收与格式修复，不是音色/实时验收。

## 证据

- 最新仓库已独立 worktree 接收，开放 PR #9/#11/#13 无 Deepseek 路线修改，原工作区 RTL 和报告改动保留。
- 实际板卡串口 COM4（CH340），COM8 为蓝牙。Linux 5.15.0-xilinx/armv7l；fpga manager 为 operating；原 v23 正在录放；交接 `/tmp/vc` 不存在。未切 PL 或设备树。
- 模型 SHA-256 `01aecb78d4a5a9b1a960f4a15cbc4bc524e005a39e59a54b107a5ebc2f32bbc5`、交付 ELF SHA `13d48df76a6366a54dce22bd4652ac50ca5f0363f44480b1a2c8e37125fee3e2` 与交付元数据一致。
- 现役 `board/pack_registration_audio.py`、`src/ps/world_live_stream.cpp` 均按低 24 位解码；Deepseek 的批处理、PL 程序与共用 stream include 却右移输入 8 位、左移输出 8 位。这与 ALSA S24_LE 的低 24 位契约不符。
- 主机对同一 PCM16 与 S24_LE 测试信号做全转换对比：修复前最大误差 0.651123，修复后批处理和 300 ms 流式均为 0.0000152587890625（小于 PCM16 一个量化步长）。机器证据见 `report/deepseek_s24_format_parity_20261027.json`。
- 由仓库标准录音 4 的 1–5 秒、双声道平均、48k→16k、多相重采样、峰值 0.35 的开发片段产生参考输出；模拟左移 8 位后按低 24 位解码，相关性约 0.001685，RMS 由 0.077316 升至 0.540402。此为数字格式诊断，不是模拟输出或真人听感结论。准备脚本最初误按 PCM24 解码了该 PCM16 WAV，已纠正，初版输入不用于正式评价。

## 改动与复现

只修改 Deepseek 三处 PCM 输入/输出位打包，不改变模型/算法/PL 时钟；新增格式对比检查与无声板端文件测试脚本。

```powershell
./Deepseek/host/app/build_host.ps1 -Cxx D:/mingw64/bin/g++.exe -Out "$PWD/build/generated/deepseek_ds01/vc_host_fixed.exe"
python build/verify_deepseek_s24.py --exe build/generated/deepseek_ds01/vc_host_fixed.exe --model Deepseek/host/model/student_v5_o64.blob --output build/generated/deepseek_ds01/format_parity.json
./Deepseek/host/app/build_arm.ps1 -GccDir D:/USER_Software/vivado/2026.1/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin -Out "$PWD/build/generated/deepseek_ds01/vc_s24fix_arm"
```

ARM GCC 13.4 构建成功，ELF32/ARM/EABI5 hard-float/static，582,928 B，SHA `96b6937f6c103465d34ad3800d80c72253558ef35a05388f8241359aae4e6d4c`。生成物不提交。交付 PL 程序的源码路径同步修正，但未重新加载或验证 PL。

## 现场与限制

操作者本轮明确回答“已接好，可以开始本轮录放测试”。首次串口传输在 v23 运行时出现 input overrun，校验中断，未使用不完整文件；随后经 `/etc/init.d/world-voice stop` 停止，两个 PCM 都 closed，在新独立路径重传并校验。尚未执行新音频采录或播放，模拟时钟问题不能凭警告断定。下一轮将完成同输入板端数值回归、低音量格式验证及本轮授权的现场测试。

Deepseek 已报告 UTMOS 低于 2.30、泄漏/CER 口径与根计划不充分，不能称五门通过；本轮用户明确指定工程诊断，既有候选分工与正式门槛不更改。
