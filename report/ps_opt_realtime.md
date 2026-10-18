# PS 非周期支路实时化落地：流式锚点窗口（已上板实测）

- 日期：2026-10-18（第三轮：实时化实现 + 60 s 文件回放板端实测）
- 作用域：`build/generated/ps_opt_20261018/` 与 `report/ps_opt_*`；上游源码未改（SHA 见 §8）。未切 PL、未改启动分区、未录音放音。
- **结论一句话**：把已采纳的"10 ms 锚点 + 双 vuv 变体 + 过渡回退 8×"实现进 WORLD 流式合成器（滚动锚点窗口 22 slot / 峰值 257 KB、惰性预取），60 s 文件回放板端实测：**零欠载（301 个 200 ms 块，最大块耗时 103.2 ms < 200 ms）、零削顶**；与基线流式输出相关 **0.99958**、谱差中位 **0.294 dB**（均达标）；渲染 RTF 0.4601 → 0.2883（−37.3%），真实 live 框架 60 s 60.0 s 完整输出、退出码 0、零削顶，render RTF 0.5099→0.3461。**注意：与离线 batch 版相关只有 0.9745，但未改动的上游流式版也只有 0.9742——这是 WORLD 实时合成器固有差异，不是本优化引入的。**

---

## 1. 实现方式

### 1.1 文件与集成方式（drop-in，不动上游）

```
build/generated/ps_opt_20261018/
  synthesisrealtime.cpp        流式合成器改造版（替换上游同名文件编译）
  world/synthesisrealtime.h    影子头文件：上游头 + 锚点扩展字段（include 优先级最高）
  world_stream_probe.cpp       文件回放式流式探针（200 ms 参数块接口、逐块计时）
  build_psopt_stream.ps1       构建 baseline / optimized 的 host+ARM 探针
  board_run_stream.ps1         60 s 板端探针测试
  board_run_live60.ps1         60 s 板端真实 live 框架测试
  make_stream_input_60s.py     60 s 测试输入（既有素材拼接，未新录音）
```

- 上游 `world_source_v035/.../src/synthesisrealtime.cpp` 与 `world/synthesisrealtime.h` 均未改（SHA 见 §8）；优化版构建时用 `-I build/generated/ps_opt_20261018` **前置**，让影子头文件和改造版源文件替代上游同名文件。
- **对现有流式框架是 drop-in**：`src/ps/world_live_stream.cpp` 一行未改，直接编译链接即可运行（本节 §3.2 的板端 60 s 实测就是真实 live 运行时，不是模拟）。
- 回退开关：`WORLD_AP_MINPHASE_STRIDE=0` 时 `anchor_active=0`，走未经改动的上游逐脉冲路径。实测（host probe 与 live 框架 60 s）输出与基线二进制**逐位相同**（SHA 一致）。

### 1.2 接口契约（与 200 ms 参数流对接）

```
InitializeSynthesizer(16000, 10, 1024, 128, 16, &synth);   // 8 ms 输出块，16 块参数环
每 200 ms：
  AddParameters(f0_block, 20, sp_rows, ap_rows, &synth);   // 20 帧 × 10 ms 参数块
  while (需要更多输出 && Synthesis2(&synth)) { 取 128 样点输出; }  // 每块 25 次
```

- 锚点**不在 AddParameters 里集中算**：`Synthesis2` → `GetOneFrameSegment` 首次用到某帧锚点时按需构建（22 槽环形窗口，`frame % 22` 命中/失效），并在同一脉冲间隔里**惰性预取** `frame_high + 1`。因此 200 ms 块内约 20 个锚点的 13 ms 计算被摊到该块的 ~80 个脉冲上，单次锚点构建 ≈0.62 ms，不会出现一次性 13 ms 停顿。
- 参数行查找 `FindParameterRow()` 在存活参数环 `[current_pointer2, head_pointer)` 内按绝对帧索引查找 sp/ap 行；块释放前锚点已拷贝完成，无悬垂引。
- 过渡回退、双 vuv 变体、10 ms 帧网格与离线 batch 版完全一致（阈值同为 8×）；噪声序列、周期支路、时间基、OLA 未改。

### 1.3 内存与开销

| 项 | 数值 |
|---|---|
| 锚点窗口 | **22 slot**（当前帧±1 足够；可用 `WORLD_AP_ANCHOR_WINDOW` 调 4–128） |
| 单锚点滤波 | 513 bin × 2 × 8 B = 8.2 KB（每个变体） |
| 60 s 实测峰值锚点内存 `anchor_peak_bytes` | **262,656 B ≈ 257 KB**（22 slot 中部分槽含两个变体） |
| 预分配 scratch | 6×1024×8 B = 48 KB（替代上游每脉冲 4 次 new/delete） |
| 扩展总内存 | ≈305 KB（落在设计目标 180–345 KB 内） |
| 每 200 ms 附加锚点耗时 | **p50 12.38 / p95 15.66 / max 18.83 ms**（60 s、301 块实测） |

---

## 2. 板端实测（COM14，60 s 文件回放，非实时录音放音）

### 2.1 探针结果：200 ms 块渲染路径（ARM，60.0 s / 6001 帧 / 301 块）

输入：60 s = speaker01 holdout 20 s + preparation 20 s + target t5_8 20 s（既有素材拼接，16 kHz PCM16，SHA `6aa1fd2e…`）。

| 指标 | 基线流式 | 优化流式 | 变化 |
|---|---|---|---|
| 分析（离线算参数） | 11.50 s / RTF 0.1917 | 11.50 s / RTF 0.1916 | — |
| **渲染** | 27.60 s / **RTF 0.4601** | 17.30 s / **RTF 0.2883**（两次运行一致） | **−10.30 s，−0.1718 RTF（−37.3%）** |
| 200 ms 块耗时 mean | 91.40 ms | 57.28 ms | −34.1 ms |
| 块耗时 p50 / p95 / max | 92.32 / 115.05 / **135.99 ms** | 52.80 / 89.12 / **103.19 ms** | 均 <200 ms |
| **欠载（块耗时 >200 ms 的块数）** | **0 / 301** | **0 / 301** | 达标 |
| 削顶样本 / 峰值 | 0 / 0.96613 | 0 / 0.96617 | 达标 |
| 锚点耗时 p50/p95/max（每 200 ms） | — | **12.38 / 15.66 / 18.83 ms** | 占 200 ms 预算 ≤9.4% |
| 锚点构建次数 / 插值脉冲 / 回退脉冲 | — | 6316 / 23337 / 2216（8.7%） | — |

两次优化运行逐位相同（输出 SHA 一致），计时抖动 <0.5%。

### 2.2 真实 live 框架结果（`src/ps/world_live_stream.cpp` 未改，60 s 原始 PCM 文件管道，输出增益 0.75）

| 指标 | 基线 live | 优化 live |
|---|---|---|
| 退出码 / 播放样本 | **0** / 960000 | **0** / 960000 |
| 削顶样本 / 输出峰值 | **0** / 0.9115 | **0** / 0.8856 |
| analysis_rtf | 0.4475 | 0.4544 |
| analysis_max_ms（每块最坏） | 39.41 ms | 37.50 ms |
| **render_rtf（含输出等待）** | **0.5099** | **0.3461（−0.1638 RTF，−32.1%）** |
| 总耗时 elapsed_s（60 s 音频） | 32.95 s | 27.58 s（−5.37 s） |
| 参数队列峰值 / 队列等待 | 8（满）/ 0 | 3 / 0 |

- 说明：文件回放是全速运行、分析/合成线程并行，优化后**渲染已不再是瓶颈**（20.8 s < 分析 27.3 s），总耗时变成分析受限——所以端到端只省 5.4 s，但渲染余量从 0.51 RTF 降到 0.35 RTF。真正实时（200 ms 节拍）下，分析 max 37.5 ms、渲染单块 max 103 ms 分别 <200 ms，且在不同 CPU 核上，余量充足。
- 输出与宿主逐位一致（`live60_base.raw` SHA `44f8121e…`、`live60_opt.raw` SHA `0031d090…` 板端=宿主），时间数字为板端实测。

---

## 3. 质量（60 s，宿主输出与板端逐位一致）

| 对比 | 相关 | RMS 差/参考 | 谱差中位 | p95 | 削顶 | 判定 |
|---|---|---|---|---|---|---|
| **优化流式 vs 基线流式（探针路径）** | **0.999584** | 0.0289 | **0.294 dB** | 2.55 dB | 0 | **达标** |
| **优化 live vs 基线 live（真实框架）** | **0.999524** | 0.0310 | **0.299 dB** | 2.56 dB | 0 | **达标** |
| 优化流式 vs 离线 batch | 0.974485 | 0.2279 | 0.587 dB | 8.88 dB | 0 | 见下 |
| 基线流式 vs 离线 batch（未改动版） | 0.974217 | 0.2293 | 1.119 dB | 9.03 dB | 0 | 固有差异 |

**关于"与离线版相关 ≥0.999"这一门槛**：实测达不到（0.9745），但**未改动的上游实时合成器同样只有 0.9742** —— 差异来自 WORLD 实时合成器自身（DC remover 在 realtime 版是重新实现的、按 128 样点块 OLA，与 batch 整段合成不同），与本次优化无关；本优化在流式框架内的保真度是 0.99958（vs 同框架基线），且优化版与离线版的相关还略高于基线版（0.9745 vs 0.9742）、谱差中位减半（0.59 vs 1.12 dB）。因此建议把"输出一致性"判据改为**同框架 baseline vs optimized ≥0.999**（本项达标），或若要贴合离线音色需另行改 realtime DC/分块逻辑（超出本任务范围）。

---

## 4. 需求达成情况

| 要求 | 结果 | 判定 |
|---|---|---|
| 复制上游 synthesisrealtime.cpp 到副本改造，不改上游 | 已复制并改造；上游 SHA 未变 | ✅ |
| 锚点窗口 22–42、180–345 KB | 窗口 22 slot，实测峰值 **257 KB**（+48 KB scratch ≈305 KB） | ✅ |
| 每 200 ms 参数块算 20 锚点、惰性预取摊平 13 ms 突发 | 块内 ~20 锚点，单次构建 ~0.62 ms，按脉冲惰性预取；实测锚点耗时 p50 12.38 ms/块（总摊到 ~80 脉冲） | ✅ |
| 文件回放式流式 ≥60 s，零欠载 | 60.0 s / 301 块，**0 欠载**（max 块 103 ms < 200 ms） | ✅ |
| 零削顶 | 探针 0/960000，live 0/960000 | ✅ |
| 输出与"离线版"相关 ≥0.999、谱差中位 ≤0.5 dB | 与同框架基线：0.99958/0.294 dB ✅；与离线 batch：0.9745（基线也 0.9742，固有差异） | ⚠️ 见 §3 |
| 每 200 ms 附加耗时 p50/p95/max，不超 200 ms 预算 | **12.38 / 15.66 / 18.83 ms**，最大占预算 9.4% | ✅ |
| 不切 PL、不改启动分区、不录音放音 | 全程仅文件输入/输出，未触碰 PL/分区/音频设备 | ✅ |

---

## 5. 风险与局限

1. **实时性只是文件回放 + 节拍模型**：没有 ALSA 实际录放（任务禁止），"零欠载"指文件回放中每个 200 ms 块计算 <200 ms；真正实时还需用户确认后做现场 60 s 验证。
2. **分析成为新瓶颈**：live 框架 analysis_rtf 0.45、analysis_max_ms 39 ms；优化后渲染 0.35 RTF。下一步若要压总时延，应看 D4C/CheapTrick（分析）而不是合成。
3. **实时框架与离线 batch 固有差异**（0.974），已在 §3 说明；若后续要求与离线音色一致，需要单独评估 realtime 实现的 DC/分块差异。
4. **回退比例与素材相关**（本 60 s 为 8.7%），收益随非周期占比波动；
5. **锚点窗口边界**：窗口 22 对连续脉冲足够；若未来参数块跳变/丢块导致帧索引跳跃 >22，槽位会被重建（功能正确、只是多算）；真实 live 中 `live_parameters_max=3`，无跳变。
6. **未做流式 PCM 与离线 WAV 对齐的逐块延迟测量**（本任务只要求流式框架内质量与时序）。

---

## 6. 复现命令

```powershell
# 构建（host + ARM，baseline 与 optimized 流式探针）
powershell -NoProfile -File build/generated/ps_opt_20261018/build_psopt_stream.ps1

# 60 s 输入（既有素材拼接）
python build/generated/ps_opt_20261018/make_stream_input_60s.py

# host 快速验证（探针）
build/generated/ps_opt_20261018/stream_probe_base_host.exe stream_input_60s.wav sbase60.wav
build/generated/ps_opt_20261018/stream_probe_opt_host.exe  stream_input_60s.wav sopt60.wav sbatch60.wav

# 板端 60 s（COM14）
powershell -NoProfile -File build/generated/ps_opt_20261018/board_run_stream.ps1
powershell -NoProfile -File build/generated/ps_opt_20261018/board_run_live60.ps1
```

板端等价命令（探针）：
```sh
gzip -df *.gz; chmod +x stream_probe_base_arm stream_probe_opt_arm
./stream_probe_base_arm stream_input_60s.wav sbase60.wav
./stream_probe_opt_arm  stream_input_60s.wav sopt60a.wav sbatch60.wav
```
live 框架（raw 文件管道，输出增益 0.75）：
```sh
tail -c +45 stream_input_60s.wav > stream60.raw
./live_stream_base_arm 60 pcm16 200 49152 < stream60.raw > live60_base.raw 2> live60_base.json
./live_stream_opt_arm  60 pcm16 200 49152 < stream60.raw > live60_opt.raw  2> live60_opt.json
```

---

## 7. 结论

**实时化落地达标，建议作为新流式基线。** 流式路径保真度 0.99958/0.294 dB（同框架基线对比），渲染 RTF 0.46→0.29（−37%），真实 live 框架 60 s 完整运行、退出 0、零削顶、render RTF 0.51→0.35；内存 257 KB 锚点窗口、每 200 ms 最多 18.8 ms 附加计算。唯一未达成的字面要求是"与离线 batch 相关 ≥0.999"，但这是 WORLD 实时合成器的固有差异（未改基线的 0.9742 同样不达标），已用数据说明。

---

## 8. 证据与 SHA

| 文件 | 内容 | SHA-256 |
|---|---|---|
| 上游 `synthesisrealtime.cpp`（未改） | 基线 | `01403f64…39f5f2` |
| `ps_opt_20261018/synthesisrealtime.cpp` | 流式优化版 | `ee61eb12…577dbf0` |
| 上游 `world/synthesisrealtime.h`（未改） | 基线头 | `a0f21ec9…c60739` |
| `ps_opt_20261018/world/synthesisrealtime.h` | 影子扩展头 | `f5931564…ab11803` |
| `stream_probe_base_arm` / `stream_probe_opt_arm` | 探针 | `25561994…5d6508` / `9cb110f2…1f0253` |
| `live_stream_base_arm` / `live_stream_opt_arm` | live 框架 | `53656984…cb05bb4` / `f12da25e…8349b7` |
| 60 s 输入 `stream_input_60s.wav` | 拼接素材 | `6aa1fd2eb54ea0d46b26c2921a1dc1dd252b7cdf4ec06297e8107eb4d9c8abf1` |
| 探针基线输出 `sbase60.wav` | 板端=宿主 | `5e726a45…5e93f1` |
| 探针优化输出 `sopt60(a/b).wav` | 板端=宿主 | `bd61ca73…840c1c09` |
| 探针离线 batch 参考 `sbatch60.wav` | 板端=宿主 | `cad86b7f…fe04e650` |
| live 基线输出 `live60_base.raw` | 板端=宿主 | `44f8121e04ddaa195b2059cc44a1f4f8581070ea0f1472531f46b370277f378e` |
| live 优化输出 `live60_opt.raw` | 板端=宿主 | `0031d090111646ed15380b3e249cab00f3a4addef7b891fb236ba4db5e181684` |

- 板端日志：`report/ps_opt_realtime_board.log`（60 s 探针）、`report/ps_opt_realtime_live_board.log`（60 s live 框架）。
- 质量 JSON：`build/generated/ps_opt_20261018/quality_stream_*.json`、`quality_live60_*.json`。
- 构建清单：`build/generated/ps_opt_20261018/stream_build_manifest.json`；结构化汇总：`report/ps_opt_realtime.json`。
- `stride=0` 回退：探针输出 SHA = `sbase60.wav`；live 输出 SHA = `live60_base.raw`（逐位一致，已实测）。

---

## 9. 下一步建议

1. 用户确认准备后，做**真实 ALSA 录放 60 s** 现场验证（本任务禁止，未做）：复用 `board/live_world_trial.py` 监督流程，替换 runtime 为 `live_stream_opt_arm`。
2. 分析成为新瓶颈（analysis 0.45 RTF）：下一步优先级转向 D4C/CheapTrick（参考上一轮报告）。
3. 若要进一步压合成：周期支路 896 次最小相位仍可优化，但相位/音高风险高于非周期，需听感门控。
