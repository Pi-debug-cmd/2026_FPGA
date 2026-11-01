# reports — 被引用的分析报告（原样拷贝）

本目录是 `metrics/metrics.csv`、`report/design_report.md`、`report/failure_analysis.md`
里**按名字引用**的 6 份分析报告的**逐字节拷贝**，目的是让每个数字都能顺藤摸到出处，
而不是引用一份"包里没有"的文件。

| 文件 | 字节 | 内容 | 谁在引用 |
|---|---:|---|---|
| `board_c_20261025.md` | 27,816 | stage-1 全程：RTF 2.067→0.972、逐阶段耗时、一致性 121.71/126.16/139.38 dB、74.86 dB 的澄清、3 次 ±0.1% | `metrics.csv`（10.1/8.1/8.2）、`failure_analysis.md` F1/F7、`README.md` §4 |
| `board_c_20261025_stage2.md` | 15,319 | stage-2 压缩档：3857–3941 ms、D4C 隔帧、第二遍 WORLD 并行 | `metrics.csv`、`design_report.md` §6.1、`failure_analysis.md` F8 |
| `board_c_20261025_squeeze.md` | 6,870 | L0–L5 六档 RTF（0.972/0.950/0.931/0.885/0.865/0.845）、300/500 ms 块的欠载 | `metrics.csv`（12 行）、`README.md` §4 |
| `board_c_20261025_int8_latency.md` | 7,583 | underrun 归因与 §0 的公开自我更正（"先更正我上轮的错误结论"） | `failure_analysis.md` F2/F9、`ai_collaboration/03_performance_optimization.md` |
| `pl_build_20261025.md` | 23,114 | 变调核：4.10 M 样本/s、RTF 0.0078、chunk 117.7–118.6 µs、bit-exact 三个比例 | `metrics.csv`（6 行）、`README.md` §4 |
| `FEASIBILITY.md` | 38,141 | 前人 RTL 的复核（cos/sin 查表漏 frac，49248 bin 全失配）与可行性边界 | `failure_analysis.md` F10、`ai_collaboration/04_numerics_and_board.md` |

SHA-256（拷贝件与研发目录原件一致，见 `MANIFEST.md`）：

```
73e5ce958616128b6210294cb868eb4ee3963b7943eee7daeed138e3756d7303  board_c_20261025.md
2bd0996f74f03ab7c9cf976ba86fade2c223ee4b16d04d787cdd851f13bb7962  board_c_20261025_stage2.md
e587e64b24b775095ce02d2e7a8e138792099c363f6628309fa8040f69653a0b  board_c_20261025_squeeze.md
1ab561c4114e25f73c829044d9ddcb064b5cd11e881a8f0dabfa9a0c370dbae9  board_c_20261025_int8_latency.md
47bab0ac670a37afbafc455318f4324aa55b21891a868bd5b34a02d502477a1b  pl_build_20261025.md
2c0720df33922235536205b9fae538d011c29a05c82761da325b956994a1b001  FEASIBILITY.md
```

## 怎么用

1. `metrics/metrics.csv` 的 `source` 列现在是**相对参赛包根目录**的路径，直接照着打开即可
   （`metrics/reports/board_c_20261025.md 8.2` = 该文件 §8.2）。
2. 想核某个数字：先在 `metrics.csv` 找行 → 打开 `source` → 在该报告里找对应小节；
   报告里每个数字又指向 `metrics/logs/` 下的原始日志或 `fpga/report/` 的 Vivado 原始文本。
3. 这几份是**历史分析报告**，写作时的目录结构与现在略有不同（例如当时 `O64` 还没定版、
   `report/` 还不存在）。**只当作溯源材料读，不要当作当前结论读**；
   当前结论以 `README.md`、`report/design_report.md`、`report/failure_analysis.md` 为准。

> 这些报告含研发过程的原始措辞（包括已被推翻的中间判断），保留原文是为了可信度，
> 不做"事后美化"。`board_c_20261025_int8_latency.md` §0 就是一次公开的自我更正。

## 拷贝件内部的链接为什么可能有"死链"

为了 SHA 可核，拷贝**逐字节未改**，因此报告里指向研发目录的相对链接（例如
`board_c_20261025_stage2.md` 里的 `out/score/stage2_compare.png`）在包内不解析。
对应的图**在本包里有一份**：`metrics/evidence/stage2_compare.png`。
除此之外，`metrics.csv` 用到的 `source` 全部是包内可打开的真实路径（2026-10-27 校验 110/110）。
