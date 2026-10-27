# 系统架构与数据流

## 1. 总览

单个 Zynq-7020 器件内，**PS 跑算法（WORLD 分析 + 升调 + 神经网络），PL 跑 STFT/IFFT +
逐 bin 包络乘法**；音频经 WM8960 codec 进出。

```
┌──────────────────────────────── xc7z020clg400-2 ────────────────────────────────┐
│                                                                                  │
│  ┌── PS: 双核 Cortex-A9 @ 667 MHz ──────────────────┐   ┌── PL: 100 MHz ────────┐ │
│  │                                                  │   │                       │ │
│  │  vc_stream_pl (静态 ARM ELF, -O2)                 │   │  axis_stft_gain       │ │
│  │  ┌────────────────────────────────────────────┐  │   │  ┌─────────────────┐  │ │
│  │  │ 解码 S24/PCM16 → 32k→16k (127-tap FIR)     │  │   │  │ fft_fwd 1024    │  │ │
│  │  │ SoundTouch WSOLA 升调 1.4×                 │  │   │  │ 24 bit, unscaled│  │ │
│  │  │ WORLD: DIO→StoneMask→CheapTrick→D4C        │  │   │  │      ↓          │  │ │
│  │  │ 特征 646 维 → MLP 4×512 → 64 阶残差        │  │   │  │ 逐 bin × g_q    │  │ │
│  │  │ 包络移植 → 513 bin 实数增益 g (Q4.19)      │  │   │  │ (Q4.19 实数)    │  │ │
│  │  │ 窗 + int16 量化 → [送 PL]                  │  │   │  │      ↓          │  │ │
│  │  │ [PL 回] → OLA + wsum → 16k→32k → S24       │  │   │  │ fft_inv 1024    │  │ │
│  │  └────────────────────────────────────────────┘  │   │  │ 32 bit, unscaled│  │ │
│  │        ▲                    ▲                     │   │  └─────────────────┘  │ │
│  │        │ AXI-Lite 0x41200000│ AXI HP0             │   │  8715 cycles/帧=87 µs │ │
│  │   ┌────┴─────┐        ┌─────┴─────┐               │   │        ▲              │ │
│  │   │ AXI GPIO │        │ DDR 控制器 │               │   │        │ AXIS         │ │
│  │   │ 状态/帧计数│       │  1 GB      │◄──────────────┼───┼──┐ ┌───┴───────┐   │ │
│  │   └──────────┘        └───────────┘               │   │  └─┤ AXI DMA   │   │ │
│  └───────┬──────────────────────────────┬────────────┘   │    │ 7.1 ×3 ch │   │ │
│          │ AXI-Lite                     │ AXI-Lite/IRQ    │    │ 2×MM2S+1×S2MM│ │
│  ┌───────┴───────┐  ┌──────────────┐  ┌─┴────────────┐   │    └───────────┘   │ │
│  │ I2S RX (43C5) │  │ I2S TX (43C6)│  │ audio_fmt    │   │                    │ │
│  └───────┬───────┘  └──────┬───────┘  └──────────────┘   └────────────────────┘ │
└──────────┼─────────────────┼─────────────────────────────────────────────────────┘
           │                 │
      ┌────┴────┐       ┌────┴────┐
      │ WM8960  │       │ WM8960  │
      │  MIC    │       │  耳机   │
      └─────────┘       └─────────┘
```

## 2. PS / PL 分工（为什么这样分）

| 任务 | 放在 | 理由 |
|---|---|---|
| WORLD 分析/合成（DIO/StoneMask/CheapTrick/D4C） | **PS** | 需要 double 精度与大量 libm 调用；PL 化收益/风险比暂时不划算 |
| 特征 + MLP（1.15 M 参数） | **PS** | 4.94 MB 权重超过 7020 的 BRAM（4.9 Mb ≈ 0.6 MB）；放 PL 需要大量 DDR 带宽 |
| 重采样 / 打包 / 流式调度 | **PS** | 控制流复杂，数据量小 |
| **STFT/IFFT + 逐 bin 实数增益** | **PL** | 1024 点 FFT 是纯数据流、无控制流；定点 FFT 与 ARM 双精度 STFT **数学等价**，可逐样本比对（corr 0.99999999 / max 4 LSB） |
| 窗、OLA、wsum 归一化、增益 Q4.19 量化 | **PS** | 保留 double 精度；搬进 PL 需要缓存整段输出，收益小于风险 |
| 定点变调核（原 SoundTouch 替代） | **PL（备用）** | 已验证 bit-exact（RTF 0.0078），但**未接入主链**；与 STFT 版**互斥**，同一时刻只能加载一个位流 |

> **状态（2026-10-27）**：PL 当前入链的是 **STFT/ISTFT 核**（`fpga/stft/`），
> ARM 侧用 `--pl-stft` 走 DMA 通道；变调核（`fpga/build/`）保留为**已验证的备用设计**，
> 两者不能共存（同一 PL、同一套 PS7/I2S/DMA/GPIO）。切换需重载 `fpga_manager` 镜像。

## 3. 数据流（流式模式，块长 B）

```
arecord (32 kHz / S24_LE / 2ch)
   │  B ms 一块 (默认 300 ms)
   ▼
[1] 取左声道, S24 → double: x = (int32>>8)/8388608
   ▼
[2] 32k→16k, 127-tap Hamming-sinc, fc 7.5 kHz
      跨块携带 126 抽头历史; 丢掉属于历史的 31 个输出样本
   ▼
[3] SoundTouch WSOLA: setPitch(1.4)  → xB (16 kHz)
   ▼
[4] WORLD 第一遍 (x16):  DIO → StoneMask → CheapTrick → D4C
       默认档：ap_stride=10 + sm_stride=2；live 档：ct_stride=2 + sm_stride=2 + int8；
       精确档：ap/ct/sm 全 1
   ▼
[5] 特征: ceps32 = logsp·DCT_inᵀ; 68 维；±4 帧上下文 → 612；句级统计 34 → 646，按 mu/sd 标准化
   ▼
[6] MLP 4×512 (GELU erf) → 64 维残差 → logsp_pred = ceps64·synth
   ▼                                         ▲
   │                     [4'] 第二遍 WORLD (xB) ──┘  ← 在 worker 线程与 MLP 并行
   ▼
[7] 包络移植: diff_db = 0.5(pred−src)·20/ln10, 限幅 ±20 dB, 静音 mask 平滑
   │         → 每帧 513 个实数增益 g；量化成 Q4.19 (g_q = g·2^19)
   ▼
[8] 窗 (periodic Hann) + int16 量化 ──AXIS/DMA──► PL:
       1024 点前向 FFT (unscaled) → Y[k]=round(A[k]·g_q/2^13) → 1024 点逆向 FFT
    ◄──AXIS/DMA── z·256 (int32) ──► OLA + wsum 归一化 (double)
   ▼
[9] 16k→32k → S24 打包 (out_gain 0.6)
   │  块间 20 ms hold-back 交叉淡化（不重复音频, 只滞后 fade_ms）
   ▼
aplay (32 kHz / S24_LE / 2ch, --start-delay=64000)
```

**延迟分解**（O64 + live 档实测，300 ms 块，2026-10-27）：
`B（攒块 300）+ proc(B)（p50 276.0 ms）+ 淡化 hold-back（20，已含在 300 内）`
→ 端到端 p50 **576.0** / p95 **584.0** / p99 **584.8** / max 586.8 ms，60 s/200 块 0 欠载
（`metrics/O64_LIVE_20261027.md`）。临界路径上没有其它排队：`--stream` 每块算完立刻写出并 flush。

## 4. 控制路径

```
主机 (Windows) ──串口 COM8 115200──► 板端 shell
                                     ├─ 上传: base64 分块 + 逐块 SHA
                                     ├─ 加载: fpga_manager (4 字节反转镜像 + gzip)
                                     ├─ 校验: AXI GPIO 回读 (regtool / devmem)
                                     └─ 运行: ./vc_o64_pl ... | aplay ...
```

串口是**独占**资源；所有板端操作的前置检查见 `docs/hardware_setup.md` §4。

## 5. 时钟与复位

| 时钟 | 频率 | 来源 | 用途 |
|---|---|---|---|
| `clk_fpga_0` | 100 MHz | PS7 `FCLK_CLK0` | 全部 PL 逻辑、AXI-Lite、AXI-Stream |
| `ACLK`（DMA/GPIO） | 100 MHz | 同上 | AXI 主机接口 |
| 音频 MCLK/BCLK/LRCLK | 由 `axi_dynclk` + I2S 产生 | PL | WM8960 |

复位：`proc_sys_reset` 的 `peripheral_aresetn` → stream 核的 `aresetn`。
`aresetn` 有效会把帧引擎拉回 IDLE 并清空帧缓存，所以**热复位可以做到"从零状态"**——
但 GPIO ch2 没有接到它，只能靠重新加载位流达到同样效果。

## 6. 资源占用（实现后，STFT 版）

| 资源 | 用量 | 占比 |
|---|---|---|
| LUT | 16,723 | 31.43% |
| FF | 28,677 | 26.95% |
| BRAM | 22 | 15.71% |
| DSP | 76 | 34.55% |
| WNS / WHS | +0.347 / +0.040 ns | 100 MHz，0 failing endpoints |

对比：**备用变调核**（`fpga/build/`）8,378 LUT / 5 BRAM / 6 DSP / WNS +0.813 ns。
STFT 版多用 8.3k LUT、17 BRAM、70 DSP（两个 1024 点 xfft 占大头），
但换来了 STFT 段 −143.2 ms / 整链 RTF −0.036。数据：`fpga/stft/report/impl_*.txt`、
`PL_STFT_20261027.md` §6。
