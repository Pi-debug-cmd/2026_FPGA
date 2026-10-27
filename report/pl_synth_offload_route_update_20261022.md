# PL 合成卸载路线更新（2026-10-22）

> 触发：PS 基线已通过 60 s 真实 ALSA 录放（见 `report/live_pspl_baseline_20261022.md`），用户确认进入 PL 加速。
> 本文件更新 10-18 的路线决策（`report/pl_synth_offload_route_decision.json`），只用已有实测数据与定点精度分析，不代表已完成任何 PL 集成。

## 1. 当前基线数字（决定优先级）

| 项 | 数值 | 来源 |
| --- | --- | --- |
| 真实 60 s 语音：分析 RTF | **0.394** | `report/live_pspl_baseline_trial60_20261022.json` |
| 真实 60 s 语音：渲染 RTF（含输出等待） | **0.334** | 同上 |
| 分析单块最大耗时 | 36.3 ms / 200 ms 块 | 同上 |
| 合成内部：最小相位构建占比 | **84.99%** | `report/pl_synth_offload_cpu_breakdown.json` |
| 最小相位内部：exp/cos/sin 占比 | **62.7%（占合成）** | 同上 |
| 最小相位内部：两次 FFT 合计 | 约 9% | 同上 |

结论：合成里最贵的是 **exp/cos/sin（513 bin/帧）**；分析（D4C/CheapTrick）已是新的整链瓶颈，但那是另一条线。先摘合成里最大的果子。

## 2. 为什么把“24 位 FFT 通路”降级、先做 exp 单元

增量 2 步骤 B 的 18 位 FFT/IFFT 核已经验证（`report/pl_fft1024_engine_20261022.md`），但它不能直接接最小相位链，原因是**定点精度链**：

- WORLD 最小相位 log 谱实测范围 `a ∈ [−13.8, 0.1]`；Q1.17 只有 ±1，18 位通路装不下。
- 即使升级到 24 位 Q5.18（分辨率 3.8e-6）：
  - 第一段 FFT 输出 `C/1024` 需要精度约 **1.5e-8**（因为第二段 FFT 会再除以 1024，最终 L 要精确到约 1.5e-5，否则 exp 后幅度误差约 65 LSB Q1.17，超过 2 LSB 门）；
  - 24 位 Q5.18 的 3.8e-6 差约 250 倍，需要 **32 位 Q6.26 数据通路**，且旋转因子需要 ≥24 位（18 位 Q3.15 的 3e-5 相对误差会主导）；
  - 代价：BRAM 1024×64、32×24 复数乘（每复乘 3～4 个 DSP，4 复乘约 12～16 DSP），并且要把这个精度链在仿真里逐位证明。
- 而两次 FFT 合计只占最小相位构建约 9%、占合成不到 8%；投入 32 位数据通路收益很小。

所以：**FFT 继续留在 PS 用 double 做**；PL 只卸载 exp/cos/sin。18 位 FFT/IFFT 核保留为已验证基础设施（后续脉冲 IFFT/OLA 路径仍可能用到），不进入本轮关键路径。

## 3. 新路线：PL 只做复数 exp 单元

接口约定（与已设计的 `minphase_exp_unit.v` 一致）：

```
每帧 513 bin，PS 送：
  A = log_spectrum/1024  Q5.18（24-bit signed）
  B = imag/1024          Q5.18（24-bit signed）
PL 返回：
  Y_RE = exp(A)*cos(B)   Q2.17（20-bit signed，|y|max≈1.115 不削顶）
  Y_IM = exp(A)*sin(B)   Q2.17
```

PS 侧保留：两次 FFT（double）、fold、以及后续脉冲谱乘/IFFT/OLA。这样 PL 替换的是最小相位里 62.7% 的合成耗时。

- 收益估算：渲染 0.334 RTF × 约 63% ≈ 释放 **0.21 RTF**；即 render 可能从 0.334 降到约 0.12（**估算，需板端实测**）。
- 资源估算（设计期）：cos/sin ROM 1024×36（1 RAMB36）+ exp ROM 256×18（1 RAMB18）、约 6 DSP、约 1.5–2k LUT；与增量 1/2 的用量叠加仍在 xc7z020 的 5 BRAM18/8 DSP/<3k LUT 量级内。
- 吞吐：串行每 bin 约 7 拍 × 513 ≈ 3.6k 拍/帧 = 36 µs @100 MHz，10 ms 帧预算的 0.36%。
- 数据带宽：每帧约 513×(8 B 入 + 5 B 出) ≈ 6.7 KB → 100 帧/s 约 0.67 MB/s，HP 口可忽略。

## 4. 前置条件与状态

| 项 | 状态 |
| --- | --- |
| 定点模型（96 次真实调用、49248 bin） | PASS：per-bin 3.07e-5、时域 0.41 LSB（`report/pl_synth_offload_minphase_expunit.json`） |
| RTL 0 LSB 验证 | **进行中**：根因已定位（cos/sin 缺 (j+1) 插值、exp ROM 同拍双地址、流水对齐），由子代理 `PL-EXP-20261022` 修复并重跑 49248 bin |
| PS 侧接口/驱动 | 待做：先把整数模型翻成 host/ARM C 参考，再设计 AXI-Stream 包装与 DMA/寄存器接口 |
| 板端集成与 RTF 实测 | 待 exp RTL 过后 |

## 5. 后续顺序

1. exp RTL 修到 0 LSB（进行中）；
2. host C 参考实现（与 Python 整数模型逐位一致），量每帧耗时与接口开销；
3. AXI-Stream 包装 + PS 驱动（先文件回放，逐帧 513 bin 注入，和 PS double 参考逐 bin 比对）；
4. 板端合成 RTF/延迟实测，再决定是否把分析（D4C/CheapTrick）也搬 PL；
5. 若后续确实需要 FFT 卸载，按 32 位 Q6.26 + 24 位旋转因子另立任务，不在本轮范围。

## 6. 证据

- 64 位基线数字：`report/live_pspl_baseline_20261022.md`、`report/live_pspl_baseline_trial60_20261022.json`
- CPU 拆解：`report/pl_synth_offload_cpu_breakdown.json`
- exp 模型与失败根因：`report/pl_synth_offload_minphase_expunit.json`、`report/pl_synth_offload_expunit_status.json`
- 18 位 FFT/IFFT 核（基础设施）：`report/pl_fft1024_engine_20261022.md`

## 7. 2026-10-22 夜间更新：exp RTL 功能已修复，时序待收敛

- **功能 PASS（子代理完成 + Lead 独立复跑）**：`minphase_exp_unit` 在 `D:\xsim_work\exp_unit_verify_20261022` 重新跑 xsim，结果 `PASS: 96 calls / 49248 bins, exp unit 20-bit fields bit-exact (0 LSB)`；RTL/ROM/TB 的 SHA-256 与子代理报告一致，TB 未改。每 bin 7 拍、513 bin = 3591 拍/帧 = 35.9 µs @100 MHz。
- **OOC 综合（Lead 单会话 MCP 执行，xc7z020，100 MHz）**：LUT **482**、FF **172**、RAMB36 **1**、RAMB18 0、DSP48E1 **9**；但 **WNS = −2.511 ns、Setup 失败端点 98**（Hold 0 失败，WHS +0.252）。关键路径 `u_rom/exp_lo_reg[0] → yre/yim_rnd`，数据路径 **12.14 ns**（18 级逻辑，CARRY4×10 + DSP×1）。
- **判断**：exp 插值（`exp_dif×frac`、`e_q16/e_q17` 移位）到最终复数乘之间缺少寄存器切分，组合路径过长；面积不是问题。
- **动作**：已开 `task-2 / PL-EXP2-20261022`，要求子代理在 exp 插值路径加流水寄存器，验收 100 MHz 下 WNS ≥ +0.3 ns、失败端点 0，且 xsim 仍 49248 bin 0 LSB；改完后 Lead 复跑 xsim + OOC 综合，再做后综合 funcsim。
- **证据**：`report/pl_expunit_fix_20261022.json`（子代理功能修复）、`report/pl_expunit_synth_20261022.json`（Lead 复核 + 综合）、`build/generated/pl_synth_offload/exp_unit_synth/`（utilization/timing/funcsim/dcp）。

## 8. 2026-10-22 最终验收：exp 单元功能 + 时序 + 后综合网表全部通过

子代理把 7 态流水扩成 **13 态流水**（每拍最多 1 个 DSP 组合段）后，Lead 做了独立最终验收：

| 项目 | 结果 |
| --- | --- |
| RTL 行为级 xsim | **PASS：96 calls / 49248 bins，0 LSB** |
| OOC 综合 @100 MHz | LUT **484** / FF **271** / RAMB36 **1** / DSP48E1 **9** |
| 时序 | **WNS +4.584 ns、WHS +0.240 ns、Setup/Hold 失败端点 0** |
| 后综合 funcsim | **PASS：49248 bins 0 LSB**（网表功能与 RTL 一致） |
| 吞吐 | 13 拍/bin × 513 = **6669 拍/帧 = 66.69 µs @100 MHz**（10 ms 帧预算的 0.667%） |
| 对比上一版 | WNS −2.511 → **+4.584 ns**；FF 172→271、LUT 482→484、DSP 不变 |

一个需要记录的插曲：第一次后综合 funcsim 出现前 6 个输出错位 + watchdog。根因是 **TB 没有等 glbl GSR 释放**（网表仿真带约 100 ns 全局复位，RTL 仿真没有），不是 RTL 功能问题。TB 加了与增量 1 相同的 `#200` GSR 等待后，RTL 与后综合网表都 0 LSB 通过；RTL 未改。失败日志保留为 `post_synth_first_fail.log`。

最终报告：`report/pl_expunit_acceptance_20261022.json`。**exp 单元可以进入 PS/AXI 集成阶段**。

下一步（PS/PL 集成）：
1. 写 AXI-Stream 包装 + PS 侧 C 驱动（513 bin/帧，Q5.18 入 / Q2.17 出）；
2. 与 PS 双精度最小相位链逐帧比对（先文件回放）；
3. 板端 RTF/延迟实测；
4. 再评估分析支路（D4C/CheapTrick）是否搬 PL。


