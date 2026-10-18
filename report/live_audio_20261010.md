# 2026-10-10 实物音频试听与无声排查

当前结论：**用户确认同一音响/线缆接电脑可用；厂商音频及其44.1kHz、32kHz对照均可听。实物语音闭环验收仍未通过。** 不能用零xrun、文件有电平或进程退出0代替可听声音与语音清晰度。

## 后续排查：可听播放基线已找到

- 用户确认同一音响/线缆接电脑能发声，并插回绿色接口。
- `board_factory_playback_probe_20261010.log`：厂商 `/opt/hardware_test/test.wav`，default播放路径，44.1kHz S24_LE双声道，period5512/buffer22048，5秒0欠载，用户听到音乐/人声。
- `board_factory_rate_probe_20261010.log` 和 `board_factory_rate_probe_drain_20261010.log`：同一厂商音乐解包为24位低位32位容器，保持配置，44.1kHz/32kHz各5秒，用户两轮均可听。准备转换在板端较慢，串口首次25秒等待超时，但测试仍继续；仅重开串口读取，未重启测试，最终退出0，32kHz欠载0。44.1kHz播放日志另归档在 `board_audible_configuration_20261010.log`，没有欠载报告。
- 可听配置：PCM左右输出打开、Headphone Playback ZC开启、Headphone105、Playback230，default解析为plug/mmap_emul。32kHz播放period4000/buffer16000，起播阈值16000；与先前直接hw播放、小缓冲、不同增益和ZC状态存在多项差异，**尚不能归因于其中单项**。
- `board_known_audio_probe_20261010.log`：单一24秒数据流，音乐5秒→录音7秒→音乐5秒→变调7秒；后两类录音临时放大8倍，两份均0削波，播放0欠载。用户反馈“都有声音，音调确实提高”。这证明此次播放可听及该录音变调有升调效果，不代表自然音色或长期稳定性。
- 只读DAPM检查显示之前无声配置与厂商路径播放时DAC、HP_L/R、左右PGA均On，ALSA指针推进；不能把电源缓存On视为物理输出成功。wm8960“slave mode…no clock configuration”在可听测试也出现，单凭该日志不能断言时钟就是根因。
- 稳健串口下载 `board/download_file.ps1` 不复位、不主动Ctrl+C，文件按长度/SHA校验后才落盘。已提取排除启动瞬态的7秒PCM16录音到 `data/diagnostics/captured_excerpt.wav`，压缩传输262672字节，SHA `aa4d4f9c3a60a747385d5c185e14454991ca8bea736713d92d398053a7b0e5aa`。本地分析 `captured_excerpt_analysis_20261010.json`：RMS0.008612、peak0.114838、YIN有声帧111/697（1.11秒覆盖），**不足现有注册3秒门槛**。不把此片段当注册样本。
- v4实时采集：沿用上述可听播放基线并设置LINPUT1模拟boost=1，采集仍32kHz；首次20秒0/0，但用户未准备，听辨无效。用户要求再次20秒，保存到独立repeat目录，反馈待补充。首次上传因Windows CRLF语法失败，转换LF后 `sh -n`通过才执行；失败轮未进入录放。

v4 repeat已正常结束：`board_live_pitch_v4_repeat_20261010.log` 采集overrun=0、播放underrun=0；`board_live_v4_repeat_state_20261010.log` 核对实际采集period512/buffer3072，播放period4000/buffer16000，录放均closed，Headphone101/Playback215已恢复。用户随后确认“能听到讲话，音调升高了，延迟还是比较明显”。只判此次PS实时链路可听且升调，不判低延迟、音色自然度或长期稳定性。

所有正常完成的测试均恢复此前mixer；只读归档确认Headphone101/Playback215、Headphone ZC off，PCM状态closed。未改SD、加载新PL或修改旧模型。下一步保持其他设置缩减播放缓冲；G1尚需真实旁路、PL回传与可追溯结果。

### v5：只缩减播放缓冲

新脚本 `board/live_pitch_low_latency_trial.sh`，保留原 `live_pitch_trial.sh` v4回退。采集不变，播放仍default，但period4000→512、buffer16000→3072、start-delay32000μs（32kHz相当于1024帧请求起播阈值）。缓冲容量500ms→96ms，起播阈值32ms；这些是配置换算，**不是实测端到端延迟**。

用户准备后执行20秒，`board_live_pitch_v5_20261010.log` 返回0、采集overrun=0、播放underrun=0；用户反馈“延迟明显减轻，持续可听，没有明显的断续杂音或颤动”。只读核验 `board_live_v5_state_20261010.log`：录放实际period512/buffer3072，播放实际start_threshold1024，录放closed、Headphone101/Playback215恢复。

随后在独立目录 `/tmp/codex_pitch_trial_v5_stability_86856` 连续运行60秒，不要求用户持续讲话；`board_live_pitch_v5_stability_20261010.log` 返回0、零xrun。状态归档 `board_live_v5_stability_state_20261010.log` 同样确认参数与恢复。v5作为后续PS-only可听基线；60秒不能替代10分钟G1或30分钟稳定性验收，也没有定量端到端延迟、PL参与或目标音色结论。

## 实際操作与结果

用户确认准备后经COM14操作。本轮开始发现/tmp试听文件丢失，恢复本项目程序与脚本并核SHA；未改SD、位流或神经模型。

| 测试 | 日志/客观结果 | 用户反馈 |
| --- | --- | --- |
| v1原声20秒 | `board_live_bypass_20261010.log`，overrun=0、underrun=1249 | 完全无声 |
| v2原声20秒与变调20秒 | 两个v2日志，均0/0 | 两轮完全无声 |
| 独立4秒440/880Hz测试音+8秒采集 | `board_audio_path_probe_20261010.log`，0/0，采集2048000字节/256000帧 | 两段测试音可听 |
| v3原声10秒与变调20秒 | 两个v3日志，均0/0 | 原声可听（该轮比例1，本来不变调）；变调完全无声 |
| 保存录音原声/变调，各7秒 | `board_saved_audio_probe_20261010.log`，均0欠载 | 全无声 |
| 临时提高输出增益后的同录音回放 | `board_saved_gain_probe_20261010.log`，均0欠载 | 全无声 |
| 同一流：提示音/原声/提示音/变调 | `board_combined_audio_probe_20261010.log`，0欠载 | 全无声，包括提示音 |

这些结果不能合并为“原声稳定通过”。仅一次独立测试音与一次实时原声获得可听反馈，后续同数据流播放仍失败。故障未定位到唯一根因；既不能断言变调算法导致，也不能排除配置/声卡开闭/物理输出因素。

## 找到并修复的局部问题

- 启动后的 `Left Input Mixer Boost`、左右 `Output Mixer PCM` 为off。v2临时打开必要通路，结束通过声卡快照恢复。
- 首版aplay起播参数1000μs太低，出现约每周期欠载；改为32000μs后短测欠载归零。但这只修复数据调度指标，不等于修复可听输出。
- 初次修复漏了当前设备树依赖的 `Right Input Mixer Boost` 供电路径。v3保留右输入通路以维持MICBIAS，同时数字输出选左ADC复制双声道，遵循已知交接供电约束。
- 实际ALSA参数：32kHz、S24_LE、2声道、period512、**buffer3072**，与请求4096不同。日志已保存，不能按请求缓冲计算实测延迟。
- 脚本现保存完整mixer快照，并在退出时恢复；原音量Headphone101、Playback215，诊断曾临时改为119/222，最终已核对恢复。测试子进程均已退出，未停全局服务。

## 采样与算法输出证据的界限

独立采集8秒，非零帧255993/256000，peak=0.8307991、RMS=0.0303467；首秒有较大启动瞬态，后续秒RMS约0.00098～0.01646。**变化的电平不能证明里面是清晰讲话**，尚未获得录音内容的听辨确认。

同一录音离线经本项目ARM变调程序（Q16=86856）处理，返回0、长度仍2048000字节，非零帧253814，peak=0.5845947、RMS=0.0264668。输出没有清零，但不保证可懂语音或自然度。独立回放时已跳过首秒启动瞬态。

Python/RTL/PS数值验证仍保留其原作用范围；本轮没有加载PL变调核。端到端延迟、目标音色和长期稳定性均未验收。

## 接续点与复用边界

1. 同一音响/线缆已由用户接电脑验证可用，随后插回绿色接口；厂商音乐已听辨，继续核查录音内容与播放配置。
2. 物理输出确认后，恢复到统一配置，先用同一数据流里已知测试音与已知可懂语音复核，取得录音内容听辨；不要马上继续试音色模型。
3. 若仍出现信号/可听性矛盾，检查PCM时钟、WM8960电源/路由与声卡开闭时序，必要时按厂商原始播放流程对照；不要靠重复提高音量包装成功。
4. /tmp诊断录音、脚本和mixer状态只在当前上电期间保留，重启会丢失；再次运行同一脚本须先归档并核对专用目录，当前脚本故意拒绝覆盖已有目录。

相关源脚本：当前可听基线 `board/live_pitch_low_latency_trial.sh`（v5），大缓冲回退 `board/live_pitch_trial.sh`（v4）；历史排查 `audio_path_probe.sh`、`saved_audio_probe.sh`、`combined_audio_probe.sh`。历史回放脚本用于提高输出增益的诊断，不能当默认验收音量。原始日志均位于本工作区report目录，后续不覆盖同日期记录。
