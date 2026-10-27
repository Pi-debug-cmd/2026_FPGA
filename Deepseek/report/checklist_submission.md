# 提交自查表 / 剩余工作清单

> **状态（2026-10-27）**：本表是 2026-10-26 的工作版，其中"PL 未集成""O64 实时档未测"
> 两条已于 2026-10-27 关闭。**以 [`SUBMISSION_CHECKLIST_FINAL.md`](SUBMISSION_CHECKLIST_FINAL.md) 为准**；
> 本文件保留作为过程记录（下面已把过期结论就地标注，不删原文）。

> 截止：2026-11-04 18:00（剩约 9 天）。本表是"现在能不能交"的判定，
> 以及"交之前还值得做什么"的排序。每项都有验收判据。

---

## 1. 硬要求（缺一项就会被扣/退）

| # | 要求 | 状态 | 证据 |
|---|---|---|---|
| 1 | 初级组器件为 Zynq-7000 | ✅ | `docs/hardware_setup.md`（`xc7z020clg400-2`） |
| 2 | 实现方式不限（RTL/HLS/PS） | ✅ | PS C + RTL，`docs/architecture.md` |
| 3 | 工具版本说明（非 2026.1/2025.2 时） | ✅ | `docs/toolchain.md`（2018.3，IP 版本逐项核对，Tcl 全入库） |
| 4 | 脚本可复现 | ✅ | `fpga/src/bd/*.tcl` + `fpga/build/build_pl.ps1` + `host/app/build_arm.ps1` |
| 5 | 板上跑通并提供实测输出 | ✅ | `metrics/logs/board_c/`、`report/o64_onboard_20261026.md`（O64 23.72 s 整段 + 4 s 同输入） |
| 6 | **大模型协作记录**（提示词/回答/自我纠错） | ✅ | `ai_collaboration/`（6 专题 + 28 轮 + 94 KB 附录） |
| 7 | **经验提炼为 Skill** | ✅ | `skill/`（3 个，含复用场景与已验证结果） |
| 8 | 目录/文件名纯英文 | ✅ | 已全量校验（332 个文件，0 个非 ASCII 名；例外清单见 `metrics/README.md` §8） |
| 9 | 性能与资源数据真实完整 | ✅ | 资源/时序完整；**延迟分位数已补**（p50 268.70 / p95 276.70 / p99 277.90 / max 278.10 ms） |
| 10 | 他人能复现 | ⚠️ | 步骤齐全；**四指标复算需目标语料（不随包分发）** |

---

## 2. 建议在提交前补的四项（按性价比排序）

### 2.1 延迟分布 p50/p95/p99（半天，收益最大）— ✅ **2026-10-26 已完成**

- **为什么**：补测前 `metrics.csv` 里三行是 `not_measured`。评委看"实时"一定会找分布。
- **怎么做**：板上跑 `sh metrics/scripts/measure_latency.sh 300 60 in.raw lat_300.csv`，
  把输出填进 `metrics/metrics.csv` 三行（status 改 `measured`），重跑 `csv_to_md.py`。
- **验收**：`e2e_p95 ≤ 700 ms` 且 `underruns == 0`。
- **风险**：低。脚本已写好，只需板子空 1 小时。
- **结果**：p50 **268.70** / p95 **276.70** / p99 **277.90** / max **278.10 ms**（200 块；
  e2e p95 576.70 ms ✅）。过程中发现原脚本把累计 `proc_ms` 当每块用，已修，
  见 `metrics/scripts/CHANGES_measure_latency_20261026.md`。

### 2.2 30 min 长稳（半天，和 2.1 一起做）— ✅ **2026-10-26 已完成**

- **为什么**：补测前最强的话只是"短时连跑 0 欠载"，撑不起"实时"这个词。
- **怎么做**：`measure_latency.sh 300 1800`，同时记录 `uptime`/`/sys/class/thermal`。
- **验收**：30 min 内 underrun ≤ 2，`proc_ms` 的 p99 不随时间漂移。
- **风险**：低。
- **结果**：6000/6000 块、**underrun 0**、无掉块、RSS 恒定 8 172 KB；削波 0.019%
  （批处理 0，属 live 档固有）。温度未采集（板端无 thermal zone 读数），不声称已测。
  见 `metrics/STABILITY_20261026.md`。

### 2.3 把 PL 变调核接进主链（2–3 天，收益与风险都最大）— ✅ **2026-10-27 已解决，但走的是 STFT 而非变调核**

> **结果**：PL 承担 STFT/IFFT + 逐 bin 频域乘法（`fpga/stft/`），端到端 corr 0.99999999 / max 4 LSB，
> STFT 段 449.04→305.82 ms、整链 RTF 0.9376→0.9019、16,723 LUT / 22 BRAM / 76 DSP、WNS +0.347 ns。
> 变调核保持"已验证的备用设计"（bit-exact、RTF 0.0078），与 STFT 版互斥。
> 见 `fpga/stft/PL_STFT_20261027.md`、`report/failure_analysis.md` F12。
> 下面保留原来的计划正文作为过程记录。

- **为什么**：这是"创新性（PS/PL 协同）"的最大短板（`report/failure_analysis.md` F12）。
- **怎么做**：
  1. 在 `vc_stream.cpp` 里把 `pitch_block()`（SoundTouch）替换成"写 DDR → DMA → PL → DMA → 读"；
  2. 缓冲区用 `skill/dma_cache_coherency/dmabuf.h`（非缓存别名）；
  3. 比例由 GPIO 写（`ratio_q16 = 91750` 对应 1.4×，即 `1.4 × 65536 = 91750.4`；先跑 65536 恒等回归）。
- **验收**：4 s 总耗时下降 ≥150 ms；四项指标变化在容差内；`--stream 300` 仍 0 欠载。
- **风险**：中。若 2 天内调不通，**立刻回退**（保留 SoundTouch 分支），不要影响提交。

### 2.4 人工盲测（半天，需人）

- **为什么**：`report/design_report.md` §8 明确写了"未做人工听音"。
- **怎么做**：ABX 三组（默认档 / live 档 / 电脑端参考），≥5 人 × 10 轮。
- **验收**：记录偏好率与"是否能听出 live 档与默认档的差别"。
- **风险**：低，但需要人到场。

---

## 3. 提交前 24 小时的检查动作（清单，按顺序）

```text
[ ] 1. 全包扫一遍文件名：无中文、无空格、无大写混用  → 已自动校验
[ ] 2. 打开 README.md 按 §3 走一遍"只看结果"路径（5 分钟）
[ ] 3. 跑 skill/golden_reference_compare/example/gen_demo.py → DEMO PASS
[ ] 4. 跑 collect_metrics.py 重新抽取资源/时序 → 与报告数字一致
[x] 5. 若补了 2.1/2.2：确认 metrics.csv 无 not_measured（除长稳外）  → 2.1/2.2 已于 2026-10-26 补完，metrics.csv 里 latency/stability 的 not_measured 已清零
[x] 6. 确认 report/design_report.md §8 的"未完成清单"与实际情况一致  → 已按 O64 定版（23.72 s）与 30 min 长稳更新（2026-10-27）
[ ] 7. 确认 ai_collaboration/ 的 6 个专题都指向真实文件（无死链）
[ ] 8. 板子撤离：alsactl restore、stty echo、/etc/init.d/world-voice start
[ ] 9. 压缩包用 ASCII 文件名（如 vc7020_submission_20261104.zip）
[ ] 10. 备份一份到第二个物理位置（U 盘/网盘）
```

---

## 4. 现在就能交吗？

**能。** 硬要求 5/7/8 全绿，6/7（协作记录与 skill）是加分与硬要求双覆盖；
性能、资源、一致性、PL bit-exact 的证据链完整。
短板（UTMOS 门禁）都在报告里**主动写清**，
不是"被发现"，而是"我们自己列的"；延迟分布与 30 min 长稳已于 2026-10-26 补测
（见 `metrics/STABILITY_20261026.md`），削波 0.019% 这个新发现也一并写明。
O64 已定为质量定版（identity 0.7293 / UTMOS 2.2659，仍差 2.30 门禁 0.034），
其 **live 档已于 2026-10-27 实测**（RTF 0.860、60 s 0 欠载、p99 284.8 ms），
报告里按两个口径分开写，不混读（`metrics/O64_LIVE_20261027.md`）。

**且**：PL STFT 与 O64 live 档已于 2026-10-27 **联测通过**——4 s RTF **0.8237**、
STFT 段 **451.3→309.5 ms（−142 ms）**、60 s/200 块处理 p99 **274.8 ms**、**0 欠载**；
四项 0.7324 / 0.6903 / −0.0343 / 2.1532（UTMOS 仍差门禁）。见 `design_report.md` §6.8a 与
`report/PL_IN_LOOP_20261027.md`——剩下的短板只有 UTMOS。

---

## 5. 剩余工作的风险提示

| 若做 | 可能踩的坑 | 兜底 |
|---|---|---|
| 接 PL 进主链 | 缓存一致性（已知，有封装）、比例映射（1.4× 对应 Q16 91750，需实测确认） | 保留 SoundTouch 分支，开关切换 |
| 长稳测试 | `/tmp` 满、板子过热降频、串口掉线 | 用 tmpfs 监控；串口用 `screen` 重连；记录温度 |
| 吹 "实时" | 短时连跑撑不住 30 min | 只说"300 ms 块、30 min 6000 块 0 欠载（T4/48 阶 live）"，O64 精确档不要称实时 |
