# WORLD Synthesis() CPU 侧拆解（增量 2 前置分析）

日期：2026-10-18　性质：只读分析（未改上游源码）　宿主：i7-14650HX / MinGW g++ 8.1 `-O3` / 单线程

## 0. 结论（先看这段）

实测 `Synthesis()` 的耗时**不是**按“帧”均分，而是按 **WORLD 的脉冲（pulse）** 循环：

| 三段（按 Lead 口径） | 秒（5.01 s 语音） | 占比 |
| --- | --- | --- |
| **1. 最小相位谱构建**（log 输入 + 镜像 → IFFT → 折叠 → FFT → exp/cos/sin） | 0.12465 | **84.99%** |
| **2. 激励/响应生成**（周期响应分数时移+IFFT、非周期噪声 FFT、复乘、包络/非周期比插值、timebase） | 0.02156 | 14.70% |
| **3. 重叠相加 OLA**（1024 点逐样本累加） | 0.00046 | 0.31% |
| 未归属（分配/初始化/计时开销） | 0.00032 | 0.22% |
| 合计 | **0.14667 s** | 100% |

且最小相位内部 **86.6% 是 exp/cos/sin**（513 bin × 3 个超越函数/次调用）：

| 最小相位内部 | 秒 | 占最小相位 | 占合成总 |
| --- | --- | --- | --- |
| **exp/cos/sin（复指数）** | 0.09201 | **86.6%** | **62.7%** |
| 正向 FFT（1024 点） | 0.00883 | 8.3% | 6.0% |
| 倒谱 IFFT（1024 点） | 0.00453 | 4.3% | 3.1% |
| 倒谱折叠 / 镜像 | 0.00090 | 0.8% | 0.6% |

**结论：占比最大的单项是“最小相位谱构建”，而其中 2/3 的整链时间花在 513 bin 的 `exp(real)·cos/sin(imag)` 上。**
增量 1 的 1024 点 IFFT 核本身只对应“响应生成”里的一小段（≈1 个 FFT/脉冲的 1/7），
按原计划做“帧级 IFFT + OLA”只能覆盖约 15%，**必须改为最小相位加速器**。

## 1. 方法（可复现）

1. 复制 `build/generated/world_source_v035/pyworld-0.3.5/lib/World/src/synthesis.cpp`，
   用 `cpu_breakdown/patch_synthesis.py` 插入 `std::chrono` 打点（不改上游源码）；
2. 复制 `common.cpp`，用 `patch_common.py` 在 `GetMinimumPhaseSpectrum` 内细分为
   镜像 / 倒谱 IFFT / 折叠 / 正向 FFT / exp-cos-sin；
3. `gen_bench_inputs.py`：取 `data/registrations/source_20261015/speaker01/holdout.wav`
   前 5 秒（32 kHz→16 kHz），用 pyworld 0.3.5（与板上同源）做
   DIO+StoneMask+CheapTrick+D4C（fft_size=1024、frame_period=10 ms），
   得到 f0 / 谱包络 / 非周期性，并用 `pyworld.synthesize` 生成参考波形；
4. `main_bench.cpp` 读二进制输入，调用插桩版 `Synthesis()`，3 次取均值，输出
   `bench_result.json`；同时把输出波形与 pyworld 参考逐样本比较。

功能一致性：插桩版输出与 pyworld 参考波形
**最大绝对差 1.67e-16、RMS 7.68e-18**（浮点舍入级），说明打点没有改变行为。

## 2. 实测数据

输入规模（5.01 s @ 16 kHz，fft_size 1024，10 ms 帧）：

| 项 | 数值 |
| --- | --- |
| 分析帧数 `f0_length` | 501（100 帧/s） |
| 合成脉冲数 `n_pulses` | **1772**（354 脉冲/s） |
| 其中浊音脉冲（跑周期分支） | 230 |
| 最小相位谱构建调用次数 | **2002**（= 1772 非周期 + 230 周期） |
| FFT/IFFT 总次数 | **7778**（非周期 4 次/脉冲 + 浊音脉冲再加 3 次） |
| log 调用总次数 | **1,027,026**（513 × 2002） |
| exp / cos / sin 调用总次数 | 各 **1,027,026** |

按 10 ms 帧折算：约 **15.5 次 FFT/IFFT、2050 次 log、2050 次 exp/cos/sin 每帧**（WORLD 按脉冲算，故比帧数多）。

宿主总耗时 0.14667 s / 5.01 s 音频 → 宿主 RTF 0.0293（x86 单线程）。
板上实测合成 RTF 0.550，约为宿主的 18.8 倍（ARM Cortex-A9 双精度超越函数更慢），
**绝对时间不可移植，占比用于估算**。

## 3. 卸载后 PS 侧 RTF 反推（0.550 × 占比）

| 卸载范围 | 合成 RTF 保留 | PS 全链 RTF（0.816 − 合成卸载量） |
| --- | --- | --- |
| 只卸 exp/cos/sin（62.7%） | 0.550×0.373 = **0.205** | 0.816 − 0.345 = **0.471** |
| **只卸最小相位构建（85.0%）** | 0.550×0.150 = **0.083** | 0.816 − 0.468 = **0.349** |
| 最小相位 + 激励/响应（≈99.7%） | ≈0.002 | 0.816 − 0.548 = **0.268**（受分析 0.25 + 映射 0.015 限制） |

## 4. 增量 2 建议（待 Lead 确认后开工，不自行扩大范围）

**PL 核：最小相位谱加速器**（覆盖 84.99% 的合成耗时），把 WORLD 的
`GetMinimumPhaseSpectrum` 原语搬进 PL：

- 输入：513 个 `log_spectrum[i]`（PS 侧由 `log(spectrum·(1−ap))/2` 或 `log(spectrum·ap)/2` 得到，
  可约定 16 位定点 + 指数；或者 PL 连 log 一起做，再覆盖 12.7%）；
- PL 内：`log_spectrum` 镜像 → 1024 点倒谱 IFFT → 最小相位折叠 →
  1024 点正向 FFT → 513 bin `exp(re/N)·cos/sin(im/N)`；
- 输出：513 个复数最小相位谱（Q 定点 + 指数），PS 取回后继续原有响应/OLA；
- 接口：AXI-Stream 双缓冲（沿用增量 1 的 valid/ready 风格），每次调用 513 拍进 / 513 拍出；
  2002 次调用/s、每次约 2 KB 输入 → 约 4 MB/s，HP 口无压力；
- 资源预估（累计，含增量 1）：1024 点 FFT/IFFT 引擎复用增量 1 蝶形（+正向模式/复数输入）
  ≈1.5k LUT / 3 BRAM / 4 DSP；CORDIC 复指数（exp + cos/sin）≈2k LUT / 2 BRAM / 4–8 DSP；
  合计预计 **3–4k LUT、≤6 BRAM、≤12 DSP**，满足 LUT ≤8k / BRAM ≤6 / DSP ≤16；
- 吞吐预估：2×1024 点 FFT（约 2×30.7k 拍，按增量 1 串行引擎）+ 513 bin CORDIC（约 16k 拍）
  ≈ 80k 拍/次 = 0.8 ms；400 次/s → 约 32% 占空比 @100 MHz，仍有余量；
  若紧可做双 CORDIC 并行或提高 FFT 时钟；
- 验证：≥20 个真实帧对应约 80 次最小相位调用，逐 bin 比对宿主参考（建议判据：
  幅度 ≤0.1 dB、相位 ≤0.5° 或时域回代差 ≤2 LSB），并做后综合 funcsim。

**不建议**继续原“帧级 IFFT+OLA”方案：实测它只覆盖 OLA 0.31% + 部分响应生成，收益约 15%，
与 84.99% 的最小相位相比性价比太低。

## 5. 局限

- 宿主 x86 与板上 ARM 的绝对时间差 ~19 倍，占比为同算法结构下的估计；
- `exp/cos/sin` 在 ARM 上可能更贵，实际占比可能更高（对 PL 卸载更有利）；
- 本拆解只覆盖 `Synthesis()`（0.550 RTF），不含分析、映射与 I/O。

## 6. 复现

```powershell
# 1) 生成基准输入（pyworld 0.3.5）
$env:PYTHONPATH='...\build\generated\world_deps'
python build/generated/pl_synth_offload/cpu_breakdown/gen_bench_inputs.py

# 2) 复制并插桩（不改上游源码）
python build/generated/pl_synth_offload/cpu_breakdown/patch_synthesis.py
python build/generated/pl_synth_offload/cpu_breakdown/patch_common.py

# 3) 编译宿主（MinGW g++）
g++ -O3 -std=c++11 -I <World/src> synthesis_bench.cpp common_bench.cpp fft.cpp \
    matlabfunctions.cpp main_bench.cpp -o bench.exe

# 4) 运行
bench.exe f0.bin sp.bin ap.bin y_ref.bin y_out.bin 1024 10 16000 501 80160 bench_result.json
```

证据：`report/pl_synth_offload_cpu_breakdown.json`、`cpu_breakdown/bench_result.json`、
`cpu_breakdown/bench_inputs.json`、`cpu_breakdown/mp_subparts_last_run`（同上 JSON 内）。
