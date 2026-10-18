# 协作边界：Lead（速度/PL/集成）与 Codex（音色）（2026-10-18）

## 分工

| 方向 | 负责方 | 主要内容 |
| --- | --- | --- |
| **音色相似度** | Codex | 音色映射算法、包络/F0 策略、目标画像拟合、离线音色候选与听感对照 |
| **速度 / PL / 集成 / 证据** | Lead（我） | PL 合成卸载、PS 性能优化、板上注册链路、实时框架集成、独立评测与证据归档 |

## 我方写作用域（Lead）

- `src/rtl/synth_offload/`（IFFT 核、最小相位加速器、ROM、TB、综合脚本）
- `src/ps/world_register.cpp`、`build/build_world_register.ps1`、`build/run_world_register_board.ps1`、`build/run_world_convert_board.ps1`（注册链路，非音色算法）
- `build/generated/pl_synth_offload/`、`build/generated/fastmath_20261018/`、`build/generated/arm_bench_20261018/`、`build/generated/world_register_20261016/`
- `tools/mcp_vivado.py`、`tools/eval_candidate.py`
- `board/` 下的串口/上传/下载脚本（本机唯一串口通道）
- 我方报告：`report/pl_synth_offload_*`、`report/synthesis_arm_breakdown_*`、`report/fastmath_*`、`report/g1_decision_*`、`report/a1_a3_*`、`report/tools_vivado_mcp_*`、`report/world_register_*`、`report/world_realtime_*`

## 避免冲突的约定

1. **不碰 Codex 的音色文件**：`src/reference/timbre_envelope.py`、`spectral_balance.py`、`source_target_mapping.py`、`world_registration.py` 的音色部分、`build/generated/a3_neural/`、`report/a3_neural_*`。
2. **不碰音色候选数据**：`data/registrations/` 下由 Codex 生成的新目录与配置；我方只读。
3. **共享文档只在必要时追加**：`plan.md`、`team_project/project_status.md`、`report/ai_worklog.md` 属共享文件。为避免同文件并发写冲突：
   - 优先写我自己的报告文件（前缀见上）；
   - 需要更新共享文档时，**用"追加一段"而不是整文件重写**，并在段落标题标注 `[Lead]`；
   - 如果发现共享文件已被对方改写，不覆盖，改为在我的报告里引用对方内容。
4. **接口对接点**（两边都要用到、改动需提前说）：
   - `tools/eval_candidate.py`（四项指标，只读调用，Codex 可直接用）
   - 实时转换链路的入口（`board/world_live_trial.md` 描述的板端程序）——Codex 若改音色映射，需保持该入口的参数契约；我若改 PL 卸载，不动音色参数含义。
5. **PL 资源账本**：现有 PL 已用 8302 LUT / 6 DSP；我新增的卸载核预算为 LUT ≤10k、BRAM ≤4、DSP ≤8（增量 1 实测 363 LUT / 3 RAMB18 / 4 DSP），预留余量给 Codex 可能的音色模块。

## 当前状态同步（截至 2026-10-18 15:00）

- 主线已定：**A1 + PL 合成卸载**（听感裁决：A3 模糊、A1 更像目标）。
- A3 已终结，身份 0.561 作为技术上界归档。
- PL 增量 1 达标；最小相位加速器 RTL 未收敛（exp 单元），候选方案 CORDIC。
- 板端拆解修正：合成中最小相位占 54.0%、非周期整体 59.6%、OLA 1.1%；PS 侧 fast-math 捷径否决。
- 收益预期：PL 卸载后 PS 全链约 **0.52 RTF**（原估 0.35 基于宿主占比，过于乐观）。
