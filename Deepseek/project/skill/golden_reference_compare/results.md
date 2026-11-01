# 已验证的复用结果 — golden_reference_compare

所有结果都是本机真实数据跑出来的，命令与文件都在下面，可以逐条复跑。
生成的表格：`example/results_table.md`（由工具自己写）。

## 1. 真实数据上的比对（4 组）

```bash
py=.../env/venv/Scripts/python.exe
gc=skill/golden_reference_compare/golden_compare.py
bc=<workspace>/board_c_20261025

$py $gc $bc/out/board/dump/x16.f32 $bc/out/host32/x16.f32 --label arm_vs_x86_x16
$py $gc $bc/out/board/dump/y16.f32 $bc/out/c_board_exact/y16.f32 --label board_vs_oracle_y16_1ulp_in
$py $gc $bc/out/opt/base/logsp.f32 $bc/out/opt/all/logsp.f32 --shape 401x513 --max-lag 0
$py $gc $bc/out/score/var/F_fp32.f32 $bc/out/score/var/G_int8.f32 --label fp32_vs_int8
```

| dut | 样本 | max\|Δ\| | SNR | 判定 | 与已有报告是否一致 |
|---|---|---|---|---|---|
| arm_vs_x86_x16 | 64000 | 0 | inf | PASS (bit-exact) | 一致：文档记 "x16 逐字节相同" |
| board_vs_oracle_y16_1ulp_in | 64000 | 4.31e-4 | 74.86 dB | FAIL → 判为 numeric axis | **一致**：文档 §8.2(c) 记录 74.86 dB，并证明是 1 ulp 放大 |
| logsp_base_vs_all_401x513 | 401×513 | 0 | inf | PASS (bit-exact) | 一致 |
| fp32_vs_int8 | 64000 | 1.44e-2 | 41.67 dB | FAIL | **一致**：文档记 "SNR 41.7 dB，corr 0.99997" |

第 2 行是最有价值的一条：74.86 dB 这种"看起来还行但其实不达标"的结果，
工具会指出 **误差处处存在但 ≤ 0.19% RMS → 数值轴问题**，而不是让人去翻 RTL。

## 2. 形状分类的回归测试（`example/gen_demo.py`，无需板卡）

```
case                   expected class                 verdict
demo_zero_lines.raw    cache-line                     FAIL - small all-zero runs (len [8]) ... cache-line writeback
demo_1lsb.raw          LSB                            FAIL - only 1 LSB: rounding mode ...
demo_lag3.raw          lag (must PASS after align)    PASS (bit-exact)
demo_2d_dut.f32        every bin of every frame       FAIL - every bin of every frame: systematic ...
DEMO PASS
```

四条注入故障全部分类正确；这条测试同时是 `verdict_text()` 的回归保护
（我在开发中就被它抓到一个 bug：`bins_bad == bins_total` 在两者都是 `None` 时成立，
导致 1-D 比对被误判成"每个 bin 都错"）。

## 3. 资源/时序自动采集

```bash
python3 collect_metrics.py --vivado-dir fpga/report \
  --telemetry metrics/logs/board_c/board_final_telemetry.json \
              metrics/logs/board_c/board_nopitch_telemetry.json \
  --out metrics/resource_timing.csv --md metrics/resource_timing.md \
  --meta board=xc7z020clg400-2 --meta clock_mhz=100
```

产出 51 行 long-format CSV，抽出的数字与人工整理的报告**逐项一致**：

| 指标 | 综合 | 实现 |
|---|---|---|
| Slice LUTs | 9374 | 8378 |
| Slice Registers | 14506 | 13286 |
| Block RAM Tile | 5 | 5 |
| DSPs | 6 | 6 |
| WNS / WHS | +3.750 / +0.035 ns | +0.813 / +0.045 ns |
| failing endpoints | 0 | 0 |

同时从遥测 JSON 抽出 `rtf=2.0672`、`total_ms=8268.88`、`peak_out=1.36006`
（stage-1 那组，用于和 stage-2 对照）。

## 4. 已修正的工具缺陷（诚实记录）

| 缺陷 | 发现方式 | 修正 |
|---|---|---|
| `bins_bad == bins_total` 在 `None == None` 时误触发 | 真实数据跑 y16 时输出"every bin of every frame"，明显不对 | 增加 `rec.get("bins_total")` 存在性判断 |
| 时延对齐作用在 reshape 之后，2-D 输入会按帧切片 | 代码审查 | 先对齐再 reshape |
| `collect_metrics.py` 漏掉 `Slice LUTs*`（带星号行） | 综合表少一行 LUT | 正则改为 `[^|]+?` 并 strip `*` |
| failing endpoints 单位写成 ns | 输出检查 | 按 metric 名给 `count` |

## 5. 未覆盖

- 未接 CI（本地手动跑；`gen_demo.py` 已经可以直接当 CI 用例）。
- 未做统计显著性检验，只做逐样本/逐帧判定。
- 未处理"允许时延随时间漂移"的流式场景（见 README 失效条件）。
