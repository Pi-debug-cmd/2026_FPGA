# fpga/report — 综合与实现报告（原始文本）

这些文件是 Vivado 直接输出的报告，**未编辑**。之所以不放截图，是因为文本可 grep、可核对。

## 1. 清单

| 文件 | 内容 | 关键数字 |
|---|---|---|
| `resources_timing.md` | **资源与时序汇总表**（由 `collect_metrics.py` 自动抽取，含每行来源） | LUT 8378 / FF 13286 / BRAM 5 / DSP 6 / WNS +0.813 |
| `impl_utilization.txt` | 实现后资源利用率 | 15.75% LUT、12.49% FF、3.57% BRAM、2.73% DSP |
| `impl_utilization_hier.txt` | 实现后**分层**资源（定位哪个模块吃资源） | 211 KB |
| `impl_timing.txt` | 实现后时序摘要 | WNS +0.813 / WHS +0.045 / WPWS +0.530 / 0 failing |
| `impl_drc.txt` | 实现后 DRC | 0 Error / 0 Critical Warning |
| `impl_clock_utilization.txt` | 时钟资源与扇出 | `clk_fpga_0` 100 MHz，扇出 13186 |
| `impl_bus_skew.txt` | 总线偏斜 | 83 KB |
| `synth_utilization.txt` | 综合后资源 | 9374 LUT / 14506 FF / 5 BRAM / 6 DSP |
| `synth_utilization_hier.txt` | 综合后分层资源 | 228 KB |
| `synth_timing.txt` | 综合后时序估计 | WNS +3.750 ns |
| `synth_drc.txt` | 综合后 DRC | — |
| `m3_compare_clean.txt` | **DMA 端到端比对 PASS** | `max_abs_diff 0`，128000 样本 |
| `m3_compare_output.txt` | **首轮 FAIL（保留为证据）** | 16 个样本错，两段各 8 个，全 0 |
| `m3_compare_ratio48k.txt` | 第二个比例的比对 | `max_abs_diff 0` |
| `build_changes_2018_3.md` | 2018.3 建工程的全部改动记录 | 4 处 BD 改动，RTL 未改 |

## 2. 读法

```bash
# 资源数字的出处
grep -E "Slice LUTs|Block RAM|DSPs" fpga/report/impl_utilization.txt

# 时序是否真的收敛
grep -A3 "WNS(ns)" fpga/report/impl_timing.txt

# 失败那次到底错在哪
head -20 fpga/report/m3_compare_output.txt
```

## 3. 与 `metrics/` 的关系

- `resources_timing.md` 是**抽取结果**，`metrics/resource_timing.csv` 是同一份数据的机器可读版。
- 重新生成：

```bash
python skill/golden_reference_compare/collect_metrics.py --vivado-dir fpga/report \
  --out metrics/resource_timing.csv --md metrics/resource_timing.md
python metrics/scripts/csv_to_md.py metrics/resource_timing.csv fpga/report/resources_timing.md
```
