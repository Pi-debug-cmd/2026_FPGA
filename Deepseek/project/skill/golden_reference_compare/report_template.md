# 结果表模板（每个数字都必须带来源）

复制这张表到你的报告里，**不要删 source 列**。评审复核时只需要顺着 source 打开文件。

## 1. 一致性（黄金参考比对）

| 对象 A | 对象 B | 样本/形状 | max\|Δ\| | SNR (dB) | corr | 时延 | 判定 | source |
|---|---|---|---|---|---|---|---|---|
| 板端 ARM `x16` | 主机 x86 `x16` | 64000 | 0 | inf | 1.000000 | 0 | bit-exact | `out/host32/x16.f32` ↔ `out/board/dump/x16.f32` |
| 板端 `y16` | Python oracle（1 ulp 输入差） | 64000 | 4.3e-4 | 74.86 | — | 0 | numeric axis | `out/c_board_exact/y16.f32` |
| RTL 输出 | 定点 Python 模型 | 128000 | 0 | inf | — | 0 | bit-exact | `fpga/report/m3_compare_clean.txt` |
| 首次失败（对照） | 同上 | 128000 | — | — | — | 0 | 16 samples / 2×8 / 全 0 | `fpga/report/m3_compare_output.txt` |

## 2. 资源与时序（Vivado 报告）

| 指标 | 综合 | 实现 | 器件总量 | 占比（实现） | source |
|---|---|---|---|---|---|
| Slice LUTs | 9374 | 8378 | 53200 | 15.75% | `synth_utilization.txt` / `impl_utilization.txt` |
| Slice Registers | 14506 | 13286 | 106400 | 12.49% | 同上 |
| Block RAM Tile | 5 | 5 | 140 | 3.57% | 同上 |
| DSPs | 6 | 6 | 220 | 2.73% | 同上 |
| Bonded IOB | 12 | 12 | 125 | 9.60% | 同上 |
| WNS | +3.750 ns | +0.813 ns | — | — | `*_timing.txt` |
| WHS | +0.035 ns | +0.045 ns | — | — | 同上 |
| failing endpoints | 0 | 0 | — | — | 同上 |

时钟：`clk_fpga_0` = PS7 `FCLK_CLK0` = 100 MHz（周期 10.000 ns）。

## 3. 性能（板上实测）

| 指标 | 数值 | 条件 | source |
|---|---|---|---|
| 4 s 批处理总耗时 | 3857–3941 ms（3 次） | 32 kHz S24 双声道输入 | `board_c_20261025_stage2.md` §1 |
| RTF | 0.967 / 0.983 / 0.985 | 同上 | 同上 |
| analysis_rtf / render_rtf | 0.792 / 0.150 | 同上 | 同上 |
| 流式块 300 ms 每块耗时 | 285 ms（3 次全 0 欠载） | `--preset live --stream 300` | `board_c_20261025_squeeze.md` §1 |
| 端到端延迟 | 585 ms | `= 300 + 285` | 同上 |
| PL 变调核 4 s 音频 | 31.19 ms（RTF 0.0078） | AXI DMA 1024 样本/块 | `pl_build_20261025.md` §4.4 |

## 4. 质量四指标（同一 4 s 素材，`scripts/score_full.py`）

| 版本 | identity_mean | identity_p10 | leakage_rel | UTMOS | CER | cer_rel | 门禁 |
|---|---|---|---|---|---|---|---|
| A 电脑端 T4 | 0.6262 | 0.6262 | −0.0373 | 1.3521 | 0.3077 | +0.1202 | UTMOS/CER 不过 |
| C 板端 stage-1 | 0.6463 | 0.6463 | +0.0215 | 2.1063 | 0.0769 | −0.1106 | UTMOS/泄漏不过 |
| E 板端 stage-2 | 0.6373 | 0.6373 | +0.0157 | 2.1045 | 0.0769 | −0.1106 | UTMOS/泄漏不过 |
| L5 演示档 | 0.6047 | 0.6047 | +0.0174 | 2.1351 | 0.1538 | −0.0337 | UTMOS/泄漏不过 |

> 注意：门禁 `utmos >= 2.30` 与 `leakage_rel <= 0` 在**所有**板上版本都没过。
> 报告里必须照实写，并把"相对 stage-1 的变化"和"绝对门禁"分开陈述。

## 5. 稳定性

| 项 | 数值 | 条件 | source |
|---|---|---|---|
| 同一二进制 3 次运行 | 8171 / 8170 / 8176 ms（±0.1%） | 4 s 批处理 | `board_c_20261025.md` §8.1 |
| 不同构建产物输出一致 | 逐字节相同 | 3 个构建 | 同上 |
| 300 ms 块 0 欠载 | 连跑 3 次 | 12 s 音频 | `board_c_20261025_squeeze.md` |
| 30 min 长稳 | **未测** | — | — |
