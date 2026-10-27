# 2026-10-27 增量修订

## 2026-10-27 提交门户格式适配 + 敏感信息清洗（本次）

- 新增 **`report/SANITIZE_20261027.md`**：全包 341 文件 / 311 文本文件逐类扫描（学校、教师、队员、学号、邮箱、手机号、`C:\Users`、研究目录、GitHub 实名）+ 二进制字节级扫描 + WAV/PNG 元数据核查。
- **身份类信息 0 项**（逐类 0 命中）；实际处理 **28 处**：本机路径占位化 21 处（个人研究目录、本机工具目录 → `<workspace>` / `<tools>`）、个人称谓泛化 7 处（指向具体个人的称呼 → 链路/组织描述），涉及 **14 个文件**。
- 原始日志（`metrics/logs/` 24 处同类路径）**有意保留**，理由与可选脱敏命令见 SANITIZE §5。
- 因文档字节变化，重算 **`MANIFEST.md`**（总量 + 各目录 + 3 个关键 SHA256）与 **`fpga/stft/SHA256SUMS.txt`**（3 行），文件数变化仅 `+1`（本记录）。
- 交付件 `D:\competition_submit_20261027\tech_report.pdf`：26 页 / 2.08 MiB / Edge 无头打印；封面（作品名+日期，无单位与姓名）→ 目录（55 条带页码，漂移 0）→ 设计报告 → 失败分析 → 附录 A 指标汇总表（130 行，与 `metrics.csv` 一一对应）；中文可检索（7,725 汉字）。

- 定版改 **O64**（64 阶 / 1,152,064 参数 / blob 4,941,804 B）：板端 identity 0.7293、UTMOS 2.2659、字错 0.1538（4 s）；与 Python O64 corr 0.999999987 / SNR 75.71 dB（`o64_onboard_20261026.md`）。
- 实时表述改 **30 min + 延迟分位数**：6000/6000 块、0 欠载、RSS 8,172 KB；p50 268.70 / p95 276.70 / p99 277.90 / max 278.10 ms，e2e p95 576.70 ms；削波 0.019%（`metrics/STABILITY_20261026.md`）。
- 新增 `design_report.md` §6.5 对照实验（时间对比度后滤波：原链路 +0.40、本方案 +0.067、**评估但不采用**，6 行文字 + 3 行表）；`checklist_submission.md` 相应项改已完成。

## 2026-10-27 提交前自查（第二版）

- `report/failure_analysis.md` 新增 **F13**：GAN 声码器支线（371,700/400,000 步、UTMOS 1.368、identity 0.726 追平 T4、周期度 0.856），决定性证据是"换 T4 相位 +0.50～0.52 / 换 T4 幅度 +0.04"；**8 行文字 + 4 行表**，不单开章。
- 溯源补链：`metrics/reports/` 新增 6 份被引用报告的**逐字节拷贝**（含 SHA）；`metrics.csv` 110 行 `source` 全部改成**相对包根、可打开**的路径，`summary.md` 重新生成；`resource_timing.csv` 用文档里的命令重跑 **51/51 行一致**。
- 修一致性：README `66 行→110 行`、日志目录计数（22/8/15/19）、`vc_stream.cpp 1652→1661 行`、`O64_ONBOARD_REPORT.md→report/o64_onboard_20261026.md`、`int8_latency.md` 文件名；`docs/toolchain.md` 增 §1.1（三条技术理由）与 §6（四道复现锁 + 2026.1 迁移顺序）；`build_arm.ps1`/`build_host.ps1`/`ref_chain.py` 的绝对路径改为参数/环境变量 + 明确报错。新增 `report/SUBMISSION_CHECKLIST_FINAL.md`。
