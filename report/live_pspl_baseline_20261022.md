# 保底方案 PS 基线：板端 60 s 真实 ALSA 录放验证（2026-10-22）

> 目的：在进入 PL 加速前，把当前最优 PS 实现（A1/WORLD 优化实时链，render RTF 0.46→0.29 的 `ps_opt_20261018`）放到板上做**真实麦克风→耳机**的 60 s 实时验证，作为“当前 PS 方案”的板端基线。
> 本轮只做板端实时链路验证：未改 GitHub、未改 PS 算法、未做音色门结论。

## 1. 条件

| 项 | 值 |
| --- | --- |
| 板卡 | 野火 Zynq-7020（xc7z020clg400-2），PetaLinux 2022.2，root@zynq_plnx |
| 连接 | COM4 串口 115200（命令与日志回传） |
| PL | 厂商音频设计，`fpga_manager` = operating，WM8960 + I2S + formatter 正常 |
| 运行时 | `world_budget_v23`（= `build/generated/ps_opt_20261018/live_stream_opt_arm`，SHA-256 `f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7`） |
| 监督脚本 | `board/live_world_trial.py`（每 60 s：alsactl 存 mixer → 配置 WM8960 → arecord S24_LE 32 kHz stereo → 运行时 native_s24 → aplay default；结束时恢复 mixer） |
| 输入增益 | 262144（4×） |
| 输出增益 | 0.60（q16 = 39322；0.75 时出现削顶，见第 2 节） |
| 提示音 | `cue3.wav`（2.05 s：1000 Hz×2 + 1320 Hz，最后 1 s 静音），操作者听到后立即连续说话 |

## 2. 三次尝试

| 轮次 | 目的 | 结果 | 判定 |
| --- | --- | --- | --- |
| #1 静音轮 | 框架冒烟 | exit 0、零 xrun、零削顶；但 `voiced_frames=8`（操作者没来得及说，采集几乎静音） | 不算语音轮 |
| #2 真实语音（增益 0.75） | 有效语音 | `voiced_frames=1129`、零 xrun；但输出削顶 **28** 样本（runtime exit 6） | 按“零削顶”门槛 REJECTED |
| #3 真实语音（增益 0.60） | 有效语音 | **exit 0、零 xrun、零削顶、`voiced_frames=1201`** | **PASS（本轮基线）** |

## 3. 通过轮（#3）关键指标

| 指标 | 数值 |
| --- | --- |
| 时长 / 帧 | 60.0 s，1502 个参数块（200 ms 块），captured16k = 960000 |
| 退出码 / 子进程 | 0 / `[0,0,0]` |
| ALSA | capture overrun **0**、playback underrun **0**、ALSA error **0** |
| 削顶 | 输出削顶 **0** 样本（output_peak 0.356）；原始采集削顶 0 |
| 分析 | RTF **0.3937**，单块最大 **36.27 ms**（预算 200 ms/块） |
| 渲染 | RTF **0.3341**（含输出等待） |
| 链路 | submitted 1502 / consumed 1502，input_queue_peak 5、parameter_queue_peak 2、output_queue_peak 1 |
| 语音检测 | `voiced_frames=1201`（麦克风通路正常） |
| mixer 恢复 | exit 0，结束后 PCM0p/PCM1c 均 closed |

对照：同一二进制的 60 s 文件回放（2026-10-18，`ps_opt_realtime.md`）render RTF 0.3461；本轮真实 ALSA 满语音为 0.3341（同量级）。

## 4. 用户听感（原话）

> **“这一版不错，我认为可以先跑着 PL 加速了”**

记录于 `report/live_pspl_baseline_trial60_20261022.json` 的 `user_listening_feedback`。解释边界：这是对 A1/WORLD 实时链连续性和清晰度的肯定，**不代表音色门通过**——该链仍保留源音色，未与目标女声做对比试听。

## 5. 限制（下结论前必须看）

1. **端到端延迟未实测**：当前 prefill=200 ms + ALSA 缓冲（arecord buffer 4096 @32k ≈ 128 ms、aplay buffer 3072 ≈ 96 ms），预计 250–350 ms，未达 `plan.md` 的 p95 ≤100 ms 目标；本轮只测了“每 200 ms 块计算 <200 ms”的实时余量。
2. **连续运行只有 60 s**，未做 30 min 稳定性、冷启动和故障恢复。
3. **A1/WORLD 链保留源音色**，不是目标女声转换；音色门（身份/P10/泄漏/UTMOS/CER）本轮完全没有参与。
4. **输出增益不是音质结论**：0.75→0.60 只是为了避免削顶，未重新标定响度。
5. 操作者听感是实时单耳主观判断，不是盲听，也不是 A/B。

## 6. 复现

```sh
# 板端（串口 root shell）
cd /tmp/codex_world_20261013
python3 live_world_trial.py --check        # 预检：二进制 SHA、PCM 空闲、CPU 0-1
aplay -D default cue3.wav                  # 操作者听到提示音后立即连续说 60 s
python3 live_world_trial.py --run --seconds 60 --prefill-ms 200 \
    --output-gain-q16 39322 --input-gain-q16 262144 --require-voiced
```

运行时文件由 `build/generated/live_pspl_20261022/` 经 `board/upload_file.ps1` 上传（`world_budget_v23.gz` 解压后 chmod +x）。

## 7. 证据

- 原始串口记录：`report/live_pspl_trial60_20261022.log`（静音轮）、`report/live_pspl_trial60_speech_20261022.log`（削顶轮）、`report/live_pspl_trial60_speech3_20261022.log`（通过轮）
- 结构化结果：`report/live_pspl_baseline_trial60_20261022.json`
- 运行时来源：`build/generated/ps_opt_20261018/live_stream_opt_arm`、`report/ps_opt_realtime.md`
- 板端 run 目录：`/tmp/codex_world_20261013/live_3479352426337`（result.json、capture.log、playback.log、mixer_*）

## 8. 下一步

PS 基线已可接受，按用户指示进入 **PL 加速**。PL 合成卸载当前状态与下一步：

1. 增量 1（1024 点 IFFT 核）已完成；
2. 增量 2 步骤 B（FFT/IFFT 可切换核）已完成（`report/pl_fft1024_engine_20261022.md`）；
3. 待做：24 位 Q5.18 数据通路、`minphase_exp_unit` 修复、PS fold + OLA + 脉冲 IFFT 串联，然后 AXI-DMA 与板端 RTF 实测。
