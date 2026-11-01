# metrics — 全部实测数据（可追溯）

## 1. 文件

| 文件 | 内容 | 生成方式 |
|---|---|---|
| **`metrics.csv`** | 汇总表：130 行，覆盖延迟/RTF/吞吐/资源/时序/质量/一致性/稳定性 | **手写**，每行带 `source`（**相对参赛包根目录**的路径） |
| `summary.md` | 上面这张表的可读版（按 section 分表） | `scripts/csv_to_md.py` 自动生成（2026-10-27 重生成，130 行） |
| `resource_timing.csv` | 资源与时序的 long-format 抽取（51 行） | `skill/golden_reference_compare/collect_metrics.py` 从 `fpga/report/*.txt` 自动抽取 |
| `resource_timing.md` | 同上，可读版 | 同上 + `csv_to_md.py` |
| `reports/` | `metrics.csv` 引用的 6 份分析报告（**原样拷贝**，含 SHA） | 见 `reports/README.md`，补上溯源链 |
| `logs/` | 原始日志（编译/上传/加载/DMA/比对/遥测） | 原样拷贝，未编辑 |
| `scripts/` | 测试与采集脚本 | 见 §4 |
| `inputs/` | 固定测试输入（4 s） | 原样拷贝 |
| `evidence/` | 图（语谱图对照、波形总览） | 原样拷贝 |

> 例外（`source` 不在包内）：`pl_in_loop_o64_live*` 这组行引自板端一次性确认记录
> `board_final_20261027\CURRENT_STATE.md`（研发目录，不随包）；包内摘要与逐项出处见
> [`report/PL_IN_LOOP_20261027.md`](../report/PL_IN_LOOP_20261027.md)。

## 2. `metrics.csv` 的列约定

| 列 | 含义 |
|---|---|
| `section` | latency / rtf / throughput / resources / timing / quality / consistency / stability |
| `config` | 哪个配置/档位（default_batch_4s、live_stream_300、board_stage2_e …） |
| `metric` | 指标名 |
| `value` / `unit` | 数值与单位（`N/A` 表示未测，不是 0） |
| `hardware` | 硬件型号（`xc7z020clg400-2` 或 `x86 host`） |
| `tool` | 软件版本 |
| `clock_mhz` | FPGA/被测时钟（PL 100 MHz；主机侧为 0） |
| `runs` | 测试次数 |
| `sample_duration_s` | 单次时长 |
| `source` | **落点**：哪个报告/日志文件（**相对参赛包根目录**，如 `metrics/reports/board_c_20261025.md 8.2`） |
| `status` | `measured` / `derived`（由公式推出）/ `not_measured` |
| `note` | 备注（含"门禁未过"这类必须写的话） |

**规矩**：`status=not_measured` 的行不允许删，也不允许填一个估计值。
评审看到 `N/A` 时应该能立刻知道这是缺口而不是 0。

## 3. 已测 / 未测（一眼看清）

| 类别 | 已测 | 未测 |
|---|---|---|
| 延迟 | 结构性延迟（B+proc）、4 s 批处理总耗时（3 次）、**300 ms 块逐块分布 p50/p95/p99/max（60 s / 200 块；含 O64 live 与 PL 联测两组）** | 温升 |
| RTF | 6 个档位（L0–L5）、O64 精确档/live 档/**live + PL STFT**、PL 核、主机侧 | — |
| 资源/时序 | LUT/FF/BRAM/DSP/IOB、WNS/WHS/WPWS、DRC | — |
| 质量 | identity / P10 / 泄漏 / UTMOS / CER（5 个版本，含 PL 联测） | 人工盲测、多人泛化 |
| 一致性 | C↔Python 121.71/126.16 dB、ARM↔x86 139.38 dB、PL bit-exact | — |
| 稳定性 | 3 次批处理 ±0.1%、300 ms 块 0 欠载×3、**30 min 实测 0 欠载（6000 块）** | 连续 1 h 以上 |

## 4. 脚本

| 脚本 | 作用 |
|---|---|
| `scripts/score_full.py` | 五项门禁评分（identity/P10/泄漏相对基线/UTMOS/CER），原来在仓库 `scripts/` |
| `scripts/evaluator.py` | 上述脚本依赖的评测器封装（WeSpeaker / UTMOS / whisper） |
| `scripts/compare_stages.py` | C 与 Python oracle 的逐阶段误差表 |
| `scripts/analyze_board.py` | 板端输出校验（S24 解码、包络域对比、导出 WAV） |
| `scripts/score_variants.py` | 一次进程内给多个变体打分 |
| `scripts/csv_to_md.py` | long-format CSV → markdown |
| `scripts/measure_latency.sh` | **板端**：逐块 `proc_ms` 分布 → p50/p95/p99（补上 §3 的缺口） |

### 怎么补上 p50/p95/p99（2026-10-26 已补）

```sh
# 板上 /tmp/vc（先把 4 s 的 in.raw 和 vc_live 传上去）
sh measure_latency.sh 300 60 in.raw lat_300.csv
# 输出: block_ms,blocks,proc_min_ms,proc_p50_ms,proc_p95_ms,proc_p99_ms,proc_max_ms,...
# 然后把 lat_300.csv 的数字填进 metrics.csv 里现在写 N/A 的三行，status 改 measured
```

实际结果（`logs/stability_20261026/lat_300_fix.csv`）：
**p50 268.70 / p95 276.70 / p99 277.90 / max 278.10 ms**（200 块，纯处理口径）。

> 注意：原脚本把 `vc_live` 打印的**累计** `proc_ms` 当作每块耗时，第一次跑出来
> p50=26 s。修正版（本目录 `scripts/measure_latency.sh`）改为取一阶差分并加自检；
> 原版留档为 `scripts/measure_latency.sh.orig`，说明见
> `scripts/CHANGES_measure_latency_20261026.md`。
> 30 min 长稳的完整报告见 `STABILITY_20261026.md`。

### 怎么重生成 `resource_timing.csv`

```bash
python3 ../skill/golden_reference_compare/collect_metrics.py \
  --vivado-dir ../fpga/report \
  --telemetry logs/board_c/board_final_telemetry.json \
              logs/board_c/board_nopitch_telemetry.json \
  --out resource_timing.csv --md resource_timing.md \
  --meta board=xc7z020clg400-2 --meta clock_mhz=100 --meta "tool=Vivado 2018.3"
```

> 2026-10-27 复核：上面这条命令在 Windows + Python 3.14 上重跑，产出与本包
> `resource_timing.csv` **51/51 行逐字段相同**（只差换行符风格），
> 说明"资源/时序数字可自动重抽取"不是口号。
> 若只想核对 STFT 版（当前入链的 `fpga/stft/`），把 `--vivado-dir` 换成
> `../fpga/stft/report`，会得到 16,723 LUT / 28,677 FF / 22 BRAM / 76 DSP、WNS +0.347 ns。

## 5. 日志索引

见 `logs/README.md`。要点：

- `logs/board_c/`：板端运行与遥测（`board_final_telemetry.json` 是 stage-1 的完整分阶段耗时；
  `board_run_*.log` 是完整会话；`scores_*.json` 是四指标原始输出）。
- `logs/pl_build/`：Vivado 建工程/综合/实现日志 + 上板加载/DMA/比对日志。
  其中 `create2_2018_3.log` 是一次**失败**（GPIO 时钟未接），保留作为证据。

## 6. 图的说明（`evidence/`）

| 文件 | 内容 |
|---|---|
| `stage2_compare.png` | 电脑端 T4 / 板端 stage-1 / stage-2 的波形+语谱图三联对照（同一条 4 s） |
| `board_run_overview.png` | 板端整链的输入/输出波形与语谱图 |

这两张图是**唯一**的图像证据；资源与时序没有截图，全部用原始文本报告（`fpga/report/`），
比截图更可核。

## 7. 2026-10-27 新增

| 文件 | 内容 |
|---|---|
| `O64_LIVE_20261027.md` | O64 + `--preset live` 的 RTF / 延迟分位 / 四指标 / 30 min 长稳（**演示定版**） |
| `logs/o64_live_20261027/` | 上述结论的原始遥测、逐块 `proc_ms`、`score_full.py` 输出与板端 wav |
| `metrics.csv`（新增 29 行） | `o64_live_*`：RTF 0.860、p99 284.8 ms、UTMOS 2.1900；`pl_stft_*`：449→305.82 ms、RTF 0.9376→0.9019、16,723 LUT/22 BRAM/76 DSP、WNS +0.347 |
| `../fpga/stft/` | PL STFT 位流、Tcl、RTL、实现报告与原始 `PL_STFT_20261027.md` |

---

## 8. 命名与编码：已知例外（全量扫描结果）

2026-10-27 对 332 个文件做了全量扫描：

- **非 ASCII 文件名：0 个**。目录名与文件名全部是 ASCII 可见字符，中文只出现在正文。
- **大写文件名**：仅两类，都是有理由的保留——
  1. 官方模板要求的大写 `README.md`（每个目录一份）；
  2. `host/app/third_party/` 下的第三方源码（`AAFilter.cpp`、`LICENSE.txt`、`Makefile`、
     `SyncAsync.vhd` 等）。这些名字被 `#include`、`Makefile` 与 LICENSE 条款引用，
     **改名会直接编译不过、并且破坏 LGPL/BSD 的归属声明**，所以按上游原名保留。
- **非 UTF-8 文本**：仅 `fpga/report/m3_compare_*.txt`（3 个）是板端工具直出的 UTF-16LE，
  原样保留，说明见 `logs/README.md` §4。
- **0 字节文件**：`logs/board_c/build_host.log`（构建无输出即成功，保留为空文件以证明"跑过"）。
