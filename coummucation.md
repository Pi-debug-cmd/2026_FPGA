# Agent 协作窗口

> **规范文件名：`coummucation.md`。** 拼写按用户要求保留。所有 Agent 开始工作前必须阅读本文件；所有方案轮次和测试轮次结束后必须更新本文件、提交并推送 GitHub。

## 角色

| 角色 | 能做 | 不能独立宣称 |
| --- | --- | --- |
| `Hardware-A` | 已在仓库提交；有板卡和 Vivado，可做板卡采录放、ARM、Vivado/RTL、PL、集成和现场证据 | 在没有可复现提交时替其他写作者补写结论 |
| `Hardware-B` | 已在仓库提交；有板卡和 Vivado，能力与 Hardware-A 相同，可独立认领硬件和 PL 任务 | 覆盖 Hardware-A 已认领的工程或改写其测试证据 |
| `Remote-PS-C` | 尚未加入；仅能在自己的电脑做 PS/软件算法、训练、离线推理、客观指标、压缩量化和 Cortex-A9 预算 | 板卡、Vivado、RTL、PL、实时和真人音色通过 |
| `Maintainer` | 分配任务、审核 PR、合并 main、冻结基线 | 删除失败证据或改写用户反馈 |

## 状态

`OPEN → CLAIMED → PROPOSED → WAIT_LOCAL_TEST → ACCEPTED / REJECTED / BLOCKED`

- `PROPOSED`：远端方案和客观证据完整，但尚未要求现场测试。
- `WAIT_LOCAL_TEST`：客观门已通过，需要本地试听或板测。
- `ACCEPTED`：对应门槛全部通过，可进入下一阶段。
- `REJECTED`：本轮失败，保留证据并写明停止原因。
- `BLOCKED`：缺少外部资源或输入，写明恢复条件。

## 方案提交模板

```markdown
### [任务编号] 标题
- 日期：YYYY-MM-DD
- 角色/Agent：Hardware-A | Hardware-B | Remote-PS-C / 名称
- 状态：CLAIMED | PROPOSED | WAIT_LOCAL_TEST
- 基准提交：<git SHA>
- 目标与本轮唯一变量：
- 修改路径：
- 复现命令：
- 输入与数据切分：
- 结果：身份 / P10 / 泄漏 / UTMOS / CER / 速度 / 模型大小
- 成功门槛对照：
- 已知限制：
- 报告链接：
- 提交或 PR：
- 下一责任方：Hardware-A | Hardware-B | Remote-PS-C | Maintainer
```

## 本地测试回填模板

```markdown
### [同一任务编号] 本地测试结果
- 日期：YYYY-MM-DD
- 角色/Agent：Hardware-A | Hardware-B / 名称
- 状态：ACCEPTED | REJECTED | BLOCKED
- 被测提交：<git SHA，不允许只写文件名>
- 板卡/工具/音频条件：
- 测试内容：
- 客观结果：
- 用户听感原话：
- 原始证据：
- 结论与停止/继续条件：
- 提交：
- 下一责任方：
```

## 当前项目裁决

### [BASE-20261021] 当前基线与分工
- 日期：2026-10-21
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED（协作基线）
- 当前事实：A1/WORLD 已能在板端运行且清楚连续，但目标身份约 0.190，仍保留输入者低沉沙哑音色；尚无通过音色门的 PS 方案。
- Remote-PS-C 主责：寻找高质量、可压缩到 Cortex-A9 的陌生源到固定目标方案，并提供可复现客观证据。
- Hardware-A/B 主责：真人试听、板卡 PS 文件转换、音色验收、PL 评估/部署/加速；两方先认领再改动，避免冲突。
- 学生客观门：身份均值 ≥0.45、身份 P10 ≥0.35、源泄漏均值 ≤0.10、UTMOS ≥2.30、CER ≤0.15。
- 现场门：客观门全过后，本地盲听相对 A1 的目标相似偏好 ≥70%。
- 证据：`report/quality_exploration_route_20261018.md`、`report/quality_exploration_ps_round_20261019.md`。
- 仓库检查：PR 和直接推送都会运行 `verify-round-record`。当前私有仓库套餐不支持 GitHub branch protection，因此该检查能明确标记违规提交，但无法在服务器端阻止有 write 权限者直接推送；协作者仍必须使用任务分支和 PR。
- 下一责任方：Remote-PS-C。

### [BASE-20261021-03] 三写作者能力边界修正
- 日期：2026-10-21
- 角色/Agent：Maintainer
- 状态：ACCEPTED（用户确认）
- 事实：项目共有三个写作者。当前已经提交的两位写作者都有 Zynq-7020 板卡和 Vivado 环境；尚未加入的第三位写作者没有板卡和 Vivado，只能在自己的电脑运行 PS/软件方案。
- 分工：Hardware-A 与 Hardware-B 均可认领板端、Vivado、RTL、PL、集成和硬件验证；Remote-PS-C 只提交可复现的软件候选和客观指标，再由任一硬件方验证。
- 冲突规则：两名硬件方修改同一 Vivado/RTL/板端任务前必须先在本文件标记 `CLAIMED`；未认领不得并行改同一组文件。
- 现场规则：需要人员操作、录音、播放或试听前，当轮先询问操作者是否准备好。
- 下一责任方：三个写作者按任务队列认领。

### [BASE-20261021-02] 协作者音频资产接收
- 日期：2026-10-21
- 角色/Agent：Hardware-B 上传，Hardware-A/Codex 只读审计
- 状态：ACCEPTED（资产清单，不代表音质通过）
- 被审计提交：`dfd61fb`、`5d5b137`
- 结果：仓库现有女声目标 Track 5～9 共 5 段、男声输入共 5 段；合计 10 个 WAV、53,629,014 字节、218.22 秒。女声为 48 kHz/双声道/24-bit，男声为 48 kHz/双声道/16-bit。
- 审计方式：仅解析 WAV 文件头并计算 SHA-256，未播放、未听辨、未操作板卡。
- 数据边界：女声 Track 5～8 可沿用为目标注册/建模素材，Track 9 保持目标留出；本批男声只作为源侧补充评测，不参与目标建模，也不足以证明多人泛化。
- 证据：`report/collaborator_audio_assets_20261021.json`
- 仍缺：完整训练/留出语料、FARGAN 可复现合成器和 HuBERT 权重仍未随 Git 提供。
- 下一责任方：Remote-PS-C。

### [DOCS-20261021-03] 协作者提交需求冲突审查
- 日期：2026-10-21
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED（文档审查完成，不代表音色或板端通过）
- 基准提交：`308928b6680497a080eed9a5152405fd3984813a`
- 目标与本轮唯一变量：核对协作者新增音频、厂商板卡资料和 `板载资料/说明.md` 是否改变现行项目需求；未运行现场测试。
- 修改路径：`板载资料/说明.md`、`report/collaborator_submission_audit_20261021.md`、`coummucation.md`
- 复现命令：`python tools/check_collaboration_policy.py --base 5fbc646 --head 308928b`
- 结果：音频和厂商资料可作为受控输入/参考资产；`04fcc7e` 中“目标声音可在演示前准备”和“子目录说明覆盖 project_guide”与板上现场注册硬要求冲突，已修正。规则生效后的 `8789c04`、`75d0edf`、`04fcc7e` 同时违反任务编号、交流记录和任务分支/PR规则。
- 限制：只做仓库静态审查，未试听、未操作板卡、未运行 Vivado；现有一组男声不足以证明陌生多人泛化。
- 报告链接：`report/collaborator_submission_audit_20261021.md`
- 提交或 PR：`agent/Pi-debug-cmd/DOCS-20261021-03`，https://github.com/Pi-debug-cmd/2026_FPGA/pull/1
- 下一责任方：Maintainer 审核；Remote-PS-C 继续 `PS-20261021-01`，Hardware-A/B 等待客观门通过后本地验证。

### [PS-20261019-01] LLVC content → FARGAN v1
- 日期：2026-10-19
- 角色/Agent：Hardware-A / Codex（离线实验）
- 状态：REJECTED
- 方案：冻结 reduced-LLVC 内容编码器，64 维 PCA 和 80 ms 过去上下文 MLP 预测完整 20 维目标 FARGAN 特征；不使用源谱残差或跳连。
- 结果：身份均值 0.656、P10 0.621、源泄漏 0.065，通过身份/泄漏门；UTMOS 1.660、CER 0.582，未过自然度和内容门。
- 决定：不试听、不部署 PS、不交 PL，不延长训练。
- 代码：`build/quality_exploration/train_llvc_content_fargan.py`、`build/quality_exploration/evaluate_llvc_content_fargan.py`。
- 报告：`report/quality_exploration_llvc_content_fargan_v1_20261019.json`、`report/quality_exploration_ps_round_20261019.md`。
- 下一责任方：Remote-PS-C。

## 当前任务队列

### [PS-20261021-01] HuBERT 语义教师到目标 FARGAN 的质量上限
- 日期：2026-10-21
- 角色/Agent：待认领的 `Remote-PS-C`
- 状态：OPEN
- 目标：先验证高质量语义特征是否足以预测目标 FARGAN 20 维特征，同时保住内容、自然度、目标身份和低源泄漏。
- 范围：只做电脑端离线实验，不接板卡，不改 RTL/Vivado，不播放音频。
- 开始前资产核对：Git 已包含目标 Track 5～9 和一组男声评测录音，但不包含 `build/generated/`、模型权重、完整训练语料或 `board_budget_20261005`。认领者必须核对 FARGAN 合成器、训练/留出语料与 HuBERT 权重；缺任一项就把本任务标为 `BLOCKED`，列出缺失项和 SHA/获取方式，不得用占位文件生成结果。
- 数据：沿用现有说话人隔离切分；不得使用验证说话人选择 checkpoint；需记录数据和模型 SHA。
- 最小对照：教师 FARGAN oracle、已拒绝的 direct-20D bottleneck、本轮 LLVC-content/FARGAN v1。
- 输出：训练/推理脚本、四项指标 JSON、模型规模和每秒 MAC、是否值得蒸馏的明确结论。
- 门槛：身份均值 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。
- 停止条件：teacher 语义上限仍不能同时通过五门时，停止 FARGAN 特征预测路线并提交失败证据。
- 下一责任方：Remote-PS-C 加入后认领并在本节下方追加记录。

远端首次操作建议：从 `main` 创建 `agent/<账号>/PS-20261021-01`；先追加一条 `CLAIMED` 或 `BLOCKED` 记录并提交。若资产齐全，再以本轮唯一变量“内容表示由 LLVC latent 改为 HuBERT teacher”实现独立训练/评测入口，禁止修改本地板卡与 PL 文件。

### [PS-20261021-02] 小型因果语义编码器蒸馏
- 状态：BLOCKED
- 恢复条件：`PS-20261021-01` 五门全部通过。
- 目标：蒸馏为 Cortex-A9 可运行的因果学生，先做 PS 文件转换，不进入 PL。
- 下一责任方：Remote-PS-C。

### [LOCAL-PS-20261021-01] Cortex-A9 文件转换与试听
- 状态：BLOCKED
- 恢复条件：远端候选客观门全部通过并标记 `WAIT_LOCAL_TEST`。
- 内容：本地做 ARM 文件转换、运行时间/内存测量，再按用户当轮准备确认进行试听。
- 下一责任方：Hardware-A 或 Hardware-B。

### [PL-20261021-01] 候选资源评估与部署
- 状态：BLOCKED
- 恢复条件：`LOCAL-PS-20261021-01` 音色通过。
- 内容：资源评估、定点/量化、PL 部署、音色回归与实时加速。
- 下一责任方：Hardware-A 或 Hardware-B。
