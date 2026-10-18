# WORLD滑窗现场测试入口

> 本文件是 WORLD 实时链路的现场操作入口。**当前状态与硬约束以 [project_guide.md](../project_guide.md) 为准**（2026-10-16：全脱机构型、现场注册目标声源、每轮录放先取得准备确认）。本文描述的 v18/40ms 滑窗为历史版本，其逐日记录见 `交接/归档_md_20261016/handoff/handoff_20261013.md` 与 [协作记录](../report/ai_worklog.md)。大小声适应专项按用户要求放到基本功能完成后的最终调优/验收，当前不反复调整增益。

当前代码采用40ms滑窗、160ms历史、40ms分析未来、32ms合成前视；Q16=108722、共振峰1.0975。参见 [开发与实测证据](../report/world_live_development_20261013.md)。已有PL变调基线保留，新WORLD声线算法目前在PS执行；原厂音频接口不等于新增PL算法加速已完成。

## 执行规则

开发、上传和文件计算无需用户配合可自主进行；每次需要讲话/试听/录音时，先确认本轮准备状态。未收到本轮明确答复不得执行 `--run`。用户恢复开发不等于准备试听。

先确认实际串口（历史记录为 COM14/115200，**2026-10-16 本机只枚举到 COM7/COM8**）及冷启动状态，不沿用旧PID或重启前的 `/tmp`。所有测试数据仅在 `/tmp/codex_world_20261013`，不改启动分区，不自动加载PL、操作设备树或热绑定摄像头。禁止全局kill。

## 版本与已测边界

| 入口 | 配置 | 实测情况 |
| --- | --- | --- |
| `live_world_trial.py`（板端v12历史） | 前级boost1、软件输入1/输出1、180ms | 可听，但14次欠载、30个输出削波，失败 |
| `live_world_trial_v13.py` | boost1、输入1/输出0.75、240ms | 20秒零xrun，但输入近满幅1200、输出削波69，失败 |
| `live_world_trial_v14.py` | boost0、输入2/输出0.75、240ms | 音量足够且自然，输入/输出饱和消除；2次欠载，失败 |
| `live_world_trial_v16.py` | boost0、Capture恢复值39/+12dB、输入2/输出0.75 | 240ms及200ms各20秒零xrun/削波，用户240ms自然连续无杂音、200ms等待感减轻；180ms有1次欠载和短断音，未通过 |
| `live_world_trial_v17.py` | boost0、Capture31/+6dB、输入4/输出0.75、200ms；复用runtime v16 | 本地补偿/恢复检查及部署检查通过；60秒现场结果以开发报告最新记录为准 |

以上缓冲数字为启动静音前缀配置，**不是实测端到端延迟**。原p95≤100ms目标未验收。20/60秒结果也不能代表30分钟稳定性或正式身份相似度。

## 部署

ARM构建（当前有效runtime v16）：

```powershell
./build/build_world_budget.ps1 -SourceFile world_live_stream.cpp -AlignedStreamFull -BinaryName world_budget_v16
```

构建前先查本日报告和清单，禁止覆盖已有黄金二进制。对应源SHA和二进制SHA在 `build/generated/world_budget/world_live_manifest_v16.json`；v17为监督配置清单 `world_live_manifest_v17.json`，二进制仍为v16。

上传器支持断点续传，同一远端文件的 `.b64` 暂存不能混用不同内容；更新助手/清单使用新版本名。文件入口 `board/upload_file.ps1`，日志入 `report/`，顺序占用COM14，不并发执行串口操作。许可证一起暂存。

## 只读预检

```sh
python3 /tmp/codex_world_20261013/live_world_trial_v17.py --check
```

预检检查运行时SHA/可执行、CPU在线、arecord/aplay/amixer/alsactl存在、PCM录放closed。它不播放音频，也不改变mixer。

## 收到本轮准备确认后的有限时测试

```sh
python3 /tmp/codex_world_20261013/live_world_trial_v17.py --run \
  --seconds 60 --prefill-ms 200 --output-gain-q16 49152 --input-gain-q16 262144
```

默认20秒，允许2～60秒。脚本先保存mixer，使用hw:0,1录音、default播放，均32kHz/S24_LE双声道，period512。采集请求buffer4096，实板曾协商为3072；播放buffer3072、起播阈值实测1024。实际参数写入测试目录，不能只按请求值报告。

每次测试目录名称唯一，保存mixer、各阶段日志、hw_params和result.json。看门狗为录音时长+15秒，子进程异常时只收回自己创建的进程，再恢复mixer并确认PCMclosed。削波退出6发生在完整处理之后，允许播放器正常排空后再拒绝本轮。

查看 `WORLD_LIVE_STARTED` 和最终JSON。检查整体/三个子进程/运行时退出、录放xrun、输入接近满幅与输出削波、输入输出样本数、参数提交消费数、FIFO峰值、mixer恢复、PCMclosed。用户听感独立记录。退出0只代表该轮上述程序门槛通过，不自动判音色或延迟验收。

## 故障及结束

不要因可听而忽略xrun或削波。180ms失败记录保留；新候选失败回到已测200ms/240ms配置，下一轮现场测试仍要单独确认准备状态。

脚本会自动清理。若被外部中断，先只读检查当前PCM/本次进程与result.json，不按历史PID发信号，不要求重启或重插来替代诊断。mixer恢复失败或PCM仍忙时不能开始下一轮；根据本次日志定位，勿热绑定摄像头。


## v18 FIFO候选补充

v18 runtime/监督/清单已部署，文件数值和FIFO生效/超时/SIGTERM核对通过，尚未现场录放。FIFO分析/合成优先级10，采集/输出20，设置失败返回8；未限速文件压测出现内核RT限流，不能当实际录放通过。恢复并得到新一轮准备确认后才可使用：

```sh
python3 /tmp/codex_world_20261013/live_world_trial_v18.py --run \
  --seconds 60 --prefill-ms 200 --output-gain-q16 49152 --input-gain-q16 262144 --fifo
```

v17的200ms/60秒虽音量自然度正常、输入/输出无饱和，但日志2次播放欠载，整体失败。v16/200ms和240ms仅各20秒通过；180ms出现欠载和可闻短断音。所有原始失败记录保留，不把用户未察觉断音等同于零xrun。
# 2026-10-14 调度候选补充

后续诊断：v20监督助手复用runtime v19，加入Codec before/configured/active只读快照与可选--require-voiced。参考音乐44.1kHz可听正常；200ms/20秒791有声帧、零欠载/触顶/削顶、听感自然连续，180ms/20秒690有声帧但2次播放欠载，未通过；用户未察觉异常不覆盖日志。两个有声轮次MICB/ADC/DAC/HP运行态均On，之前无声根因尚未确认，保持200ms回退点。

v21是新的runtime与监督器版本：算法和增益不变，加入analysis_stage_s五阶段墙钟耗时，有限运行上限600秒。清单world_live_manifest_v21.json、二进制world_budget_v21、助手live_world_trial_v21.py。主机16项回归与v19 PCM一致、600秒文件计数/边界与15项监督器检查通过；板端、3/10分钟现场仍待验证，不据此宣称长期稳定。

长时讲话候选命令，仅在上传/板端检查完成且本轮另获准备确认之后执行：

    python3 /tmp/codex_world_20261013/live_world_trial_v21.py --run --seconds 180 --prefill-ms 200 --output-gain-q16 49152 --input-gain-q16 262144 --fifo-io --require-voiced

预检使用同一助手的--check，不会启动录放。大小声适应专项继续留到基本完成之后。

v18全线程FIFO的60秒现场试听反馈自然连续、未察觉断音，但日志有8次播放欠载、23个输出削顶样本，并出现内核RT限流；不能标记为通过。当天原始与结构化记录见 `report/board_world_live60_v18_fifo_20261014.log`、`report/world_live60_v18_fifo_20261014.json`。结束后mixer恢复成功、PCM均closed。

v19新增可选 `--fifo-io`：仅管道读取/写入线程使用SCHED_FIFO/20，分析与合成显式使用并核对SCHED_OTHER/0。保留内核RT预算；音量、算法、200ms启动前缀保持原配置。这是待验证候选，不能写成稳定性或延迟验收。

新助手 `live_world_trial_v19.py` 使用 `world_live_manifest_v19.json`；不录放预检命令：

```sh
python3 /tmp/codex_world_20261013/live_world_trial_v19.py --check
```

下面真实录放命令仅可在用户本轮明确准备后执行，之前的准备确认不能复用：

```sh
python3 /tmp/codex_world_20261013/live_world_trial_v19.py --run --seconds 60 --prefill-ms 200 --output-gain-q16 49152 --input-gain-q16 262144 --fifo-io
```

`board/check_world_paced_cpu.py` 是无ALSA的合成文件节拍诊断，CPU统计与管道读取间隔不能当作现场欠载或端到端延迟测量。大小声适应专项按用户要求留到基本功能完成之后。

