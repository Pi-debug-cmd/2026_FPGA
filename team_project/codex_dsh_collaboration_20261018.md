# Codex 与 deepseek-harness 协作边界（2026-10-18）

## 共同目标

现场在板卡上注册目标声源；随后不同陌生输入者经过短准备录音，均能实时转换为该目标声线。

项目主线以PL实现为核心。统一门控顺序为：可接受音色方案 → PL资源评估 → PL基础部署 → PL音色验证 → PL实现层修复；实现层多轮无法恢复音色才回退算法方案。只有PL音色通过后，才进入实时性优化。不得长期停留在电脑端模型，也不得用PS计算替代应由PL承担的主要工作量。

## 文件所有权

### deepseek-harness 当前主责（Codex 只读）

- `src/rtl/synth_offload/`：IFFT、最小相位与后续 PL 加速器。
- `src/ps/world_*.cpp`：A1 板端注册、转换与实时性主线。
- `build/check_world_*`、`build/run_world_*`、PL 综合/仿真脚本。
- `report/pl_synth_offload_*`、`report/world_realtime_*`、`report/g1_decision_20261021.md`。
- 当前 Vivado MCP 会话 `vivado-20261018-135638-4cffbfb1`；Codex 只读取会话和历史，不执行 TCL、不停止会话。

### Codex 当前主责（dsh 可读取结果）

- `build/quality_exploration/`：离线高质量教师、目标提示与蒸馏实验。
- `report/quality_exploration_*`：质量指标、失败原因和候选决策。
- `data/registrations/target_profiles/`：目标注册画像的版本化测试产物。
- `tools/eval_candidate.py`：共享只读评测入口；保持向后兼容。

## 冻结交接接口

Codex 只向 dsh 交付下列产物，不直接改实时链：

1. `target_profile_v2.json`：格式版本、目标音频 SHA、F0 分位、谱画像、质量门控、可选教师嵌入的来源与维度。
2. `candidate_metrics.json`：身份相似度、源泄漏、UTMOS、内容字错及主观听感，必须列明窗口对齐。
3. 候选算法规格：逐帧输入/输出、定点范围、状态量、每秒 MAC、模型与缓存大小。
4. 只有同时满足质量门槛和板端预算的候选，才建议 dsh 接入 A1＋PL；接入由 dsh 完成。

## 当前决策

- A3 参数域网络已触发杀停线：身份和内容提高，但自然度约 1.40、用户听感模糊，不再续调。
- Seed-VC 保留为电脑离线质量教师；不能直接声称可在 Zynq-7020 实时。
- 多段目标注册提示已被用户判为比单段提示更像目标、闷感更少；CFG 0.70/0.95听感接近，暂不固化单一值。Seed-VC继续作为离线教师。
- mapper-independent FARGAN目标真人录音oracle通过：身份均值0.878、UTMOS均值2.752、繁简归一CER均值0.031。FARGAN声码器骨架可保留。
- 直接从源20维FARGAN特征学习的无跳连因果瓶颈已在两名未见源上失败：身份0.658，但泄漏0.224、UTMOS1.670、CER0.580。该特征路线停止，产物不得交给dsh接入实时链。
- 下一质量路线是用更强的说话人无关语义教师蒸馏因果内容编码器；越过离线质量门前不提出A1/PL集成请求。
- 每次现场录音或试听仍需用户当轮确认准备；纯离线计算可持续进行。

## Vivado MCP 使用约束

- 已验证服务器 2026.9.1 可握手并列出工具。
- 当前恢复到的 Vivado 2026.1 会话正在综合 `src/rtl/synth_offload/`，属于 dsh；Codex 只读查询了会话与历史，没有向该会话执行 TCL，也没有停止会话。
- 本机当前实际可用的是 Vivado 2026.1；旧安装说明中的2018.3路径已经不存在。2026.1只能用于独立临时工程的语法、仿真和OOC审查，不能打开并保存比赛的2018.3基线工程。
- Codex 如需自己的 RTL 审查/仿真，必须使用独立端口、状态目录、工作目录和Vivado会话；不得复用、清理或终止dsh会话。
