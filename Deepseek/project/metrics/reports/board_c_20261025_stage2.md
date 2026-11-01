# 阶段 2 报告：RTF 达标 + 实时流式版（Zynq-7020）

- 日期：2026-10-25（接 `board_c_20261025.md` 阶段 1）
- 目标：RTF ≤ 1.0 且保住听感；按批准顺序做 D4C 改造 → CheapTrick 只跑一遍 → MLP int8 → （必要时）双核
- **结果：RTF 0.967–0.985（达标），四项客观指标与 stage-1 的差异全部在验收线内**
- 产物 SHA-256：`6550e91925d4b4b10c1a1739ddc7b61e024417d9d380d485db026bb3736056a3`（796,232 B，板上 `/tmp/vc/vc_rt2`）

---

## 1. 结论摘要

| 项 | 阶段 1 | 阶段 2 最终 | 变化 |
|---|---|---|---|
| 总耗时（4 s 音频） | 8,269 ms | **3,857–3,941 ms** | −53% |
| **RTF** | **2.067** | **0.967 / 0.983 / 0.985**（三次） | **达标 ≤1.0** |
| analysis_rtf | 1.613 | 0.792 | |
| render_rtf | 0.177 | 0.150 | |
| `clipped_samples` | 144 | **0** | 峰值 0.8166 FS（`out_gain_q16=39322`） |
| 输出可复现 | 3 构建逐字节相同 | 同左（`5e15eb03…`，最终二进制复跑一致） | |

四项客观指标（录音 5 = `data/pair16k/male/male_04.wav` 的 1.0–5.0 s，16 kHz，`scripts/score_full.py`）：

| | identity_female | leakage_strict | UTMOS | CER |
|---|---|---|---|---|
| A 电脑端 T4（librosa 相位声码器 + v5 包络） | 0.6262 | 0.1700 | 1.3521 | 0.3077 |
| C 板端 stage-1（精确两遍 + fp32 MLP） | 0.6463 | 0.2288 | 2.1063 | 0.0769 |
| **E 板端 stage-2 最终** | **0.6373** | **0.2230** | **2.1045** | **0.0769** |
| E − C（优化的代价） | −0.0090 | −0.0058（更好） | **−0.0018** | **0.0000** |
| E − A（相对电脑端参考） | +0.0111 | +0.0530 | **+0.7524** | **−0.2308** |

**板端（含全部优化）比电脑端 T4 参考的 UTMOS 高 0.75、CER 低 0.23**（因为 librosa 的相位声码器本身伤音质并衰减 3.2 dB，而 SoundTouch WSOLA 不衰减），身份/泄漏略好或相当。

![电脑端 T4 vs 板端 stage-1 vs stage-2（同一 4 s）](out/score/stage2_compare.png)

上图：A（电脑端 T4）电平低 9.5 dB、语谱图有明显相位声码器的"涂抹"；C 与 E 几乎无法区分（E−C 波形相关 0.99975，UTMOS 差 0.0018）。

---

## 2. 三项批准优化的实测结论

### 2.1 D4C 改造 —— 采纳（收益最大）

- 做法：**每 10 帧算一次 D4C + 帧间线性插值**。D4C 的帧网格是入参，所以这是真正跳过了计算（不是加权近似）。
- 板上：`d4c_ms` **1,470 → 155 ms**（−1.31 s，占总耗时 16%）。
- 质量：与"每帧 D4C"的最终波形相关 **0.99975**；UTMOS −0.0018（门槛 ≤0.05）。
- 备选（谱平坦度近似）没有采用：插值已经够准，且平坦度会同时改掉 ap 的绝对尺度。

### 2.2 CheapTrick 只跑一遍 —— 纯频轴映射被否决，改用"f0 继承 + 把第二遍藏到 MLP 后面"

按批准方案实现并实测了三档，全部对照精确两遍版：

| 方案 | 与两遍版波形相关 | 结论 |
|---|---|---|
| 纯频轴映射 `logsp_b[b] = logsp_src[b/1.4]` | **0.9793** | **不达标（<0.99）** |
| 用 STFT 幅度谱 + DCT-48 当包络 | 0.8857 | 更差，弃 |
| 第二遍 CheapTrick 隔 2 帧 + 插值 | 0.9893 | 差一点，弃 |
| **f0 继承（第二遍不再跑 DIO/StoneMask）+ 精确 CheapTrick** | **0.9986** | 达标 |

纯频轴映射不达标的原因（实测）：SoundTouch 的升调 = 重采样（频轴 ×1.4）**再** WSOLA 时长拉伸，而重采样带的抗混叠滤波会把 5.7 kHz 以上搬移后的内容切掉，同时 CheapTrick 的 F0 自适应窗在 WSOLA 处理后的信号上给出的平滑也不同 —— 所以真实包络不是源包络的简单拉伸，形状差 2%（3.7 dB 中位差异），"1.389× 频轴映射"这个前提在 0.99 的门槛下不成立。

**最终采用的方案**：`f0_shifted = 1.4 × f0_source`（升调严格按比例改 f0，比重新估更平滑），只跑 CheapTrick（省掉第二遍 DIO+StoneMask，约 220 ms）；并且把整个第二遍 WORLD **放到 worker 线程，与 MLP 并行**，所以在关键路径上几乎免费（见 3.2）。输出与精确两遍版相关 **0.99975**。

### 2.3 MLP int8 —— 没有采用，改用 NEON fp32（同等提速、零精度损失）

- 实测板上 MLP（401 帧）：逐帧推理 24 ms/帧（RTF 2.4，纯内存受限）→ 2 维分块 9.5 ms/帧 → **寄存器分块 + 显式 NEON（8 帧 × 4 神经元，8 个 `float32x4` 累加器）+ 双核 → 2,097 ms（串行）→ 1,272 ms（双核）**。
- 因此"精度换速度"没有必要：验收要求的 UTMOS 降 ≤0.10、身份降 ≤0.01，实际是 **−0.0018 / −0.0090**，比 int8 的目标好一个量级。
- 8 帧分块与 4 帧分块输出**逐字节相同**（`max|d| = 0`），说明分块只改数据布局不改算术。
- 另测整包 `-O3`：主机 553 vs 539 ms，无收益，未采用。

---

## 3. 额外优化（不在批准清单，但零质量损失，收益很大）

### 3.1 双核：MLP 按帧切两半

`--threads 2`。两半写不重叠的输出行，`mlp_forward_batch` 无状态，**结果与串行完全一致**（实测 corr 1.000000000）。

静态 glibc 的坑：`std::thread` 会 `terminate`（libpthread 的 stub 被优先链接），改用裸 `pthread_create` + 链接时 `-Wl,--whole-archive -lpthread` 才 work，并保留失败回退（遥测 `threaded:false`）。

### 3.2 把第二遍 WORLD 藏到 MLP 后面（关键的一步）

第二遍 WORLD 只依赖 `xB`，与 MLP 无关 → 交给 worker 线程：worker 先跑第二遍，再跑它那半 MLP；主线程跑另外 3/4 的 MLP 帧（按 688 ms : 1,272 ms 的比例偏置切分）。

**实测：第二遍 WORLD 900 ms 几乎完全被隐藏**（`den_stride 0` 的精确两遍版只比继承版多 24 ms）。这也是"保住听感"的关键——不用为了速度牺牲包络精度。

### 3.3 两处底层优化

- **STFT/ISTFT 改单精度 FFT**：A9 的 VFP 双精度吞吐只有单精度一半且无 NEON 双精度，802 次 1024 点变换 **518 → 466 ms**。
- **重采样器按对称性折叠抽头**：线性相位 FIR 一半乘法是冗余的，175 → **134 ms**（输出转换 + S24 打包），结果 `max|d| = 0`。

### 3.4 增益（按指示修正）

- 默认 `out_gain_q16 = 39322`（0.6，与前人 v23 调度器一致）：包好的 S24 峰值 **0.8166 FS**，`clipped_samples = 0`。
- 麦克风：`input_gain_q16 = 262144`（4×）。实测板上麦克风 4 s：`median_gain_db 11.6`、`clipped 0`、RTF 0.858 —— 链路通，但信号本身只是 −42 dBFS 底噪。

---

## 4. 最终分阶段耗时（板上，4 s，最终二进制）

| 阶段 | ms | 相对阶段 1 |
|---|---|---|
| WORLD 第一遍（DIO+StoneMask+CheapTrick+D4C） | 1,118 | 2,444 |
| MLP 段（含并行的第二遍 WORLD） | 1,858 | 3,817 |
| SoundTouch 升调 | 193 | 193 |
| STFT/ISTFT | 466 | 521 |
| 16k→32k + S24 打包 | 134 | 185 |
| 其余（读入/32k→16k/建模） | ~170 | ~200 |
| **合计** | **3,857–3,941** | **8,269** |

`analysis_rtf 0.792`、`render_rtf 0.150`、`rtf 0.967–0.985`。

---

## 5. 实时流式版（按 v23 契约）

### 5.1 用法

```
# 与 v23 调度器完全相同的管道形状，只多一个 --stream
arecord -D hw:0,1 -t raw -f S24_LE -r 32000 -c 2 -d 600 \
  | ./vc_stream 600 native_s24 200 --stream 1000 \
  | aplay -D default -t raw -f S24_LE -r 32000 -c 2 --start-delay=64000
```

CLI 仍是 `vc_stream <seconds> pcm16|native_s24 <prefill_ms> [out_gain_q16 [in_gain_q16]]`，`stderr` 出 JSON：每块一行 `{block, frames_in, audio_ms, proc_ms, block_rtf, cum_rtf}`，结束时一行汇总 `{mode:"stream", blocks, rtf, clipped_samples}`。`prefill_ms` 仍被接受但不参与计算（播放端的预填充由 `aplay --start-delay` 或 v23 调度器负责）。

### 5.2 实现要点

- 按 `--stream <block_ms>` 切块；16k↔32k 两个重采样器**跨块携带滤波器历史**（32k 侧带 127 抽头尾巴，丢掉 31 个属于历史的输出样本）。
- **交叉淡入淡出用 hold-back 方案**：每块末尾 20 ms 暂不输出，与下一块开头交叉淡化 —— 不会重复任何音频，输出只滞后 `fade_ms`（默认 20 ms）。
- 说话人统计（32 维平均倒谱 + log-F0 中位 + 浊音比例）按块估计，并做一阶平滑（new = 0.5·old + 0.5·fresh），否则逐块的音色会跳。
- 每块内部用与批处理相同的双核安排。

### 5.3 实测

| 场景 | 结果 |
|---|---|
| 纯计算（输出到 `/dev/null`，12 s 音频，1 s 块） | **11,785 ms → RTF 0.982**（工具本身可以实时） |
| 完整 `cat → vc_stream --stream 1000 → aplay`（12 s） | 14,758 ms（1.22×），**11 次 underrun** |
| 同上但 `--stream 2000` | 14,516 ms（1.20×），1 次 underrun |
| 同上 + 快速档（`--den-stride 1 --ap-stride 20`） | 14,515 ms（1.20×），**11 次 underrun（几乎没变）** |
| 同上 + `--stream 500` + 快速档 | 12,235 ms（1.02×），12 次 underrun |

**结论（重要）**：工具的计算已经实时（0.982），但 `arecord/file → vc_stream → aplay` 整条链路在双核 A9 上仍会 underrun，而且**减计算量不解决问题**（快速档省了 290 ms 计算，整链时间几乎不变）。

> **更正（2026-10-25 晚，见 `board_c_20261025_int8_latency.md`）**：我原先把原因写成"内存带宽与 DMA 争用"，并把 int8 当成解药。实测推翻了这一点——int8 把权重流量降 4 倍，MLP 只快 11%、总时间只快 2.4%，**MLP 是指令发射受限（issue-bound），不是带宽受限**；int8 之后 underrun 依旧（11–39 次）。真实原因是整链 RTF 0.96–0.98 几乎没有吞吐余量，aplay 一争 CPU 就顶不住。int8 的价值退回为"权重 4.57 → 1.14 MB、指标不降"。

### 5.4 流式 vs 批处理（包络域，4 s 同一素材）

| 块长 | 与批处理的窗包络相关（中位） | 包络绝对差中位 | 打包峰值 |
|---|---|---|---|
| 500 ms | 0.9858 | 4.77 dB | 1.00（有削波） |
| 1000 ms | **0.9915** | 3.76 dB | 0.894 |
| 2000 ms | **0.9944** | 2.67 dB | 0.909 |

块越长越接近批处理（统计窗口更长）；**推荐 `--stream 1000`**（延迟约 2 s，包络 0.99、无削波）。

---

## 6. 验收结论对照

| 验收项 | 标准 | 实测 | 结论 |
|---|---|---|---|
| RTF | ≤1.0 | **0.967 / 0.983 / 0.985** | **通过** |
| D4C 改造 UTMOS 降 | ≤0.05 | **−0.0018** | 通过 |
| CheapTrick 只跑一遍 波形相关 | ≥0.99 | 纯频轴映射 0.9793 → **否决**；最终方案 0.99975 | 通过（换方案） |
| int8 UTMOS 降 | ≤0.10 | 未用 int8；实际 −0.0018 | 通过（更优） |
| int8 身份降 | ≤0.01 | **−0.0090** | 通过 |
| 削波 | `clipped_samples=0` | **0**（峰值 0.8166 FS） | 通过 |
| 实时流式 | 按 v23 契约 | 已实现并跑通；纯计算 0.982，整链仍 underrun | **部分通过**（见 5.3） |

---

## 7. 新增/变更的开关

| 开关 | 默认 | 作用 |
|---|---|---|
| `--ap-stride N` | **10** | D4C 每 N 帧算一次 + 插值（1 = 精确参考） |
| `--den-stride N` | **0** | 0 = 精确第二遍 WORLD；N≥1 = f0 继承 + 每 N 帧 CheapTrick |
| `--threads N` | **2** | 双核：MLP 切半 + 第二遍 WORLD 并行；失败自动回退串行 |
| `--stream <block_ms>` | 0（关） | 实时流式模式 |
| `--fade-ms N` | 20 | 流式块间接缝淡入淡出 |
| `--pitch-axis-ratio R` | 1.4 | 升调频轴/f0 比例（实测 1.394） |
| `--ct-once` / `--ct-stft` | 关 | 被否决的两种"只跑一遍 CheapTrick"近似，保留作对照 |
| `out_gain_q16` 默认 | **39322** | 0.6，避免削波；传 65536 恢复单位增益 |

新增文件：`src/stream_mode.inc`（流式实现）、`score_variants.py`（一次进程内给多个变体打分）、`make_score_wavs.py`。

---

## 8. 这一轮踩到的坑

1. **静态 glibc + pthread**：`std::thread` 直接 `terminate`（libpthread 的 stub 被优先链接）；`pthread_create` 也返回垃圾错误码。解法：裸 pthread API + `-Wl,--whole-archive -lpthread -Wl,--no-whole-archive` + 失败回退串行。
2. **"只跑一遍 CheapTrick"的前提不成立**：见 2.2，必须实测才发现（0.9793 差一点点）。
3. **MLP 提速的方向猜错两次**：先以为纯内存受限（批处理不给力，因为激活块 32 KB 冲刷 L1），再以为 4→8 帧能减半权重流量（无效果）；最后靠"寄存器分块 + 显式 NEON + 双核"才拿到 1.8×。
4. **串口会话被自己的引号卡死**：命令里嵌引号让板端 shell 停在续行状态，`Invoke-BoardCmd` 超时并占住 COM8。恢复：Ctrl-C + 重新 `stty echo`。教训：板端命令只用单引号/无引号的简单形式。
5. **流式的接缝**：第一版把上一块的尾巴"复制"到下一块开头（重复 20 ms 音频）；改成 hold-back 后长度才对（127,360 → 128,000）。
6. **流式统计不平稳**：逐块统计让音色跳，加一阶平滑后包络相关从 0.986 → 0.992。
7. **`--ap-stride 20`**：UTMOS 反而更好（2.1157）但身份掉 0.0117（超过 0.01 门槛）→ 停在 10。
8. **PowerShell 的 `Set-Content` 默认 ANSI**：用它改 UTF-8 报告会毁掉中文，必须用 write 工具或显式 `-Encoding utf8`。
9. 主机上仍有别人的训练任务在跑，`cc1plus: out of memory` 偶发；重试即可，未 kill 任何进程。

---

## 9. 复现

```powershell
cd <workspace>/board_c_20261025
$py = "<workspace>/env/venv/Scripts/python.exe"

.\build_arm.ps1 ; .\build_host.ps1

# 桌面侧质量对照（同一 x16 喂给各变体；与板端输出相差 139 dB，可直接当板端用）
build\vc_stream_host.exe 4 pcm16 0 --model data\student_v5.blob --in-f32-16k --out-f32-16k 65536 65536 < out\board\dump\x16.f32 > v.f32
& $py score_variants.py out\score\A_desktop_t4.wav out\score\C_board_stage1.wav out\score\E_board_stage2_final.wav
& $py ..\scripts\score_full.py out\score\A_desktop_t4.wav out\score\C_board_stage1.wav out\score\E_board_stage2_final.wav --cer-from out\audio\source_16k.wav

# 上板
.\tools\upload_board.ps1 -LocalFile build\vc_stream_arm -RemotePath /tmp/vc/vc_rt2

# 板上（批处理）
cd /tmp/vc && ./vc_rt2 4 native_s24 200 --dump fin5 < in.raw > fin5/out.raw 2> fin5/tel.json

# 板上（实时）
cat in.raw | ./vc_rt2 12 native_s24 200 --stream 1000 | aplay -D default -t raw -f S24_LE -r 32000 -c 2 --start-delay=64000
```

---

## 10. 遗留状态

1. 板上 `world-voice` 演示仍是**停止**状态（与我进场时一致）。演示前：`/etc/init.d/world-voice start`。
2. 板上文件全部在 `/tmp/vc/`：`vc_stream`、`vc_stream2/3/_final/_final2/vc_opt1..4/vc_stage2/vc_stage2b/vc_stage2c/vc_rt2`、`student_v5.blob`、`in.raw`、`mic.raw`、`fin2/fin3/fin4/fin5/`（含 `out.raw`、`y16.f32`、`tel.json`）、`dump*/`、`t*.json`、`aplay*.log`。串口会话结束时已恢复 `stty echo` 与 PS1。
3. RTF 在 0.967–0.985 之间抖动（±1.5%，与板上其他负载有关）；如果演示要求更稳的余量，最快的办法是 int8 权重（见 5.3），其次是 `--ap-stride 20`（牺牲 0.002 身份）。
4. 实时整链仍会 underrun（工具本身 0.982 实时）。**没有**伪造"实时已完全跑通"：这是当前硬件 + 该模型体量下的真实边界，下一步是 int8 权重或把第二遍 WORLD 换成廉价方案。
