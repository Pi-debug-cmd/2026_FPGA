# 提交前自查表（终版）

- 作品：VC-7020（Zynq-7020 固定目标音色转换），定版 **O64 + live + PL STFT**
- 检查人：提交自查（AI 辅助，人工复核）
- 时间：2026-10-27 13:40–15:10（Asia/Shanghai）；16:20 补正 PL 联测（见 §9.1、§10）
- 范围：**只做静态核对与文档修正**——不重跑训练、不重新综合/实现、不碰板卡、不改 `<workspace>` 的任何实验产物
- 依据：2026 AMD 赛题指南 §3.3（PDF 28 页，3.3 自 p22 起）

## 1. 结论

**7 项硬性自查全部通过，剩余 ✘ = 0。** 另有 **3 项"受限/未验证"**（不是缺陷，是纪律与素材边界），
在 §9 单列；原先列在此处的第 4 项"PL STFT 与 O64 live 未联测"已于 2026-10-27 实测关闭，
移入 §9.1「已验证」，避免"看起来全绿"的误读。

| # | 检查项 | 结论 | 一句话 |
|---|---|---|---|
| 1 | 目录/文件名全英文 | ✅ | 342 个文件、58 个目录，**非 ASCII 文件名 0 个**；大写仅 2 类合理例外 |
| 2 | 提交项齐全 | ✅ | README / docs / fpga(src·build·report) / host / metrics(csv·logs·scripts·evidence) / skill / ai_collaboration / report 全部在位 |
| 3 | 数字一致性 | ✅ | 六份主报告 **635 个小数**逐一回溯成功（1 个为千分位误报）；修正 8 处不一致 |
| 4 | 可复现性（静态） | ✅ | README 每一条路径/命令都可解析；4 条命令实跑通过（含 `resource_timing.csv` **51/51 行**复现） |
| 5 | 相对链接 | ✅ | 全文 **25 条**相对链接：**24 条可达**；1 条位于逐字节拷贝的历史报告内（已注明包内替代文件） |
| 6 | 2018.3 说明 | ✅ | `docs/toolchain.md` 新增 §1.1（三条技术理由）与 §6（四道复现锁 + 迁移顺序） |
| 7 | 本检查表 | ✅ | 本文件 |

---

## 2. 逐项：目录/文件名全英文

全量扫描（含隐藏文件、二进制、第三方源码）：

| 检查 | 结果 |
|---|---|
| 非 ASCII 文件名 | **0 / 342** |
| 含空格或 `<>:"\|?*` 的文件名 | **0** |
| 非 UTF-8 文本 | 3 个（`fpga/report/m3_compare_*.txt`，板端工具直出 UTF-16LE，**原样保留**，见 `metrics/logs/README.md` §4） |
| 大写文件名 | 仅 2 类（见下） |

**保留大写的两类，以及为什么不能改**：

| 类别 | 例子 | 理由 |
|---|---|---|
| 官方模板要求 | 各目录 `README.md` | 赛题指南把 `README.md` 写成固定名；改成 `readme.md` 反而不符合模板 |
| 第三方上游源码 | `AAFilter.cpp`、`LICENSE.txt`、`COPYING.TXT`、`Makefile`、`SyncAsync.vhd` | 被 `#include`、`Makefile` 与 LICENSE 条款引用；改名 → 编译失败 + 破坏 LGPL/BSD 归属声明 |

> 判定口径：**"全英文"= 路径只用 ASCII 可见字符**（这是会被自动扫描卡住的东西）。
> 大小写是风格问题，且与本表自身的 `SUBMISSION_CHECKLIST_FINAL.md`、官方的 `README.md` 一致。
> 结论写进 `metrics/README.md` §8，供评委复核。

---

## 3. 逐项：提交项齐全

| 要求项 | 位置 | 文件数 | 关键内容 | 结论 |
|---|---|---:|---|---|
| README | `README.md` | 1 | 简介 / 目录对照 / 从零复现 / 关键数字速览 / 缺口 | ✅ |
| docs | `docs/` | 4 | `architecture.md`、`interface.md`、`hardware_setup.md`、`toolchain.md` | ✅ |
| fpga/src | `fpga/src/` | 15 | `rtl/`（4 个 .v）、`bd/`（6 个 .tcl）、`constraints/`、比对脚本 | ✅ |
| fpga/build | `fpga/build/` | 9 | `.bit`/`.bin`/`.hdf`/swap(+gz)/`SHA256SUMS.txt`/`build_pl.ps1` | ✅ |
| fpga/report | `fpga/report/` | 16 | 综合/实现原始报告（util/timing/drc/clock/bus_skew）+ 资源时序表 + 2018.3 变更记录 | ✅ |
| fpga/stft（当前入链） | `fpga/stft/` | 71 | RTL、Tcl、位流、上板工具、原始报告、`PL_STFT_20261027.md` | ✅ |
| host | `host/` | 85 | `app/`（源码+构建+third_party）、`model/`（2 个 blob + 元数据）、`deploy/`（上板脚本+预编译工具） | ✅ |
| metrics | `metrics/` | 97 | `metrics.csv`(130 行)、`logs/`(65)、`scripts/`(13)、`evidence/`(3)、`inputs/`(2)、`reports/`(7) | ✅ |
| skill | `skill/` | 29 | 3 个 skill，各有 README + results + example + 可执行工具 | ✅ |
| ai_collaboration | `ai_collaboration/` | 9 | 6 个专题 + 28 轮索引（`prompt_log.csv` 29 行含表头）+ 94,536 B 原始附录 | ✅ |
| report | `report/` | 8 | 设计报告、失败分析、O64 上板报告、**PL 联测摘要**、过程版自查、CHANGELOG、SANITIZE、**本表** | ✅ |

> 顺带修掉的计数错误：README 与 `metrics/README.md` 都把 `metrics.csv` 写成"66 行"（实际 **110 行**）；
> README 把日志目录写成"board_c 15 个 + pl_build 19 个"（实际 **22 + 8 + 15 + 19**）。

---

## 4. 逐项：数字一致性

### 4.1 方法（可重跑）

1. 把 `metrics/logs/`（65 个）、`metrics/reports/`（7 个）、`fpga/`（含两份 Vivado 原始报告）
   以及 `metrics.csv`/`resource_timing.csv` 里出现过的所有数字建成索引；
2. 抽取六份主报告（README、design_report、failure_analysis、o64_onboard、O64_LIVE、STABILITY）
   里**全部两位以上小数**，逐个到索引里找；
3. 整数（含千分位）同法再查一遍，剩余项人工判读。

### 4.2 结果

| 检查 | 数量 | 未匹配 |
|---|---:|---:|
| 小数（≥2 位） | 635 | **0**（1 条为 `20,909.50` 被正则截成 `909.50` 的误报） |
| 整数（3–5 位或千分位） | — | 8 条，逐条判读后**全部为误报或可外部核验**（见下） |

8 条整数"未匹配"的判读：

| 报告位置 | 数字 | 判读 |
|---|---|---|
| `O64_LIVE_20261027.md` §10 | 759,084 B | 文件大小，`board_o64live_full.wav` 实际 759,084 B ✔ |
| `STABILITY_20261026.md` | 300,200,233.00 | CSV 行文本被拼读，非单一数字 |
| `STABILITY_20261026.md` | 34000 | **建议值**（"把 out_gain_q16 从 39322 降到 ~34000"），非实测 |
| `STABILITY_20261026.md` | 6001 | `blocks.jsonl` 行数，实测 **6001** 行（6000 块 + summary）✔ |
| `failure_analysis.md` F13 | 100,200,300 | 文件名通配 `scores_step{100,200,300}k.json` |
| `o64_onboard_20261026.md` §2 | 64,513 | 张量形状 `dct_out=(64,513)` |
| `o64_onboard_20261026.md` §5 | 1,518,080 B | `male04_16k.f32` 大小（=379,520×4）✔ |
| `o64_onboard_20261026.md` §6 | 102,656 B | `401×64×4` ✔ |

### 4.3 关键数字 → 来源（评委最常查的 14 个）

| 数字 | 含义 | 主来源（包内路径） |
|---|---|---|
| **0.8602 / 0.8595 / 0.8611** | O64 live 4 s RTF ×3 | `metrics/logs/o64_live_20261027/rtf4_{1,2,3}.json` |
| **284.8 ms** | 300 ms 块处理 p99（60 s/200 块） | `metrics/logs/o64_live_20261027/lat300_blocks.csv` + `lat300_summary.json` |
| **584.8 ms** | 端到端 p99（= 300 + 284.8） | `metrics/O64_LIVE_20261027.md` §4（派生行） |
| **6000/6000、0 欠载** | O64 live 30 min | `metrics/logs/o64_live_20261027/blocks.jsonl`（6001 行）、`aplay.log` |
| **8,408 KB 恒定** | O64 live 30 min RSS | `metrics/logs/o64_live_20261027/mem.csv` |
| **10,501 / 21,473** | 30 min 削波（O64 / T4） | `metrics/logs/o64_live_20261027/blocks.jsonl` 末尾 summary、`stability_20261026/blocks.jsonl` |
| **0.7321 / 0.7006 / −0.0346 / 2.1900** | O64 live 四指标 | `metrics/logs/o64_live_20261027/score_board_o64live_full.json` |
| **0.7293 / 2.2659 / −0.0223** | O64 精确档四指标 | `metrics/logs/board_c/o64_scores_full.json` |
| **0.999999987 / 75.71 dB** | 板端 vs Python O64 | `metrics/logs/board_c/o64_board_vs_pyref.json` |
| **16,723 / 28,677 / 22 / 76** | STFT 版实现资源 | `fpga/stft/report/impl_utilization.txt` |
| **+0.347 / +0.040 / 0 failing** | STFT 版 WNS/WHS | `fpga/stft/report/impl_timing.txt` |
| **corr 0.99999999 / 4 LSB / 0.60 LSB** | PL STFT vs 全 ARM | `fpga/stft/PL_STFT_20261027.md` §5（`tools/compare_e2e.py` 产出） |
| **449.04 → 305.82 ms、0.9376 → 0.9019** | STFT 段 / 整链 RTF | 同上 §5.1 |
| **0.8237 / 451.3→309.5 ms / 274.8 ms / 0 欠载** | PL + O64 + live 整链（联测） | `report/PL_IN_LOOP_20261027.md`（源 `board_final_20261027\CURRENT_STATE.md` §4/§5） |
| **121.71 / 126.16 / 139.38 dB** | C↔Python / 板端 32 kHz / ARM↔x86 | `metrics/reports/board_c_20261025.md` §8.2 + `metrics/logs/board_c/` |

> 另外：`metrics.csv` 的 **110 行 `source` 全部改成"相对参赛包根目录"的可打开路径**
> （原先 48 行指向包里不存在的文件名，8 行是 `stab30_20261026` 这类非文件标识）。
> 6 份被引用但没入包的报告已**逐字节拷贝**进 `metrics/reports/`（含 SHA），见该目录 README。

### 4.4 本次因一致性而改的数字/表述

| 位置 | 原 | 改 | 依据 |
|---|---|---|---|
| README、`metrics/README.md` | `metrics.csv` 66 行 | **110 行** | 实测行数 |
| README | `board_c/`（15 个）+ `pl_build/`（19 个） | **22 + 8 + 15 + 19** | 目录实测 |
| `design_report.md` §5.1 | `vc_stream.cpp` 1652 行 | **1661 行** | `wc -l` |
| `design_report.md` §6.1 | 引用 `O64_ONBOARD_REPORT.md` | **`report/o64_onboard_20261026.md`** | 包内真实文件名 |
| `O64_LIVE_20261027.md` §10 | `o64_20261026/O64_ONBOARD_REPORT.md` | **`../report/o64_onboard_20261026.md`** | 同上 |
| `failure_analysis.md` F9、`ai_collaboration/03` | `int8_latency.md` | **`board_c_20261025_int8_latency.md`** | 真实文件名 |
| `design_report.md` §6.3 | 默认档 0.6369/2.1040 与 §6.4 的 0.6373/2.1045 未说明 | 加脚注：两次独立评分、**不互相修正** | `scores_L5.json` vs `scores_cer.json` |

---

## 5. 逐项：可复现性（只做静态核对，未跑 Vivado）

### 5.1 实跑通过的四条（今天真跑了）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `python skill\golden_reference_compare\collect_metrics.py --vivado-dir fpga\stft\report --out …` | 34 行；**16,723 / 28,677 / 22 / 76、WNS +0.347 全部一致** |
| 2 | 同上 `--vivado-dir fpga\report` + 2 份遥测 + 3 个 `--meta`（`metrics/README.md` §4 的完整命令） | **51 行与 `resource_timing.csv` 逐字段相同** |
| 3 | `python skill\golden_reference_compare\example\gen_demo.py` | **DEMO PASS**（4 个用例判定全对） |
| 4 | `python metrics\scripts\csv_to_md.py metrics.csv summary.md` | 8 个 section / 130 行，**与提交的 `summary.md` 完全一致** |

### 5.2 README 命令逐条静态核对

| README 小节 | 命令/路径 | 结论 |
|---|---|---|
| §3.1 | `collect_metrics.py`、`gen_demo.py`、`report\design_report.md`、`metrics\summary.md` | ✅ 全部存在（且前两条实跑） |
| §3.2 | `host\app\build_arm.ps1`、`build_host.ps1`、`build\vc_stream_host.exe` | ✅ 脚本存在；`.exe` 由脚本生成（未随包发，属正常） |
| §3.2 | 自检命令的**当前目录** | ⚠️→✅ 已补 `cd D:\competition_pkg_20261026`（原文档紧跟 `cd host\app`，会找不到相对路径） |
| §3.3 | `fpga\build\build_pl.ps1 -Work D:\pl_try` | ✅ 脚本确有 `-Work` 参数；默认 Vivado 路径不存在时会**明确报错**并提示改参 |
| §3.4 | `stage.ps1`、`deploy_all.ps1`、`tools\*`、`D:\vc_stage_20261026` | ✅ `stage.ps1` 默认就是该目录，`tools\` 由它创建 |
| §3.5 | `audio_pitch_dma_2018_swap.bin.gz`、`prepare_recovery.py`、`load_pl_2018.py`、`regtool` | ✅ 都在包内/由 `stage.ps1` 铺好 |
| §3.5 | `compare_reference.py work\input16_mono.raw` | ⚠️→✅ `work\` 并不存在，已改为 `<回读目录>` 占位（该步需要板端回读的 dump） |
| §3.6 | `score_full.py`、`metrics\inputs\test_src_16k.wav` | ✅ 脚本在；语料不随包（见 §6 限制 2） |

### 5.3 绝对路径依赖：逐个处理

| 文件 | 原状态 | 处理 |
|---|---|---|
| `host/app/build_arm.ps1` | 写死 `D:\Vivado\SDK\2018.3\…\bin` | 改为 `-GccDir` / `$env:FVC_GCC_DIR`，默认值保留但**找不到就报错并给出两种改法** |
| `host/app/build_host.ps1` | 写死 `…\msys64\mingw64\bin\g++.exe` | 改为 `-Cxx` / `$env:FVC_HOST_CXX`，报错提示"任意 mingw g++ 7+ 均可" |
| `fpga/stft/tools/ref_chain.py` | 写死研发目录的输入/输出 | 改为 `FVC_DUMP_DIR` / `FVC_WORK_DIR`，缺目录时**说明需要哪四个 dump** |
| `fpga/build/build_pl.ps1` | 已有 `-Vivado`，但无 `-Work` 说明 | 已有 `-Work`；`Test-Path` 失败会 `throw`（无需改） |
| `metrics/scripts/evaluator.py` | 有 `FVC_ASSETS` 环境变量 + 旧工程兜底 | 保留（兜底不改变行为），在 README §3.6 写清"评测权重不随包" |

> 仍保留 `D:\` 的地方只有三类，都是**有意的**：① Vivado/Vitis 安装路径（工具在哪是事实，
> 且都可参数覆盖）；② 研发目录的溯源引用（"这份权重来自 `…\O64.pt`"，明确标注不在包内）；
> ③ `metrics/reports/` 里 6 份**逐字节拷贝**的历史报告（改了就破坏 SHA 可核）。

### 5.4 明确"不保证"的

- **位流 SHA 不保证重编一致**：place & route 非位级可复现。承诺的是"资源/时序可复现到几个百分点"
  与"功能逐样本可复现"，`docs/toolchain.md` §6 已写清。
- **Vivado 重建未实跑**（按本次纪律"不跑 Vivado"）：脚本、Tcl、原始报告齐备，但没有在今天验证
  一次端到端 15–25 min 的重建。

---

## 6. 逐项：相对链接

| 检查 | 结果 |
|---|---|
| Markdown 相对链接总数 | 25 |
| 可达 | **24**（本次新增的 `checklist_submission.md → SUBMISSION_CHECKLIST_FINAL.md` 指向本文件，已随本文件成立） |
| 不可达 | **1**，且是**有意的**：`metrics/reports/board_c_20261025_stage2.md` 里的 `out/score/stage2_compare.png`。该目录是逐字节拷贝（改了就破坏 SHA 可核），包内对应图为 `metrics/evidence/stage2_compare.png`，已在 `metrics/reports/README.md` 写明 |
| 外部 URL | 0（本包不依赖外网） |

---

## 7. 逐项：2018.3 说明（`docs/toolchain.md`）

本次新增 / 强化：

| 小节 | 内容 | 回答的问题 |
|---|---|---|
| §1 | 三条原因表（唯一完整安装 / 风险权衡 / 结论） | **为什么是 2018.3** |
| §1.1（新增） | 三条**可核对**的技术理由：无 `write_hw_platform`；`axi_iic` 只有 2.0；位流头带版本与器件 | 不是"懒得升级" |
| §2 | 10 个 IP 的 VLNV 逐个核对表 + `write_hwdef/write_sysdef` + 位流大小端 | **差异在哪、怎么处理** |
| §3 | 构建命令（4 条 Tcl + make_swap），全部入库 | **怎么重建** |
| §5 | 复现性核对表（含 **STFT 版** 6 个产物的字节数/SHA） | **怎么核** |
| §6（新增） | **四道复现锁**：脚本参数化 / IP 版本 / 原始报告可重抽取 / 位流 SHA；外加"位流不保证位级可复现"的说明与**2026.1 迁移顺序（5 步）** | **如何保证复现** |

---

## 8. 逐项：打包

| 项 | 值 |
|---|---|
| 包内文件数 | **342**（含本表与 `MANIFEST.md`；本轮新增 `report/PL_IN_LOOP_20261027.md`） |
| 包总大小 | **约 51.2 MB（48.8 MiB）**；逐字节值以 `MANIFEST.md` §1 为准 |
| 单文件 > 100 MB | **0**（最大 `student_v5_o64.blob` 4.94 MB） |
| MANIFEST | `MANIFEST.md`（文件数/体积/各目录计数/关键产物 SHA256/排除项） |
| 压缩包 | `D:\competition_submit_20261027.rar`（RAR5，`-r -m5 -ep1 -idq`；内含 **340** 个文件） |
| 压缩包布局 | `-ep1` 去掉顶层目录名：解压后 `README.md`、`report/`、`host/` … 直接展开；要还原成 `competition_pkg_20261026/` 就解压到同名目录 |
| 排除项 | 真人源录音 2 个：`metrics/inputs/test_src_16k.wav`、`metrics/inputs/test_src_32k_s24.raw`（各一条 `-x`） |
| 排除后仍可做 | 资源/时序重抽取、比对工具回归、PS 重建、PL 位流重建、全部指标与日志核对 |
| 排除后不可直接做 | §3.2/§3.4 板级自检（可用任意 4 s/32 kHz/S24 输入替代）、§3.6 四指标复算（本就需自备语料） |

---

## 9. 未完成 / 受限（3 条，不计为 ✘）

| # | 项 | 为什么没做 | 影响 / 兜底 |
|---|---|---|---|
| 1 | **Vivado 端到端重建** | 本次纪律明确"只做静态核对，不要真跑 Vivado"（重建 15–25 min 且会占用机器） | 脚本/Tcl/原始报告齐备；资源与时序已用 `collect_metrics.py` 从原始报告**重抽取并逐字段核对** |
| 2 | **四指标复算** | 需 WeSpeaker/UTMOS/whisper 权重 + 目标女声/男性语料（含真人语音），均不随包分发 | 本包提供全部**既有**评分 JSON（含 `hyp` 转写原文），可逐项核对；`score_full.py` 缺资产会明确报路径 |
| 3 | **压缩包不含测试输入** | 按"排除任何真人音频"的提交要求剔除 | 包目录内保留；README §3.0 已写明替代输入的要求与不变的判据 |

另有两项**设计层缺口**（不是自查项，但已如实记录）：人工盲测未做；温升未采集。

### 9.1 原"受限"第 4 条已关闭：PL STFT + O64 live 已联测（2026-10-27）

| 项 | 结论 |
|---|---|
| 配置 | `vc_pl_dbg3`（sha `40dc1375…`）+ `student_v5_o64.blob`（O64）+ `--preset live` + **PL STFT v5 位流参与**（`pl_stft=1`；位流 sha `d597cb0a…`，与主机 `stft_dma_swap.bin` 逐字节相同） |
| RTF | 4 s **0.8237**（0.8237 / 0.8238 / 0.8235）；23.72 s 整段 **0.8396**；60 s 流式总 **0.8555**（纯 ARM 对照 0.8602 / 0.8910） |
| STFT 段 | **451.3 → 309.5 ms**（−142 ms，同二进制 `VC_PL=0` 对照）；PL DMA 往返 75.6 ms |
| 延迟（60 s / 200 块，300 ms 块） | 处理 p50 266.0 / **p99 274.8** / max 275.0 ms；端到端 p50 566 / **p99 574.8** / max 575 ms；**欠载 0** |
| 四项（23.72 s，score_full） | identity **0.7324** / P10 **0.6903** / 泄漏 **−0.0343** / UTMOS **2.1532**（仍差 2.30 门禁）/ CER 相对 **−0.0250**；clipped 0 |
| 来源 | `board_final_20261027\CURRENT_STATE.md` §3–§6（板端一次性确认记录）；包内摘要 `report/PL_IN_LOOP_20261027.md` |
| 安全提示 | 旧 `vc_o64_pl`（04:25）与 v5 位流**不兼容**（输出 ×32768、123991/128000 样本削顶），**不得用于取数** |

> 已就地更正的说法：`design_report.md` §8 #12、`README.md` §5、`checklist_submission.md` §4 里
> 原先的"未联测 / live+PL 的 RTF 不能外推"；`design_report.md` 另新增 §6.8a 记录整链实测。

---

## 10. 本次改动清单

| 文件 | 改动 |
|---|---|
| `report/failure_analysis.md` | 新增 **F13**（GAN 声码器，8 行 + 4 行表）、总览表加 1 行、F4 与 §4 各加 1 处交叉引用 |
| `report/SUBMISSION_CHECKLIST_FINAL.md` | **本文件（新增）** |
| `MANIFEST.md` | **新增**（文件数/体积/目录计数/SHA/排除项） |
| `metrics/reports/` | **新增 7 个文件**：6 份源报告逐字节拷贝 + `README.md`（索引与 SHA） |
| `metrics/metrics.csv` | 110 行 `source` 改为包根相对、可打开路径 |
| `metrics/summary.md` | 由 `csv_to_md.py` 重新生成（与 CSV 一致） |
| `metrics/README.md` | 66→110 行、补 `reports/`、补 §4 复现命令的 `--meta tool` 与"51/51 行"复核记录、新增 §8（命名/编码例外） |
| `metrics/logs/README.md` | 新增 UTF-16LE 说明（`m3_compare_*.txt`） |
| `metrics/O64_LIVE_20261027.md` | 修 `O64_ONBOARD_REPORT.md` 死引用 |
| `report/design_report.md` | 1652→1661 行、修 §6.1 引用、§6.3 加来源脚注（0.6369/2.1040 vs 0.6373/2.1045） |
| `report/checklist_submission.md` | 顶部加"以终版为准"横幅；215→332 文件；两处过期结论就地标注 |
| `report/CHANGELOG_20261027.md` | 追加 3 行"提交前自查（第二版）" |
| `docs/toolchain.md` | 新增 §1.1（三条技术理由）、§5 表补 STFT 产物、新增 §6（四道复现锁 + 2026.1 迁移顺序） |
| `README.md` | 66→110 行、日志计数、目录树补 `MANIFEST.md`/`metrics/reports/`、§3.1 改为抽取 STFT 报告并给出期望值、§3.2 补 `cd <包根>`、§3.5 去掉不存在的 `work\` 路径、§3.6 写清资产/语料缺失、§7 修正"真人语音"表述 |
| `host/app/build_arm.ps1`、`build_host.ps1` | 编译器路径改为参数/环境变量 + 明确报错 |
| `fpga/stft/tools/ref_chain.py` | 研发目录硬编码改为 `FVC_DUMP_DIR`/`FVC_WORK_DIR` + 缺目录说明 |
| `ai_collaboration/03_performance_optimization.md` | 修 `int8_latency.md` 文件名 |

### 10.1 2026-10-27 16:20 补正：PL 联测（本轮只改文档与打包）

| 文件 | 改动 |
|---|---|
| `report/PL_IN_LOOP_20261027.md` | **新增**（19 行）：配置 / RTF / 延迟 / 分段 / 四项 / 旧二进制不兼容警告 |
| `report/design_report.md` | 新增 **§6.8a**（PL 参与下的整链实测）；§6.1 改为"已补联测"；§8 #11/#12 由"未联测"改为"已联测"给数字；§10 结论删"没做到：PL 联测" |
| `report/failure_analysis.md` | §4 第 4 项与 §5"仍没做"改为已联测 + 数字；补 `vc_o64_pl` 不兼容警告 |
| `report/SUBMISSION_CHECKLIST_FINAL.md` | §9 由 4 条降为 3 条、原第 4 条移入 §9.1「已验证」；§1–§5、§8、§10 计数同步 |
| `report/checklist_submission.md` | §4 "还没联测——最大短板"改为已联测（给数字） |
| `metrics/metrics.csv` | **新增 20 行** `pl_in_loop_o64_live*`（RTF / 分段 / 延迟 / 欠载 / 四项），`source` = `board_final_20261027\CURRENT_STATE.md`；110 → **130 行** |
| `metrics/summary.md` | 由 `csv_to_md.py` 重生成（8 section / 130 行） |
| `metrics/README.md` | 110 → 130 行；§1 补"source 例外"（PL 联测行的来源在研发目录）；§3 补 PL 联测 |
| `README.md` | §4 速览加"O64 + live + PL STFT（联测）"行；§5 第 5 条改为已联测（删"不能外推 RTF"）；130 行 |
| `MANIFEST.md` | 全量重算（342 文件 / 新报告 / SHA）；§4 压缩包改为 RAR |
| 打包 | PDF 由 Edge 无头重打（附录 A 随 CSV 变 130 行）；RAR 重打并剔除 2 个真人源录音 |

---

## 11. 评委复核用最短路径（3 条命令）

```powershell
cd D:\competition_pkg_20261026
# ① 资源/时序：从 Vivado 原始报告重抽，应与报告一致
python skill\golden_reference_compare\collect_metrics.py --vivado-dir fpga\stft\report --out check.csv
# ② 比对工具自检
python skill\golden_reference_compare\example\gen_demo.py      # 期望 DEMO PASS
# ③ 任一数字的出处：例如 UTMOS 2.1900 / identity 0.7321 / 泄漏 −0.0346
Select-String -Path metrics\logs\o64_live_20261027\score_board_o64live_full.json -Pattern "2.19|0.7321|-0.0346"
```
