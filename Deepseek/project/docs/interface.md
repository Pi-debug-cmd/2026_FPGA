# 接口契约：AXI-Stream / AXI-Lite 寄存器 / CLI

> **状态（2026-10-27）**：当前入链的 PL 是 **STFT 版**（`axis_stft_gain` + 2×xfft，
> 帧格式见 `fpga/stft/README.md` §1/§2：每帧 1537 words 输入、1024 words 输出，
> 状态寄存器 `0x41200000` 读帧计数）。本文件 §1/§3 描述的是**备用变调核**
> `axis_pitch_shift`（与 STFT 版互斥、不能同时加载），保留作为已验证设计的接口记录。

三份契约：**PL 的流接口**、**PL 的控制接口**、**PS 程序的命令行与遥测**。
任何一方改动都必须同时更新本文件——这是"可复现"的前提。

---

## 1. AXI-Stream：`axis_pitch_shift`

### 1.1 端口

| 端口 | 方向 | 位宽 | 说明 |
|---|---|---|---|
| `aclk` | in | 1 | 100 MHz（PS7 `FCLK_CLK0`） |
| `aresetn` | in | 1 | 低有效；复位后进入 CLEAR（清 2048 深 RAM，约 2048 拍 ≈ 20.5 µs） |
| `ratio_q16` | in | 18 | 变调比例，Q16；**有效范围 32768–131072** |
| `s_axis_tdata` | in | 32 | PCM16 放在 **bit[15:0]**，高位忽略 |
| `s_axis_tkeep` | in | 4 | 原样保存，随输出返回 |
| `s_axis_tlast` | in | 1 | 原样保存，随输出返回 |
| `s_axis_tvalid/tready` | — | 1 | `tready = aresetn && state==IDLE && valid_ratio` |
| `m_axis_tdata` | out | 32 | PCM16 **符号扩展到 32 位**（`{{16{s[15]}}, s}`） |
| `m_axis_tkeep/tlast` | out | 4/1 | 与最近一次被接收的输入字一致 |
| `m_axis_tvalid/tready` | — | 1 | 每接收 1 个字，约 12 拍后产出 1 个字 |

### 1.2 时序与语义

- **每样本 1 进 1 出**：不改变样本数（变调通过重采样相位实现，不做时长伸缩）。
- **延迟**：从 `tvalid&&tready` 到对应 `m_axis_tvalid` 固定 **12 个 aclk**（状态机走
  READ_A0→…→OUTPUT_WORD），即 120 ns @100 MHz。跨 125 个 DMA 块不累积（RAM 保留 2048 样本历史）。
- **背压**：`m_axis_tready=0` 时核停在该状态，`s_axis_tready` 自动为 0，不会丢字。
- **`ratio_q16 == 65536`**：走旁路分支，输出 = 输入（**输出 SHA 必须等于输入 SHA**，这是恒等测试）。
- **`ratio_q16` 越界**：`valid_ratio=0` → `s_axis_tready` 恒 0，流被挂起（不会出错数据）。

### 1.3 定点语义（与 Python 参考模型逐位一致）

```
phase   : 26-bit 累加器，phase += (65536 - ratio_q16) & 0x3FFFFFF
other   : phase ^ 0x2000000            (半窗偏移)
address : wptr - 2 - (phase >> 16)     (2048 深环形 RAM)
frac    : phase & 0xFFFF
tap     : (buf[a]·(65536-frac) + buf[a-1]·frac) >> 16
weight  : phase[25] ? 131072-{1'b0,phase[25:9]} : {2'b0,phase[24:9]}
out     : (tap0·weight + tap1·(65536-weight)) >> 16      (算术右移 = 向下取整)
```

与 `fpga/src/compare_reference.py` 的 `pitch_shift()` 完全同构；
**板端实测 128000 个样本 `max_abs_diff = 0`**（三个比例：86856 / 48000 / 65536）。

---

## 2. AXI-Lite：寄存器映射

### 2.1 地址总览（本设计）

| 基地址 | 范围 | 模块 | 说明 |
|---|---|---|---|
| `0x40400000` | 64 KB | AXI DMA | simple mode，MM2S/S2MM 各一通道 |
| `0x41200000` | 64 KB | **AXI GPIO（双通道）** | ch1 = `ratio_q16`，ch2 = scratch |
| `0x41600000` | — | AXI I2C | 音频 codec 控制 |
| `0x43C00000` 起 | — | audio_formatter / i2s_rx / i2s_tx / axi_dynclk | 音频与显示 |
| `0x43C40000` | — | audio_formatter | ALSA 声卡 |
| `0x43C50000` / `0x43C60000` | — | i2s_receiver / i2s_transmitter | 采集 / 播放 |

### 2.2 AXI GPIO `0x41200000`（本项目唯一新增的控制寄存器）

| 偏移 | 名称 | 位宽 | 复位值 | 访问 | 说明 |
|---|---|---|---|---|---|
| `0x00` | `ratio_q16` | 18 | **86856**（`C_DOUT_DEFAULT=0x15348`） | R/W | 变调比例 Q16。65536=恒等，86856=1.3253×，131072=2× |
| `0x04` | 保留 | — | — | — | AXI GPIO 的 tri-state 寄存器 |
| `0x08` | `dsp_run` | 1 | 1（`C_DOUT_DEFAULT_2=0x1`） | R/W | **本构建里只是可读写 scratch，未接 `aresetn`**（见 `fpga/report/build_changes_2018_3.md`） |
| `0x0C` | 保留 | — | — | — | — |

**已验证**（板上，2026-10-25）：初值 86856 精确读出；写 86856/65536/131072/32768/86856 五组全部精确回读；
ch2 写 0 读 0、写 1 读 1。原始输出见 `skill/overlay_load_and_verify/results.md` §3。

> ⚠️ 因为 ch2 未接 `aresetn`，`CONFIGURE` 式的"先复位再配置"**不会**清空核内 RAM/相位。
> 要做"从零状态"的数值比对，必须**重新加载位流**（CLEAR 状态会把 2048 深 RAM 清零）。

### 2.3 AXI DMA `0x40400000`（用到的最小集）

| 偏移 | 名称 | 说明 |
|---|---|---|
| `0x00` | MM2S_DMACR | bit0=RS（run/stop），bit2=Reset |
| `0x04` | MM2S_DMASR | bit0=Halted，bit1=Idle，bit4-6=错误位（写 1 清除） |
| `0x18` | MM2S_SA | 源物理地址（32-bit） |
| `0x28` | MM2S_LENGTH | 传输字节数（写即启动） |
| `0x30` | S2MM_DMACR | 同上 |
| `0x34` | S2MM_DMASR | 同上 |
| `0x48` | S2MM_DA | 目的物理地址 |
| `0x58` | S2MM_LENGTH | 传输字节数（写即武装） |

**顺序**：先 `S2MM_DA`/`S2MM_LENGTH`（武装接收），再 `MM2S_SA`/`MM2S_LENGTH`（启动发送），
轮询两个 `SR.Idle` 同时为 1。每块 **1024 × 32-bit = 4 KiB**，实测 117.7–118.6 µs。

---

## 3. CLI 契约（`vc_stream`）

### 3.1 用法

```
vc_stream <seconds> <pcm16|native_s24> <prefill_ms> [out_gain_q16 [in_gain_q16]] [flags...]
vc_stream --model <blob> <上面的位置参数...>
```

- 位置参数**必须**沿用前代 v23 调度器的形状（调度器不改一行即可替换 `binary_name`）。
- `prefill_ms` 被接受但**不参与计算**（播放端预填充由 `aplay --start-delay` 负责）。
- 第 5/6 个位置参数是 Q16 增益：默认 `out=39322`（0.6）、`in=65536`（1.0）。
- 第 7 个位置参数（v23 的 `normal|fifo|fifo_io`）接受但忽略。

### 3.2 开关

| 开关 | 默认 | 作用 |
|---|---|---|
| `--model PATH` | `student_v5.blob` 或 `$VC_MODEL` | 权重 blob |
| `--stream MS` | 0（批处理） | 流式块长（ms） |
| `--fade-ms MS` | 20 | 块间交叉淡化（hold-back，不重复音频） |
| `--preset live\|safe\|off` | — | live = ct2+sm2+int8；safe = sm2；off = 精确 |
| `--ap-stride N` | 10 | D4C 每 N 帧一次 + 插值（1 = 精确） |
| `--ct-stride N` | 1 | CheapTrick 每 N 帧一次 + Catmull-Rom 插值 |
| `--sm-stride N` | 2 | StoneMask 每 N 帧一次 + log-f0 插值 |
| `--den-stride N` | 0 | 0 = 精确第二遍 WORLD；N≥1 = f0 继承 + 每 N 帧 |
| `--threads N` | 2 | 双核（MLP 切半 + 第二遍 WORLD 并行），失败回退串行 |
| `--mlp-int8` | 关 | int8 权重（同一 blob，不重新导出） |
| `--nopitch` | 关 | 跳过升调（对照组） |
| `--in-f32-16k` / `--out-f32-16k` | 关 | 浮点 16 kHz 输入/输出（**比对钩子**） |
| `--xB-f32 PATH` | — | 直接读入升调后的信号（与 oracle 吃同一份输入） |
| `--dump DIR` | — | dump 各级中间量（**.f32**） |
| `--pitch-axis-ratio R` | 1.4 | 频轴/f0 比例（实测 1.394） |
| `--ct-once` / `--ct-stft` | 关 | **被否决的方案**，保留作对照 |

### 3.3 stderr 遥测（JSON，一行一条）

批处理结束：

```json
{"ok":true,"seconds":4.0,"samples_in":64000,"samples_out":64000,
 "frames_world":401,"voiced_frames":266,"median_f0_hz":135.323,
 "pitch_ratio":1.4,"pitch_impl":"soundtouch_wsola","format":"native_s24",
 "model_bytes":4843308,"peak_out":1.36006,"rms_out":0.22783,"clipped_samples":144,
 "world_ms":2441.12,"mlp_ms":3817.04,"analysis_ms":6451.20,
 "total_ms":8268.88,"analysis_rtf":1.6128,"rtf":2.0672}
```

流式模式：每块一行 + 结束时一行汇总：

```json
{"block":1,"frames_in":9600,"audio_ms":300.0,"proc_ms":285.2,"block_rtf":0.951,"cum_rtf":0.951,"done_s":0.3}
{"ok":true,"mode":"stream","blocks":3,"seconds":0.9,"block_ms":300,"fade_ms":20,
 "threads":2,"proc_ms":855.6,"wall_ms":890.1,"rtf":0.9510,"clipped_samples":0}
```

**字段契约**：`rtf` = `proc_ms / audio_ms`（不含 aplay 等待）；`samples_out` **必须等于**
`samples_in`（流式模式下 hold-back 的尾巴在结束时刷出，实测 127360 → 128000 就是靠这个修的）。

---

## 4. 权重 blob 格式（`host/model/student_v5.blob`）

小端，逐字段顺序：

```
char   magic[4] = "VCB1"
int32  version=1, in_dim=646, hidden=512, layers=4, out_dim=48,
       context=4, nceps_in=32, nceps_out=48, n_bins=513,
       fft_size=1024, frame_period_x10=100, sample_rate=16000
float  pitch_ratio
float  mu[646], sd[646]
float  dct_in[32][513], dct_out[48][513], synth[48][513]    # synth = pinv(dct_out).T
float  pitch_ratio (again)
per layer: float W[512][in_l], float b[512]
float  W_out[48][512], float b_out[48]
```

- 大小 4,843,308 B，SHA-256 `c04107b95de35fb3…`（见 `host/model/MODEL.md`）。
- `synth` 与 `dct_out` 只差 1.9e-9（DCT-II 行正交），仍按 `np.linalg.pinv` 原样导出，
  避免"用转置近似"的争议。

---

## 5. 兼容性声明

- **CLI 向后兼容 v23 调度器**：位置参数形状不变，`stderr` JSON 的 `rtf`/`clipped_samples` 字段不变。
- **blob 向后兼容**：`version=1`；新增 int8 量化表在运行时由 fp32 权重生成，**不写进 blob**。
- **寄存器兼容**：新增 GPIO 在 `0x41200000`，与 2026-10-11 控制版同址同义（ch1=ratio，ch2=reset 语义上
  只是本构建未接线）。
