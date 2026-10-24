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
- 远端存储：所选非系统盘总目录 / 主要缓存与临时目录 / 空间不足或无法重定向的例外；非远端任务写“无”
- 输入与数据切分：
- 结果：身份 / P10 / 泄漏 / UTMOS / CER / 速度 / 模型大小
- 成功门槛对照：
- 已知限制：
- 报告链接：
- 模型产物：Release URL/标签 / 源提交 SHA / 附件名、字节数及 SHA-256 / 获取与推理命令 / 干净目录下载运行证据；本轮未产生则写“无”
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

## 历史任务队列（已由下方三级路线重置取代）

以下 `PS-20261021-01/02`、`LOCAL-PS-20261021-01`、`PL-20261021-01` 均已 `SUPERSEDED`，不得按旧任务说明认领。当前唯一开放的算法任务是下方 `PS-20261021-10`。

### [PS-20261021-01] HuBERT 语义教师到目标 FARGAN 的质量上限
- 日期：2026-10-21
- 角色/Agent：待认领的 `Remote-PS-C`
- 状态：SUPERSEDED（由 `PS-20261021-10` 取代，内容只可作为候选对照）
- 目标：先验证高质量语义特征是否足以预测目标 FARGAN 20 维特征，同时保住内容、自然度、目标身份和低源泄漏。
- 范围：只做电脑端离线实验，不接板卡，不改 RTL/Vivado，不播放音频。
- 开始前资产核对：Git 已包含目标 Track 5～9 和一组男声评测录音，但不包含 `build/generated/`、模型权重、完整训练语料或 `board_budget_20261005`。认领者必须核对 FARGAN 合成器、训练/留出语料与 HuBERT 权重；缺任一项就把本任务标为 `BLOCKED`，列出缺失项和 SHA/获取方式，不得用占位文件生成结果。
- 数据：沿用现有说话人隔离切分；不得使用验证说话人选择 checkpoint；需记录数据和模型 SHA。
- 最小对照：教师 FARGAN oracle、已拒绝的 direct-20D bottleneck、本轮 LLVC-content/FARGAN v1。
- 输出：训练/推理脚本、四项指标 JSON、模型规模和每秒 MAC、是否值得蒸馏的明确结论。
- 门槛：身份均值 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。
- 停止条件：teacher 语义上限仍不能同时通过五门时，停止 FARGAN 特征预测路线并提交失败证据。
- 下一责任方：Remote-PS-C 加入后认领并在本节下方追加记录。

历史操作建议（已失效，不要执行）：当时要求从 `main` 创建 `agent/<账号>/PS-20261021-01`。现行任务应从下方 `PS-20261021-10` 认领，遵守 `plan.md` 的固定男性一对一切分。

### [PS-20261021-02] 小型因果语义编码器蒸馏
- 状态：SUPERSEDED（改由 `PS-20261021-11` 管理）
- 恢复条件：`PS-20261021-01` 五门全部通过。
- 目标：蒸馏为 Cortex-A9 可运行的因果学生，先做 PS 文件转换，不进入 PL。
- 下一责任方：Remote-PS-C。

### [LOCAL-PS-20261021-01] Cortex-A9 文件转换与试听
- 状态：SUPERSEDED（改由 `LOCAL-PS-20261021-10` 管理）
- 恢复条件：远端候选客观门全部通过并标记 `WAIT_LOCAL_TEST`。
- 内容：本地做 ARM 文件转换、运行时间/内存测量，再按用户当轮准备确认进行试听。
- 下一责任方：Hardware-A 或 Hardware-B。

### [PL-20261021-01] 候选资源评估与部署
- 状态：SUPERSEDED（改由 `PL-20261021-10` 管理）
- 恢复条件：`LOCAL-PS-20261021-01` 音色通过。
- 内容：资源评估、定点/量化、PL 部署、音色回归与实时加速。
- 下一责任方：Hardware-A 或 Hardware-B。

## 2026-10-21 三级路线重置

### [DOCS-20261021-04] 重写保底、进阶、最终三级计划
- 日期：2026-10-21
- 角色/Agent：Maintainer / Codex
- 状态：SUPERSEDED（三级顺序继续有效；其中“两名固定输入者”的错误定义由 `DOCS-20261021-06` 纠正）
- 基准提交：`308928b6680497a080eed9a5152405fd3984813a`
- 目标与本轮唯一变量：废止旧 `plan.md` 的日历与阶段顺序，建立“固定两人保底 → 陌生多人进阶 → 现场注册最终”的严格串行门控。
- 修改路径：`plan.md`、`AGENTS.md`、`project_guide.md`、`handoff_20261021.md`、`coummucation.md`
- 复现命令：`git diff --check origin/main..HEAD`；`python tools/check_collaboration_policy.py --base origin/main --head HEAD`
- 输入与数据切分：保底和进阶统一以 `人物音频资料/女声/Track 5～8.wav` 建模，`Track 9.wav` 锁定目标留出；历史 `voice_src/src_1` 五个文件 SHA 与其逐一相同，不重复计数。
- 结果：当前只开放第一级。保底允许固定两人各自源配置，但必须两人分别通过软件音色、PS 文件、试听、PL 音质、实时和稳定性；之后才取消源档案做陌生多人，最后才实现板上现场目标注册。
- 成功门槛对照：每级沿用身份均值/P10、源泄漏、UTMOS、CER 和真人试听门，并新增 PL 质量回归、p95 延迟与 30 分钟稳定性出口门，详见 `plan.md`。
- 已知限制：现有仓库明确只有 `Fixed-A` 一组男声素材；第二名 `Fixed-B` 尚未采集。公开语料和无效历史诊断录音不能冒充第二人。
- 报告链接：`plan.md`
- 提交或 PR：`agent/Pi-debug-cmd/DOCS-20261021-04`，https://github.com/Pi-debug-cmd/2026_FPGA/pull/2
- 下一责任方：Remote-PS-C 或任一硬件方先认领 `PS-20261021-10`；后续级别保持关闭。

### [PS-20261021-10] 固定男性到既定女声的一对一质量上限
- 状态：OPEN（现有男性 3/1/1 素材足以启动）
- 范围：按句子/录制会话隔离冻结唯一固定男性输入者，建立该男性到既定女性目标声的一对一音色上限；允许源专用配置，不接板卡、不改 RTL/Vivado。说话人隔离只用于第二级。
- 目标资产：`人物音频资料/女声/Track 5～8.wav`；`Track 9.wav` 只作留出。
- 输入资产：`Fixed-Male` 使用男声标准录音 1～3 训练、4 验证、5 锁定验收，清单见 `report/fallback_one_to_one_assets_20261021.json`；最终验收前按 `board/fallback_one_to_one_capture.md` 补一段冻结模型后的新会话句。
- 出口：固定男性输入者在未见句上通过身份均值 ≥0.45、P10 ≥0.35、源泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15，并标记 `WAIT_LOCAL_TEST`。
- 下一责任方：待认领的 Remote-PS-C、Hardware-A 或 Hardware-B；认领者先补 `CLAIMED` 记录。

### [PS-20261021-11] 保底方案因果压缩
- 状态：BLOCKED
- 恢复条件：`PS-20261021-10` 一对一男转女质量上限通过。

### [LOCAL-PS-20261021-10] 保底 Cortex-A9 文件与一对一男转女试听
- 状态：BLOCKED
- 恢复条件：`PS-20261021-11` 客观门通过并标为 `WAIT_LOCAL_TEST`。

### [PL-20261021-10] 保底 PL 部署与音质回归
- 状态：BLOCKED
- 恢复条件：`LOCAL-PS-20261021-10` 一对一男转女试听通过。

### [TEST-20261021-10] 保底实时完整验收
- 状态：BLOCKED
- 恢复条件：`PL-20261021-10` 音质回归通过。
- 出口：固定男性到固定女声的板上实时转换、p95 延迟、30 分钟稳定性、冷启动和恢复全部通过后，才开放进阶方案。

旧 `PS-20261021-01/02`、`LOCAL-PS-20261021-01`、`PL-20261021-01` 的队列顺序从本节起标记为 **SUPERSEDED**；其证据保留，候选内容只能在新任务编号下重新认领和验收。

### [DOCS-20261021-05] 统一三阶段基线与两人素材协议
- 日期：2026-10-21
- 角色/Agent：Maintainer / Codex
- 状态：SUPERSEDED（其中“两名固定输入者”定义由 `DOCS-20261021-06` 纠正；其余三级顺序和第三级现场注册要求继续有效）
- 基准提交：`308928b6680497a080eed9a5152405fd3984813a`
- 目标与本轮唯一变量：合并原 PR #1/#2 的相容要求，确认第三级现场板上注册是最终硬标准，并修正第一级数据切分与素材阻塞。
- 修改路径：原 PR #1/#2 全部文档，以及 `board/fallback_source_capture.md`、`board/capture_source_mapping.py`、`report/fallback_two_source_assets_20261021.json`
- 复现命令：`python -m json.tool report/fallback_two_source_assets_20261021.json`；`python board/capture_source_mapping.py --help`；`git diff --check origin/main..HEAD`；`python tools/check_collaboration_policy.py --base origin/main --head HEAD`
- 输入与数据切分：`Fixed-A` 使用标准录音 1～3 训练、4 验证、5锁定验收；`Fixed-B` 待按同样 3/1/1 角色采集。第一级按同一说话人的句子/录制会话隔离，第二级才按说话人隔离。
- 结果：公开语料、目标女声、转换输出和历史无效诊断均不得替代 `Fixed-B`；当前任务准确状态为 `BLOCKED（缺少 Fixed-B 资产）`。
- 已知限制：`Fixed-A` 五个文件是否跨日期录制没有证据，最终验收仍需冻结模型后的新会话句。
- 报告链接：`report/fallback_two_source_assets_20261021.json`、`board/fallback_source_capture.md`
- 提交或 PR：`agent/Pi-debug-cmd/DOCS-20261021-05`，https://github.com/Pi-debug-cmd/2026_FPGA/pull/3
- 下一责任方：由 `DOCS-20261021-06` 重新开放 `PS-20261021-10`，不再采集 `Fixed-B`。

### [DOCS-20261021-06] 将保底方案纠正为一对一男转女
- 日期：2026-10-21
- 角色/Agent：Maintainer / Codex
- 状态：ACCEPTED（用户明确纠正范围）
- 基准提交：`6304247b18298808cc55cf011c1c77ff5ec467c4`
- 目标与本轮唯一变量：把第一级从“固定两名输入者”纠正为“固定一名男性输入者到既定女性目标声的一对一转换”；第二级陌生多人和第三级现场注册定义不变。
- 修改路径：`plan.md`、`AGENTS.md`、`project_guide.md`、`handoff_20261021.md`、`coummucation.md`、`board/fallback_one_to_one_capture.md`、`report/fallback_one_to_one_assets_20261021.json`
- 复现命令：`python -m json.tool report/fallback_one_to_one_assets_20261021.json`；`rg -n "Fixed-B|fallback_two_source|固定两名输入者|两人专用" AGENTS.md project_guide.md plan.md handoff_20261021.md board report/fallback_one_to_one_assets_20261021.json`（应无输出）；`git diff --check origin/main..HEAD`；`python tools/check_collaboration_policy.py --base origin/main --head HEAD`
- 输入与数据切分：唯一 `Fixed-Male` 使用男声标准录音 1～3 训练、4 验证、5 锁定验收；固定女性目标使用 Track 5～8 建模、Track 9 锁定留出。第一级按同一男性说话人的句子/录制会话隔离。
- 结果：删除 `Fixed-B` 和第二名输入者要求，`PS-20261021-10` 从资产阻塞改为 `OPEN`；最终验收前只需同一男性补一段冻结模型后的新会话句。
- 量化结果：源素材 5 个文件，角色切分 3/1/1；目标素材 5 个文件，角色切分 4/1；本轮未运行算法、板卡或听感测试。
- 已知限制：现有五段男声是否跨日期录制没有证据；该限制由最终新会话验收覆盖，不阻塞电脑端方案启动。
- 报告链接：`report/fallback_one_to_one_assets_20261021.json`、`board/fallback_one_to_one_capture.md`
- 提交或 PR：`agent/Pi-debug-cmd/DOCS-20261021-06`
- 下一责任方：Remote-PS-C、Hardware-A 或 Hardware-B 先追加 `CLAIMED`，再开展 `PS-20261021-10` 的一对一男转女软件音色上限探索。

### [DOCS-20261021-07] 统一当前入口与跨电脑模型交付规则
- 日期：2026-10-21
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED（PR #5 已合并 `main`；仅文档与交付规则通过）
- 基准提交：`d4150311be83d19685be4b89c291799f1679873e`
- 目标与本轮唯一变量：把仍指向旧 `PS-20261021-01`/G1 的入口纠正为 `PS-20261021-10`，并明确 Claude 在另一台电脑做好的模型如何可取回、校验、复现。
- 修改路径：`AGENTS.md`、`ARTIFACTS.md`、`README.md`、`project_guide.md`、`plan.md`、`handoff_20261021.md`、`team_project/README.md`、`team_project/team_roles.md`、`team_project/project_status.md`、`team_project/development_plan.md`、`交接/远端模型交付与接收.md`、`coummucation.md`
- 复现命令：`git -c core.whitespace=cr-at-eol diff --check origin/main...HEAD`（仓库历史 Markdown 为 CRLF）；`python tools/check_collaboration_policy.py --base origin/main --head HEAD`；检查上述入口与 `ARTIFACTS.md` 的 Release/SHA-256 规则。
- 输入与数据切分：未改变；固定男性 1～3 训练、4 验证、5 锁定验收；目标女声 Track 5～8 建模、Track 9 留出。
- 结果：文档统一现行三级路线；规定模型权重不得仅留在某台电脑，候选必须有可下载的私有 Release 资产、完整依赖、逐件 SHA-256 和推理复现说明。补充 Claude 的必读文件、打包内容、Release 目标提交、干净目录取回运行和板卡方独立接收门槛。Git 克隆本身不含模型权重。
- 成功门槛对照：本轮仅修文档，未运行算法、板卡或真人试听，未宣称任何音色、7020 部署或实时门槛通过。
- 已知限制：当前尚无新候选模型或 Release 附件；未来 Claude 仍需依本规则交付，硬件方再验证可部署性。
- 报告链接：`ARTIFACTS.md`、`plan.md`
- 模型产物：无。
- 提交或 PR：`bac29329d4062c74d7ac28d7864e0733aaa84e82`（`main` 合并提交），https://github.com/Pi-debug-cmd/2026_FPGA/pull/5
- 下一责任方：Remote-PS-C 或硬件方先追加 `CLAIMED`，再认领 `PS-20261021-10`。

### [DOCS-20261021-08] 远端电脑非系统盘集中存储约束
- 日期：2026-10-21
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED（PR #6 已合并 `main`；仅存储约束文档通过）
- 基准提交：`bac29329d4062c74d7ac28d7864e0733aaa84e82`
- 目标与本轮唯一变量：落实用户要求，Claude 在另一台电脑克隆、下载和训练前先选择空间充足的非系统盘，把必要的大型项目数据集中在单一项目总目录，尽量避免占用 `C:`。
- 修改路径：`AGENTS.md`、`ARTIFACTS.md`、`README.md`、`handoff_20261021.md`、`project_guide.md`、`交接/远端模型交付与接收.md`、`coummucation.md`
- 复现命令：`git -c core.whitespace=cr-at-eol diff --check origin/main...HEAD`；`python tools/check_collaboration_policy.py --base origin/main --head HEAD`；检查交接清单的根目录、环境变量和 Release 包路径是否一致。
- 远端存储：先检查另一台电脑实际固定盘的剩余容量；盘符未知，不预设 `D:`。选定后把仓库、虚拟环境、数据、模型、缓存、检查点、临时文件、日志及交付包放在同一非系统盘项目总目录；系统工具不可避免的少量配置例外需记录。
- 输入与数据切分：无变化。
- 结果：交接清单增加选盘、容量和缓存重定向步骤；Release 上传示例改用选定的总目录；旧机器绝对路径标为不可照搬。
- 成功门槛对照：本轮仅修文档；未在 Claude 的另一台电脑执行下载、训练或板测，不能声称实际磁盘占用已受控。
- 已知限制：Claude Code/GitHub CLI/系统可能仍在用户配置目录写入少量设置或凭据；不能保证 `C:` 绝对零写入。若非系统盘容量不足，需先向该机操作者确认目标盘位或扩容办法。
- 报告链接：`交接/远端模型交付与接收.md`、`ARTIFACTS.md`
- 模型产物：无。
- 提交或 PR：`0cbb29f2d5434e7faaf201d0dd5ca217c361637f`（`main` 合并提交），https://github.com/Pi-debug-cmd/2026_FPGA/pull/6
- 下一责任方：Remote-PS-C 开工前执行存储步骤并在本文件记录实际选盘；Hardware-A/B 接收模型时独立核对。

### [DOCS-20261021-09] 审查远端交付与存储规则
- 日期：2026-10-21
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED（文档一致性审查完成，不代表模型、音色或板端通过）
- 基准提交：`0cbb29f2d5434e7faaf201d0dd5ca217c361637f`
- 目标与本轮唯一变量：审查 PR #5/#6 合并后的三级路线、任务入口、模型 Release 交付、非系统盘存储和协作状态是否一致，并修正可导致 Agent 误判的文字。
- 修改路径：`AGENTS.md`、`coummucation.md`
- 复现命令：核对 `main` 文件树和 PR #5/#6 diff；检查新文档相对链接；扫描 `PROPOSED`、旧任务入口、`Fixed-B` 与一对一男转女定义；运行 `git diff --check` 和协作策略工作流。
- 远端存储：无；本轮只读 GitHub `main` 和修改文档，没有下载模型或训练资产。
- 输入与数据切分：无变化；固定男性 1～3 训练、4 验证、5 锁定验收，目标女声 Track 5～8 建模、Track 9 留出。
- 结果：三级路线和当前 `PS-20261021-10` 入口正确；PR #5/#6 的仓库内链接检查无缺失。把两条已合并记录从 `PROPOSED` 更新为 `ACCEPTED`，并明确“模型权重不进入 Git 历史，但可按规则进入私有 Release”，消除 `AGENTS.md` 的表面矛盾。
- 成功门槛对照：本轮未运行算法、板卡、Vivado 或真人试听；未改变任何技术门槛。
- 已知限制：远端存储规则尚未在 Remote-PS-C 的实际电脑执行；当前仍无新候选模型或 Release 附件。
- 报告链接：`AGENTS.md`、`ARTIFACTS.md`、`交接/远端模型交付与接收.md`
- 模型产物：无。
- 提交或 PR：`agent/Pi-debug-cmd/DOCS-20261021-09`
- 下一责任方：Remote-PS-C 或硬件方先在本文件追加 `CLAIMED`，再开展 `PS-20261021-10`；Remote-PS-C 同时记录实际非系统盘总目录。

### [PS-20261021-10] WORLD 保底基线音色优化认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（仅电脑端离线算法阶段）
- 状态：CLAIMED
- 基准提交：`2720ebe8f81a12a9cb0df3a4230ef6855c7c72a9`
- 目标与本轮唯一变量：保留 `world_budget_v23` 的实时框架，以固定男性 1～3 训练、4 验证、5 锁定验收和女声 Track 5～8 建模、Track 9 留出的协议，优化音色映射；先做电脑端客观筛选，不操作板卡、不修改 RTL/Vivado。
- 修改路径：计划仅涉及 `src/reference/`、`build/`、`sim/`、`report/` 和本记录；完成后回填实际路径。
- 复现命令：完成后回填。
- 远端存储：无；本轮在 Hardware-A 现有项目工作区执行，不下载新模型或训练资产。
- 输入与数据切分：`Fixed-Male` 标准录音 1～3/4/5 按训练/验证/锁定验收隔离；目标 Track 5～8/9 按建模/锁定留出隔离。
- 结果：待测；基线为身份 0.1903、泄漏 0.1719、UTMOS 2.0354、CER 0.1667。
- 成功门槛对照：身份均值 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；客观门未全部通过不得请求试听或上板。
- 已知限制：既有证据已显示纯参数化 WORLD 身份约在 0.19～0.22；若最小可复现实验仍不能整体改善，将如实 `REJECTED`，不以实时稳定性冒充音色通过。
- 报告链接：完成后回填。
- 模型产物：无；若后续产生权重，另按 `ARTIFACTS.md` 交付。
- 提交或 PR：`agent/Pi-debug-cmd/PS-20261021-10`
- 下一责任方：Hardware-A / Codex 完成本轮离线优化与客观判定。

### [PS-20261021-10] 固定男性 WORLD 延伸优化结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED（本轮 WORLD/A3 延伸路线失败；不代表整个 `PS-20261021-10` 关闭）
- 基准提交：`c5042a3c307dbe165e895b68f3a9a8112460b9a6`
- 目标与本轮唯一变量：保持 v23 实时框架，先搜索固定男性源专用 WORLD 音高/谱形/AP，再把已有 A3 高身份包络与 WORLD 做全频及分频参数融合；不改板卡或 PL。
- 修改路径：`src/reference/world_fixed_male_mapping.py`、`build/optimize_world_fixed_male_20261024.py`、`build/blend_world_a3_fixed_male_20261024.py`、`sim/test_world_fixed_male_mapping.py`、`report/world_fixed_male_optimization_20261024.{md,json}`、`coummucation.md`。
- 复现命令：`python -m unittest sim.test_world_fixed_male_mapping -v`；两个离线脚本命令见报告“实现与复现”；`python -m json.tool report/world_fixed_male_optimization_20261024.json`。
- 远端存储：无；复用本机现有依赖。失败候选 WAV 在忽略目录 `build/generated/`，未提交。
- 输入与数据切分：男性 1～3 建源画像、4 只选参、5 候选冻结后锁定评价；女声 Track 5～8 建目标画像/质心，Track 9 不参与选参。
- 结果：纯 WORLD 锁定句 0.3557/0.2449/1.6258/0.1250（身份/泄漏/UTMOS/CER）；WORLD 0.40 + A3 0.60 锁定句 **0.5650/0.1968/1.9631/0.1000**。后者身份和 CER 通过，但泄漏 >0.10、UTMOS <2.30；未计算跨句 P10。
- 成功门槛对照：未全部通过，禁止试听和上板；不以身份/CER 两项改善替代完整门槛。
- 已知限制：A3 checkpoint 是本机忽略资产，未作为 Release 交付；UTMOS 为域外预测；五个源文件是否跨日期未知；未做真人听感、板卡、实时或 PL 测试。
- 报告链接：`report/world_fixed_male_optimization_20261024.md`、`report/world_fixed_male_optimization_20261024.json`。
- 模型产物：无新权重；未提交或发布失败候选音频。现有本机忽略资产 `a3_content.pt` SHA-256 为 `46ebff5951216b8b63ab7fd7a509c2dc10ddec7dbcbdb93e65fa8490d5d96b13`，`reduced_student_v2/final.pt` SHA-256 为 `5a3f5de6f7bef12a29323be5bb88168025d85080b527933e8f3f54cbf07a9641`；本轮不构成跨电脑模型交付。
- 提交或 PR：结果提交 `fe34f45`；PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)，分支 `agent/Pi-debug-cmd/PS-20261021-10`。
- 下一责任方：Remote-PS-C / GPT+Codex 或任一硬件方另行认领更强语义教师/自然声码器路线；v23 继续只作为板端清楚连续的运行保底。

### [PS-20261021-10] Seed-VC 严格留出上限复验认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`910b4e11d395d8d18f911804723bb6e6e3706be0`
- 目标与本轮唯一变量：停止已证伪的 WORLD/A3 参数融合，复用现有 Seed-VC V2 30 步教师，以男声 1～3 建模、4 选参、5 冻结验收及女声 Track 5～8 条件、Track 9 留出的严格协议，验证高质量教师能否同时通过身份、P10、泄漏、UTMOS、CER 客观门。
- 修改路径：计划新增 Seed-VC 严格切分运行/评测脚本、正式 JSON/Markdown 报告，并追加本文件；不修改板卡、启动项、Vivado、RTL 或 PL。
- 复现命令：完成后在正式报告回填；本轮先核验现有本机忽略资产和历史推理入口。
- 量化结果：待生成；门槛为身份均值 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。
- 限制：电脑端非因果教师约 363M 参数、30 步扩散，只用于第一级音质上限，不能宣称可在 Zynq-7020 实时部署；客观门通过后仍须模型交付与本地真人试听。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 完成本轮严格留出复验并按结果标记 `WAIT_LOCAL_TEST` 或 `REJECTED`。

### [PS-20261021-10] Seed-VC 严格留出上限复验 Round 1
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED（仅本轮候选；任务继续）
- 基准提交：`2060a05`
- 修改路径：`build/run_seed_fixed_male_strict_20261024.py`、`build/evaluate_seed_fixed_male_strict_20261024.py`、`report/seed_fixed_male_strict_round1_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/seed_fixed_male_strict_round1_20261024.md`；固定依赖新增 `opencc-python-reimplemented==0.1.7`，仅装在忽略目录。
- 数据切分：1～3 建源评估质心、4 选参、5 冻结后首次验收；Track 5～8 构造目标提示/质心，Track 9 完全未使用。
- 量化结果：验证 4 为 0.5992/0.5624/0.0979/2.7454/0.1471（身份/P10/严格泄漏/UTMOS/CER），五门通过；锁定 5 为 **0.5784/0.5278/0.1079/2.7941/0.0625**，仅泄漏失败。
- 限制：30 步 363M 级非因果教师，不是 7020 部署候选；无试听、板卡、实时或 PL 结论。录音 5 已用于本轮判定，后续只作回归，最终仍需冻结后的新会话句。
- 报告链接：`report/seed_fixed_male_strict_round1_20261024.md`、`report/seed_fixed_male_strict_round1_20261024.json`。
- 模型产物：复用本机已校验 Seed-VC 资产；无新权重，候选 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：Hardware-A / Codex 开始 Round 2，只用验证录音 4 搜索 Track 5～8 目标提示结构，继续降低泄漏。

### [PS-20261021-10] Seed-VC 目标提示结构优化 Round 2 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`6d52477`
- 唯一变量：保持 Seed-VC V2、30 步、固定男性数据切分和严格评估器不变，只在 Track 5～8 合法开发目标素材内比较多轨提示与高质量 Track 8 单轨提示；只用录音 4 选参。
- 复现命令与量化结果：完成后回填正式报告。
- 限制：录音 5 已在 Round 1 暴露，只能作回归；Round 2 达标后仍需冻结后的新会话句完成最终客观接受。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 完成验证筛选与已暴露回归，不触碰板卡。

### [PS-20261021-10] Seed-VC 目标提示结构优化 Round 2 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：PROPOSED / WAIT_NEW_SESSION（现有文件五门通过；尚未达到最终 `WAIT_LOCAL_TEST`）
- 基准提交：`1bfe3d5`
- 唯一变量：模型、步数、随机种子、源切分和评估器不变，只把多轨 4×2 秒目标提示替换为 Track 8 高活动 1.77～9.77 秒提示。
- 修改路径：`build/run_seed_fixed_male_strict_20261024.py`、`report/seed_fixed_male_prompt_round2_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/seed_fixed_male_prompt_round2_20261024.md`。
- 量化结果：验证录音 4 为 **0.5515/0.5121/0.0753/2.8138/0.1471**；已暴露录音 5 回归为 **0.5336/0.5163/0.0919/2.9340/0.0500**（身份/P10/严格泄漏/UTMOS/CER），两者五门均通过。
- 限制：录音 5 已在 Round 1 暴露，不能再次当独立锁定集；必须采集冻结后的同一男性新会话句。30 步大教师仍非板端候选，无试听、板卡、实时或 PL 结论。
- 报告链接：`report/seed_fixed_male_prompt_round2_20261024.md`、`report/seed_fixed_male_prompt_round2_20261024.json`。
- 模型产物：复用现有 Seed-VC 资产，无新权重；生成 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：现场操作者明确准备后，Hardware-A 采一条冻结后新会话句并只运行一次；通过才制作可复现模型包并转 `WAIT_LOCAL_TEST`。

### [PS-20261021-10] 冻结后新会话客观验收认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：CLAIMED（操作者已明确回复“准备好了”，仅授权本轮录音）
- 基准提交：`607d1ea`
- 操作范围：短暂停止当前 v23 自启动录放服务，播放 300 ms 提示音、等待 150 ms 后采集同一男性 20 秒新会话；采集后恢复同一 v23 自启动服务与最大音量配置。冻结 Seed-VC 参数只运行一次。
- 端口与预检：CH340 `COM4` 已握手为 Zynq/PetaLinux；当前 PCM 被 `/opt/world_voice/world_voice_autostart.sh` 管理的 v23 占用，已只读确认其 TERM 陷阱会停止子进程并恢复 mixer。
- 数据规则：新录音、转换 WAV 和原始串口日志留在忽略目录，不加入 Git；正式报告只记录 SHA、格式、量化指标和结论。
- 成功门槛：身份均值 ≥0.45、P10 ≥0.35、严格泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；任一失败不请求试听。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A 完成本次采录、恢复板上服务并运行冻结候选客观评测。

### [PS-20261021-10] 冻结后新会话客观验收 Round 3 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：REJECTED（仅本轮冻结候选；任务继续）
- 基准提交：`607d1ea`
- 修改路径：`board/capture_fixed_male_new_session.py`、`report/seed_fixed_male_new_session_round3_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/seed_fixed_male_new_session_round3_20261024.md`；使用 CPython 3.12 `-S` 隔离系统 `torchvision`，参数保持 Round 2 冻结值。
- 数据与板卡：现场新录 20 秒，WAV SHA-256 `fd4aaf53a7637cccf458442feffe8232d3e8ca9317da69d332666e3babb02db2`；真人音频和串口日志未提交。采集后已恢复单实例 v23 最大音量自启动，录放 PCM 均为 `RUNNING`。
- 量化结果：**0.5007/0.4431/0.1223/2.8356/0.1148**（身份/P10/严格泄漏/UTMOS/CER）；只有泄漏超过 `0.10` 上限，其余四门通过。
- 限制：本条新会话从本轮起已暴露，只能用于回归；不得据此调参后再次充当盲测。未试听，未产生实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/seed_fixed_male_new_session_round3_20261024.md`、`report/seed_fixed_male_new_session_round3_20261024.json`。
- 模型产物：复用本机 Seed-VC 资产，无新权重；生成 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：Hardware-A / Codex 只用既有开发与已暴露录音做下一轮结构优化；重新冻结后必须另采全新会话才能最终接受。

### [PS-20261021-10] Seed-VC 目标提示时长优化 Round 4 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`01fa299`
- 唯一变量：保持 Seed-VC V2、30 步、CFG、随机种子、严格评估器和 Track 8 目标素材不变，仅在录音 4 上比较目标高活动提示时长；不使用本次新会话做选择。
- 复现与门槛：完成后写入正式报告；门槛仍为身份均值 ≥0.45、P10 ≥0.35、严格泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。
- 限制：录音 5 与 Round 3 新会话只能在候选选定后做已暴露回归；通过回归仍需另一条冻结后的全新会话。无板卡、试听、实时、Vivado、RTL 或 PL 工作。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 完成目标提示时长筛选、回归与可复现提交。

### [PS-20261021-10] Seed-VC 目标提示时长优化 Round 4 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED（仅本轮候选；任务继续）
- 基准提交：`547cc66`
- 唯一变量：Track 8 高活动提示由 8 秒增加到 12 秒；模型、30 步、CFG=1.10、随机种子和评估器不变。
- 修改路径：`build/run_seed_fixed_male_strict_20261024.py`、`report/seed_fixed_male_prompt_round4_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/seed_fixed_male_prompt_round4_20261024.md`。
- 量化结果：验证录音 4 为 **0.5837/0.5441/0.0644/2.9656/0.1912**（身份/P10/严格泄漏/UTMOS/CER）；仅 CER 超过 `0.15` 上限。
- 限制：只使用录音 4；未运行录音 5 或 Round 3 新会话回归。无试听、板卡、实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/seed_fixed_male_prompt_round4_20261024.md`、`report/seed_fixed_male_prompt_round4_20261024.json`。
- 模型产物：复用现有 Seed-VC 资产，无新权重；生成 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：Hardware-A / Codex 固定 12 秒提示，另开一轮只调整 CFG，尝试恢复 CER 且保留泄漏余量。

### [PS-20261021-10] Seed-VC 12 秒提示 CFG 优化 Round 5 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`528244d`
- 唯一变量：固定 Track 8 高活动 12 秒提示、Seed-VC V2、30 步、seed=20261018 和严格评估器，只在验证录音 4 上提高 CFG，目标是把 CER 恢复到 ≤0.15，同时保持严格泄漏 ≤0.10。
- 数据纪律：只用录音 4 选 CFG；录音 5 与 Round 3 新会话只在候选选定后做已暴露回归，不作为选择依据。
- 限制：通过回归仍需冻结后的另一条全新会话；无试听、板卡、实时、Cortex-A9、Vivado、RTL 或 PL 工作。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 完成 CFG 筛选并按结果提交。

### [PS-20261021-10] Seed-VC 12 秒提示 CFG 优化 Round 5 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED（仅本轮候选；任务继续）
- 基准提交：`88afa2a`
- 唯一变量：固定 Track 8 高活动 12 秒提示、30 步、seed=20261018，只在录音 4 上比较 CFG 1.10/1.25/1.40/1.70。
- 修改路径：`report/seed_fixed_male_cfg_round5_20261024.{md,json}`、`coummucation.md`；运行器沿用 Round 4 的 `track8_active12`。
- 复现命令：见 `report/seed_fixed_male_cfg_round5_20261024.md`。
- 量化结果：验证录音 4 的 CFG 1.70 为 **0.5912/0.5527/0.0671/2.8428/0.1471**，五门通过；冻结后录音 5 回归为 **0.5621/0.5122/0.0664/2.9805/0.0375**，五门通过；Round 3 已暴露新会话回归为 **0.5078/0.4728/0.0661/2.7222/0.9672**，CER 严重失败，ASR 仅“正确的正确的”。
- 用户反馈：原话“刚刚进行了两段试音，我觉得第一个改进好些，第二就没什么改进”，并澄清是在验收提示音后说话时听到转换。该声音来自恢复后的 v23 板端保底，本轮 Seed-VC 未播放或部署，因此不归因到 CFG 候选。
- 限制：录音 5 与 Round 3 新会话均为已暴露回归；未采新盲测。无 Seed-VC 试听、板卡候选、实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/seed_fixed_male_cfg_round5_20261024.md`、`report/seed_fixed_male_cfg_round5_20261024.json`。
- 模型产物：复用现有 Seed-VC 资产，无新权重；生成 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：Hardware-A / Codex 转向输入稳健性或 8～12 秒提示折中，不再继续提高 CFG。

### [PS-20261021-10] Seed-VC 10 秒提示折中 Round 6 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`5ae158b`
- 方案：在 8 秒提示“新会话内容通过但泄漏失败”和 12 秒提示“泄漏通过但高 CFG 内容塌缩”之间，新增 Track 8 高活动 10 秒提示；只在录音 4 上筛选 CFG，再冻结做已暴露回归。
- 数据纪律：录音 4 选参；录音 5 与 Round 3 新会话只做冻结后回归。若三者均过，仍须另一条全新会话最终接受。
- 门槛：身份均值 ≥0.45、P10 ≥0.35、严格泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。
- 限制：无试听、板卡、实时、Cortex-A9、Vivado、RTL 或 PL 工作；板上继续运行 v23 最大音量保底。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 完成 10 秒提示筛选与回归。

### [PS-20261021-10] Seed-VC 10 秒提示折中 Round 6 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：PROPOSED / WAIT_NEW_SESSION（现有三组数据五门通过；尚未达到最终 `WAIT_LOCAL_TEST`）
- 基准提交：`34a3beb`
- 方案与选择：新增 Track 8 高活动 10 秒提示，在录音 4 比较 CFG 1.10/1.40/1.70；按“通过五门的最低 CFG”冻结 1.10，seed=20261018、30 步不变。
- 修改路径：`build/run_seed_fixed_male_strict_20261024.py`、`report/seed_fixed_male_prompt_round6_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/seed_fixed_male_prompt_round6_20261024.md`。
- 量化结果：验证录音 4 为 **0.5810/0.5581/0.0678/2.8604/0.1471**；已暴露录音 5 为 **0.5591/0.4879/0.0903/2.8988/0.0500**；Round 3 已暴露新会话为 **0.4818/0.4174/0.0679/2.7261/0.0984**（身份/P10/严格泄漏/UTMOS/CER），三组均五门通过。
- 限制：录音 5 与 Round 3 新会话均已暴露，只能作回归；参数冻结后仍须另一条全新会话最终客观接受。未试听、未部署 Seed-VC，无实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/seed_fixed_male_prompt_round6_20261024.md`、`report/seed_fixed_male_prompt_round6_20261024.json`。
- 模型产物：复用现有 Seed-VC 资产，无新权重；生成 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：现场操作者再次明确准备后，Hardware-A 采另一条不同文本的新会话，只运行冻结候选一次；通过后再处理可复现模型交付与真人试听。

### [PS-20261021-10] Round 6 冻结后第二条新会话客观验收认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：CLAIMED（操作者已对本轮明确回复“准备好了”）
- 基准提交：`7a22ff0`
- 冻结候选：Seed-VC V2、30 步、CFG=1.10、seed=20261018、Track 8 高活动 10 秒提示；本轮不再调参，只运行一次。
- 操作范围：短暂停止 v23 自启动录放服务，播放 300 ms 提示音、等待 150 ms 后采集同一男性 20 秒不同文本；随后恢复同一 v23 最大音量自启动服务。
- 数据规则：新录音、转换 WAV 和串口日志只放 `build/generated/` 忽略目录；正式报告仅记录 SHA、格式、量化指标与结论。
- 成功门槛：身份均值 ≥0.45、P10 ≥0.35、严格泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；任一失败不请求 Seed-VC 试听。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A 完成本轮采录、恢复板上服务并运行冻结候选一次。

### [PS-20261021-10] Round 6 冻结后第二条新会话客观验收 Round 7 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：REJECTED（仅本轮冻结候选；任务继续）
- 基准提交：`8dc1c6a`
- 修改路径：`board/capture_fixed_male_new_session.py`、`report/seed_fixed_male_new_session_round7_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/seed_fixed_male_new_session_round7_20261024.md`；冻结参数只运行一次。
- 数据与板卡：现场新录 20 秒，WAV SHA-256 `da1737af90da8ebeb0578719816e6d381fcfe74469d1a9f18519d250ef78fa3e`；真人音频和串口日志未提交。采集后恢复单实例 v23；发现 mixer 快照回退后已纠正为 Headphone 127 / Playback 255，录放 PCM 均为 `RUNNING`。
- 量化结果：**0.4334/0.2491/0.1067/2.5821/0.1538**（身份/P10/严格泄漏/UTMOS/CER）；除 UTMOS 外四门失败。第一窗身份 `0.1529`、UTMOS `1.9587`，后续三窗身份均 ≥`0.4736`。
- 限制：本条新会话已经暴露，只能用于回归；不得针对它调参后再次当盲测。未试听 Seed-VC，无实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/seed_fixed_male_new_session_round7_20261024.md`、`report/seed_fixed_male_new_session_round7_20261024.json`。
- 模型产物：复用本机 Seed-VC 资产，无新权重；生成 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：Hardware-A / Codex 先诊断并修复起始窗稳健性，再冻结新候选；最终仍需另一条全新会话。

### [PS-20261021-10] 持续语音起点裁切 Round 8 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`a5ec1b1`
- 根因证据：Round 7 源录音前约 8 秒没有持续语音，仅首 0.5 秒存在瞬态；冻结输出第一窗身份 `0.1529`、UTMOS `1.9587`，后三窗身份均 ≥`0.4736`。
- 唯一变量：保持 Seed-VC、10 秒提示、CFG=1.10、30 步、随机种子和严格评估器不变，仅在推理输入端加入确定性的持续语音起点检测与少量前滚保留，不改变评估门槛或评估器。
- 回归范围：录音 4、录音 5、Round 3 新会话和 Round 7 新会话均已暴露，只用于开发/回归；新候选冻结后仍需另一条全新会话最终接受。
- 限制：无试听、板卡、实时、Cortex-A9、Vivado、RTL 或 PL 工作；板上继续运行 v23 最大音量保底。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 实现并验证持续语音起点裁切，按结果提交。

### [PS-20261021-10] 持续语音起点裁切 Round 8 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：PROPOSED / WAIT_NEW_SESSION（四组已暴露数据五门通过；尚未达到最终 `WAIT_LOCAL_TEST`）
- 基准提交：`a0dd298`
- 唯一变量：推理输入增加持续语音起点检测；20 ms 帧、-40 dBFS、2 秒窗、30% 活动帧、250 ms 前滚，且只有裁切量 ≥2 秒才启用。模型、10 秒提示、CFG=1.10、30 步、随机种子和评估器不变。
- 修改路径：`build/run_seed_fixed_male_strict_20261024.py`、`report/seed_fixed_male_onset_round8_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/seed_fixed_male_onset_round8_20261024.md`。
- 量化结果：录音 4 为 **0.5810/0.5581/0.0678/2.8604/0.1471**；录音 5 为 **0.5591/0.4879/0.0903/2.8988/0.0500**；Round 3 新会话为 **0.4883/0.4340/0.0560/2.6624/0.0820**；Round 7 新会话为 **0.5828/0.5512/0.0628/2.8588/0.1154**（身份/P10/严格泄漏/UTMOS/CER），四组均五门通过。
- 失败探测：初版裁录音 5 的 0.57 秒导致 CER `0.1875`，已拒绝；最终规则的 2 秒最小裁切使其保持不裁。
- 限制：四组数据均已暴露，只能作开发/回归；规则冻结后仍须另一条全新会话。未试听、未部署 Seed-VC，无实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/seed_fixed_male_onset_round8_20261024.md`、`report/seed_fixed_male_onset_round8_20261024.json`。
- 模型产物：复用现有 Seed-VC 资产，无新权重；生成 WAV 未提交或发布。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：现场操作者再次明确准备后，Hardware-A 用不同文本采一条冻结后新会话并只运行一次；通过后再处理模型交付与真人试听。

### [PS-20261021-10] Round 8 冻结后第三条新会话客观验收认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：CLAIMED（操作者已对本轮明确回复“准备好了”）
- 基准提交：`601eb17`
- 冻结候选：Seed-VC V2、30 步、CFG=1.10、seed=20261018、Track 8 高活动 10 秒提示，以及 Round 8 的持续语音起点裁切规则；本轮不再调参，只运行一次。
- 操作范围：短暂停止 v23 自启动录放服务，播放 300 ms 提示音、等待 150 ms 后采集同一男性 20 秒不同文本；随后恢复同一 v23 最大音量自启动服务。
- 数据规则：新录音、转换 WAV 和串口日志只放 `build/generated/` 忽略目录；传输真人录音仍需本轮单独明确授权。
- 成功门槛：身份均值 ≥0.45、P10 ≥0.35、严格泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；任一失败不请求 Seed-VC 试听。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A 完成本轮采录、恢复板上服务；获得传输授权后只运行冻结候选一次。

### [PS-20261021-10] Round 8 冻结候选第三条新会话 Round 9 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED_OBJECTIVE / WAIT_MODEL_DELIVERY（电脑端五项客观门通过；模型尚未完成跨电脑交付，暂不标记 `WAIT_LOCAL_TEST`）
- 基准提交：`015304f`
- 修改路径：`report/seed_fixed_male_new_session_round9_20261024.{md,json}`、`coummucation.md`；真人录音、生成 WAV 和串口日志均在忽略目录，未提交。
- 冻结候选：Seed-VC V2、30 步、CFG=1.10、seed=20261018、Track 8 高活动 10 秒提示和 Round 8 持续语音起点裁切；本轮只运行一次，未调参。
- 采录与授权：操作者先确认准备，再单独授权传输；20 秒 WAV SHA-256 `72ab2217f1480e5241cd28d41f3c7c4ba3f286d428ad69f9a27793c448d45876`，冻结裁切起点 `5.95 s`。
- 复现命令：见 `report/seed_fixed_male_new_session_round9_20261024.md`。
- 量化结果：**0.5200/0.4719/0.0591/3.0789/0.1020**（身份/P10/严格泄漏/UTMOS/CER），相对门槛 ≥0.45/≥0.35/≤0.10/≥2.30/≤0.15，五门全部通过；输出 SHA-256 `f6880252d63839e7ba64b5141a7d3babd6cdc2ddd451915ca99062622234d0ac`。
- 板端状态：采录后恢复单实例 v23 自启动保底，录放 PCM 均为 `RUNNING`；Headphone 127、Playback 255，均为最大音量。Seed-VC 未部署到板上。
- 限制：本结论仅为电脑端非因果离线客观接受；无真人听感、Cortex-A9、板端实时、Vivado、RTL 或 PL 通过结论。
- 报告链接：`report/seed_fixed_male_new_session_round9_20261024.md`、`report/seed_fixed_male_new_session_round9_20261024.json`。
- 模型产物：复用本机 Seed-VC 资产；尚未按私有 Release 规则完成完整权重、依赖与干净下载复现，故不宣称模型已交付。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：Hardware-A / Codex 按 `ARTIFACTS.md` 与 `交接/远端模型交付与接收.md` 完成模型交付并验证；随后再请求现场操作者准备真人试听。

### [PS-20261021-10] Round 9 下一责任方纠正
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED_OBJECTIVE / WAIT_LOCAL_LISTENING
- 基准提交：`5352c3c`
- 纠正：上一条把 Remote-PS-C 候选的跨电脑交付规则误套到 Hardware-A 已在本机完整运行的候选。用户明确：第三位无环境、无板卡合作者只运行独立电脑端测试，不负责复现或验证本方案。
- 影响：Round 9 五门客观通过结论、冻结参数、SHA 和板端 v23 状态均不变；停止本候选的模型打包与 Release 工作，不把 Remote-PS-C 设为验证方。
- 修改路径：`report/seed_fixed_male_new_session_round9_20261024.{md,json}`、`coummucation.md`。
- 下一责任方：Hardware-A 在现场操作者对本次播放再次明确准备后，进行本机候选真人试听；Remote-PS-C 继续其独立电脑端任务。
