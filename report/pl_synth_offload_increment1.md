# WORLD 合成卸载 · 增量 1：1024 点 IFFT 核（时分复用版）

日期：2026-10-18　器件：xc7z020clg400-2（野火 Zynq-7020）　工具：Vivado 2026.1 / xsim 2026.1

## 0. 结论速览

| 项目 | 结果 | 目标（Lead） |
| --- | --- | --- |
| Slice LUT | **363**（0.68%） | ≤10k ✅ |
| Slice FF | **154**（0.14%） | — |
| BRAM | **1×RAMB36 + 1×RAMB18 = 3 个 RAMB18 当量**（1.1%） | ≤4 ✅ |
| DSP48E1 | **4**（1.8%） | ≤8 ✅ |
| 时序（clk 10 ns / 100 MHz） | **WNS +3.714 ns，WHS +0.267 ns，0/545 失败端点** | ≥0 ✅ |
| 仿真 | 6/6 用例 PASS；**RTL 与 Python 定点模型 0 LSB 逐位一致**；vs numpy 浮点黄金 ≤2 LSB（1.53e-5，容差 1e-3） | 保持 ✅ |
| 后综合网表仿真 | funcsim 网表（1×RAMB36 + 1×RAMB18 + 4×DSP48E1 + 154 FF）同样 6/6 PASS、0 LSB 逐位一致 | ✅ |
| 吞吐 | 5120 蝶形 × 6 拍 = 30,720 拍 = **307 µs/帧**；实测含 AXI 背压 33.5k 拍 ≈ 335 µs/帧 → **约 2984 帧/s**，为 WORLD 需求（100 帧/s）的 **29.8 倍**，占空比 3.35% | 核算 ✅ |

> 关于"LUT 363 是否被优化掉了"：否。本核是**单蝶形时分复用**，10 级 FFT 共用同一套硬件：
> 4 个 DSP（1 次 18×18 复数乘）、1 条 37 位和差/舍入/饱和通路、2 组 10 位地址计算、12 态 FSM；
> 数据与旋转因子都在 BRAM。作为对比，Xilinx FFT IP 的 1024 点**流水线**核有 10 级蝶形阵列，
> 才需要约 5k LUT。证据见 §4.3：后综合网表中 4×DSP48E1、1×RAMB36E1、1×RAMB18E1、154 FF
> 全部在位，且 funcsim 仿真逐样本匹配黄金向量——若输出未连接或 RAM 读数据未参与输出，不可能通过。

## 1. 接口（AXI-Stream 风格）

| 信号 | 方向 | 位宽 | 说明 |
| --- | --- | --- | --- |
| `clk` / `rst_n` | in | 1 / 1 | 100 MHz 时钟；同步复位，低有效 |
| `s_axis_tvalid/tready` | in/out | 1 | 输入握手；`tready` 仅在空闲态为 1 |
| `s_axis_tdata` | in | 32 | `{imag_q15[15:0], real_q15[15:0]}`，Q1.15 有符号 |
| `s_axis_tlast` | in | 1 | 预留，本版本忽略（固定按 513 拍计数） |
| `m_axis_tvalid/tready` | out/in | 1 | 输出握手；背压时 `tdata/tlast` 保持稳定 |
| `m_axis_tdata` | out | 32 | `{{14{x[17]}}, x[17:0]}`，x[n] 为 Q1.17 有符号 |
| `m_axis_tlast` | out | 1 | n = 1023 时为 1 |
| `busy` / `done` | out | 1 / 1 | 处理中标志 / 一帧结束单拍脉冲 |

- 输入固定 **513 拍**，k = 0..512 顺序（DC..Nyquist）；内部自动补 `X[1024-k] = conj(X[k])`（k=1..511）。
- 输出固定 **1024 拍**实样本：`x[n] = (1/1024)·Σ X[k]·exp(+j2πkn/1024)`（等价 numpy `ifft`）。
- 输入无溢出契约（主机保证）：`(|X0|+|X512|+2Σ|X1..511|)/1024 ≤ 0.99` 且 `|X[k]| ≤ 32767/32768`。

## 2. 结构

```
s_axis ──> 输入打包 (Q1.15→Q1.17, 厄米补点)
              │  写 X[k]→mem[rev10(k)], conj→mem[rev10(1024-k)]
              ▼
        1024×36 SDP BRAM (1 RAMB36)  ←── 旋转因子 ROM 512×36 Q3.15 (1 RAMB18)
              │  单蝶形 6 拍流水，完成 10 级 × 512 = 5120 次蝶形
              ▼
        顺序读 1024 点 → m_axis (Q1.17 实部)
```

- **时分复用**：一个 radix-2 蝶形串行处理全部 5120 次蝶形；级号 `stage(1..10)`、级内序号
  `bf_count(0..511)` 决定地址：`half=2^(s-1)`，`a=(group<<s)|j`，`b=a|half`，
  旋转因子地址 `j<<(10-s)`（512 项 ROM，Q3.15，1.0=32768 可精确表示）。
- **蝶形 6 拍**：读 A → 读 B（同时锁存 A）→ 4 个 18×18 乘积打拍 → 和/差+舍入+饱和
  → 写回 A → 写回 B（推进计数）。单读单写 RAM 每拍只有 1 次访问，避免 Vivado 无法推断的
  "同拍 2 读 + 2 写"模式。
- **定点格式**：输入 Q1.15；内部/输出 Q1.17（18 位有符号）；旋转因子 Q3.15（18 位有符号）；
  每级蝶形缩放 1/2（10 级共 1/1024）；复数乘 18×18→36 位，+2^14 四舍五入后右移 15 位并饱和；
  和/差为 19 位，+1 后算术右移 1 位（四舍五入）。逐级缩放保证内部不溢出。
- **背压**：输出侧用 `out_raddr/out_count` 只在真正发起新读时前进；被 `tready` 挡住时读地址
  保持不变，`dout/tdata/tlast` 全程稳定。
- **资源收敛过程（重要教训）**：最初用"同拍 2 读 + 2 写"的原地 DPRAM 写法，Vivado 2026.1
  无法推断成 BRAM，退化为 36,864 个寄存器 + 数万 LUT（LUT 70,249 / FF 37,023 / WNS −1.762 ns）。
  改为标准单读单写 SDP 模板后回到 1 个 RAMB36，LUT/FF 降低约 200 倍。

## 3. Python 参考实现与黄金向量

`src/rtl/synth_offload/gen_ifft_vectors.py`（纯 numpy）：

1. 按 WORLD 合成链路同构生成 6 组 513 点复数谱：全带冲激、8 单音、sqrt(包络)+最小相位
   （300 Hz~4 kHz 四个共振峰）、随机相位宽带、仅 Nyquist、仅 DC；DC/Nyquist 强制实数，
   并按无溢出上界归一化。
2. 厄米补齐后做 `numpy.fft.ifft`，量化 Q1.17 作为黄金向量；
3. 生成与 RTL 同序的**逐位定点模型**（同一套舍入/饱和），自检模型 vs numpy 误差 = **1.53e-5**；
4. 生成 `twiddle_rom_1024.v`（512×36，Q3.15）与 `case*_input.hex / case*_expected.hex / vectors.json`。

产物：`build/generated/pl_synth_offload/`（hex、vectors.json、sim_verification.json、post_synth_verification.json）。

## 4. 验证

### 4.1 方法

- `sim/tb_ifft1024_stream.sv`：513 拍输入（随机 valid 空拍）+ 1024 拍输出（随机 `tready` 背压），
  逐样本比对黄金向量；检查 TLAST、背压下输出稳定、无多余输出、帧间可再次接收；统计最大绝对误差。
- xsim 在工作区外运行（DSH 沙箱限制）：`D:\xsim_work\synth_offload`。
- 判据：最大绝对误差 ≤ 1e-3（Q1.17 下 131 LSB），且 RTL 与定点模型 0 LSB。

### 4.2 结果（行为级 RTL，xsim 2026.1）

| 用例 | 输入峰值 | 输出峰值(Q1.17) | RTL vs 定点模型 | RTL vs numpy golden | 结果 |
| --- | --- | --- | --- | --- | --- |
| impulse_full_band | 0.45 | 0.45 | 0 LSB | 2 LSB = 1.53e-5 | PASS |
| multi_tone | 0.90 | 0.0141 | 0 LSB | 2 LSB = 1.53e-5 | PASS |
| world_like_minphase | 0.95 | 0.338 | 0 LSB | 2 LSB = 1.53e-5 | PASS |
| random_broadband | 0.95 | 0.0575 | 0 LSB | 2 LSB = 1.53e-5 | PASS |
| nyquist_alternating | 0.90 | 8.8e-4 | 0 LSB | 1 LSB = 7.6e-6 | PASS |
| dc_only | 0.90 | 8.8e-4 | 0 LSB | 1 LSB = 7.6e-6 | PASS |

每用例实测帧周期 33,493~33,540 拍（含随机空拍/背压），背压空拍约 930 次输入、110~190 次输出。

### 4.3 后综合网表仿真（回应“是否被优化掉了”）

- MCP 执行 `write_verilog -force -mode funcsim` 导出综合后网表
  `synth/ifft1024_stream_funcsim.v`（6885 行，205 KB）。
- 网表原语统计：**RAMB36E1×1、RAMB18E1×1、DSP48E1×4、FDRE×142 + FDSE×12 = 154 FF**，无黑盒。
- 在 `D:\xsim_work\synth_offload\post_synth` 用同一 TB 跑后综合仿真（`xelab -L unisims_ver` + `glbl`）：
  **6/6 PASS，RTL vs 定点模型 0 LSB，vs numpy golden ≤2 LSB**。
  证明综合没有剪掉功能逻辑，输出端口、RAM 读数据、DSP 乘法都真实参与运算。

## 5. 资源与时序（OOC 综合）

- 命令：`synth_design -mode out_of_context -top ifft1024_stream -part xc7z020clg400-2`
  + `create_clock -name clk -period 10.000`（100 MHz）。
- 结果（`synth/utilization.txt`、`synth/timing_summary.txt`）：

| 资源 | 使用 | 可用 | 占比 |
| --- | --- | --- | --- |
| Slice LUT | 363（网表 LUT 单元 468） | 53,200 | 0.68% |
| Slice FF | 154 | 106,400 | 0.14% |
| RAMB36 | 1 | 30（140 RAMB18 当量中的 2） | — |
| RAMB18 | 1 | 280 | — |
| DSP48E1 | 4 | 220 | 1.8% |
| 控制集 | 10 | 13,300 | 0.08% |

- 时序：WNS **+3.714 ns**、WHS **+0.267 ns**、WPWS 4.500 ns，Setup/Hold 失败端点均为 **0/545**。
- 关键路径：`pr_rr_reg/CLK → t_re_reg[17]/D`（10 级逻辑，6.286 ns / 10 ns）：
  DSP 乘积打拍 → 37 位和差 → 舍入 → 饱和。
- 说明：OOC 综合不含板级 I/O 约束，也未做 place/route；WNS 余量 3.7 ns，实现后应仍为正，
  但上板前需在完整工程中复测（下一步增量 2 一并做）。

## 6. 吞吐核对

```
每帧蝶形次数   = (N/2)·log2N = 512 × 10 = 5120
单蝶形拍数     = 6（读A/读B/乘/舍入/写A/写B）
每帧蝶形拍数   = 5120 × 6 = 30,720 拍
@100 MHz       = 307.2 µs/帧  → 3255 帧/s（纯计算）
实测含 AXI 背压 = 33,509 拍/帧（6 用例均值）= 335.1 µs → 2984 帧/s
WORLD 需求     = 100 帧/s（10 ms 帧）
余量           = 29.8 倍；占空比 = 335 µs / 10 ms = 3.35%
```

即使把帧率提高到 1 kHz，仍有约 3 倍余量；后续加最小相位/OLA 前不必再扩并行。

## 7. 复现

```powershell
# 1) 生成黄金向量 + 旋转因子 ROM（numpy）
python src/rtl/synth_offload/gen_ifft_vectors.py

# 2) 行为级仿真（必须在工作区外，DSH 沙箱限制）
#    拷贝 src/rtl/synth_offload/*.v|sv 与 build/generated/pl_synth_offload/*.hex 到 D:\xsim_work\synth_offload
xvlog -sv ifft1024_stream.v dpram_1024x36.v twiddle_rom_1024.v
xvlog -sv tb_ifft1024_stream.sv
xelab tb_ifft1024_stream -s ifft_test
xsim ifft_test -runall -log xsim.log

# 3) 证据汇总（RTL vs 定点模型/golden）
python build/generated/pl_synth_offload/verify_increment1.py

# 4) OOC 综合（Vivado MCP）
python tools/mcp_vivado.py start
python tools/mcp_vivado.py exec "source C:/Users/World/Desktop/2026_FPGA/src/rtl/synth_offload/synth_ifft1024.tcl"

# 5) 后综合网表仿真（可选，需 unisims_ver + glbl）
#    MCP: write_verilog -force -mode funcsim .../synth/ifft1024_stream_funcsim.v
#    在 D:\xsim_work\synth_offload\post_synth 下 xvlog/xelab -L unisims_ver/xsim
```

## 8. 下一步（增量 2：最小相位 + OLA，不含在本轮）

1. **双缓冲输入**：两帧 ping-pong（或 513 深度 FIFO），消除"处理一帧时 `tready=0`"对上游的影响。
2. **最小相位与分数时移**：建议 PS 侧沿用 WORLD 现有最小相位代码生成 513 点复谱（Q1.15），
   分数时移线性相位在 PS 或 PL 频谱域乘；PL 只做 IFFT + OLA，避免在 PL 里再放倒谱 FFT。
3. **OLA**：PL 建 1024+160 点 Q1.17 累加缓冲，帧移 160 点（16 kHz/10 ms）；每帧把 1024 点
   加窗后累加、输出 160 点；输入加 `scale_exp`（每帧 2^-e 归一化，输出乘回 2^e）。
   预算：累加器 1~2 个 RAMB18 + 加法器，LUT 预计 <1.5k，DSP 仍 4，总量仍远低于器件上限。
4. **验证**：Python 参考实现逐帧生成 IFFT + OLA 结果，PL 模型逐样本比对（目标 ≤1e-4）。
5. 风险：WORLD 合成还含非周期（aperiodic/noise）分量；建议增量 2 只覆盖 periodic 部分，
   aperiodic 先留 PS，作为增量 3 再评估。

## 9. 文件清单

| 文件 | 说明 |
| --- | --- |
| `src/rtl/synth_offload/ifft1024_stream.v` | IFFT 核 RTL（时分复用，12 态 FSM） |
| `src/rtl/synth_offload/dpram_1024x36.v` | 1024×36 单读单写 SDP BRAM 封装 |
| `src/rtl/synth_offload/twiddle_rom_1024.v` | 512×36 Q3.15 旋转因子 ROM（生成） |
| `src/rtl/synth_offload/tb_ifft1024_stream.sv` | 自动比对 testbench |
| `src/rtl/synth_offload/gen_ifft_vectors.py` | Python 参考实现 / 黄金向量 / 定点模型 / ROM 生成 |
| `src/rtl/synth_offload/synth_ifft1024.tcl` | OOC 综合脚本（MCP 可复现） |
| `build/generated/pl_synth_offload/` | 黄金向量、vectors.json、sim/sim_post_synth 日志、synth 报告与 DCP |
| `report/pl_synth_offload_synth.json` | 综合/时序/后综合仿真证据 |
| `report/pl_synth_offload_post_synth.json` | 后综合网表仿真逐用例证据 |
