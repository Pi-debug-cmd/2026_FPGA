# Agent 协作窗口

### [PS-20261025-20] Remote-PS-C 配对语料交付修复认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（资产交付，不运行 Remote-PS-C 方案）
- 状态：CLAIMED
- 基准提交：`ba48816b449a256bc5a331476999831b3ee444f6`
- 问题：PR #11 已恢复并校验 FARGAN、UTMOS 与 Whisper；真正阻塞仅剩 HuBERT→FARGAN 同内容配对语料。Remote-PS-C 的 clone 不包含这些被 Git 忽略的大型资产。
- 本机证据：受控资产区存在 `fargan_corpus_expanded`（240 train/8 validation）和 `full_train_corpus_16k`（192 train/8 validation），两份 manifest 均为 `complete=true`；这些目录未被 Git 跟踪。
- 本轮目标：从本机受控资产生成仅含 Remote-PS-C 所需 200 对的便携归档、相对路径 manifest、逐文件 SHA-256 和校验脚本，上传私有 Release，并在 PR #11 提供下载恢复命令。
- 数据边界：不上传额外真人录音；只交付项目已有 CosyVoice3 teacher 配对资产。Track 9 不进入训练或选参。
- 限制：不替 Remote-PS-C 训练、推理或给出质量结论；不接触板卡、Vivado、RTL、PL、播放或录音。
- 下一责任方：Hardware-A / Codex 完成可重复下载的资产交付；Remote-PS-C 在自己的非系统盘干净目录校验后解除 BLOCKED。

### [PS-20261025-20] Remote-PS-C 配对语料便携包
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（资产交付，不运行 Remote-PS-C 方案）
- 状态：PROPOSED
- 基准提交：`ba48816b449a256bc5a331476999831b3ee444f6`
- 改动路径：`tools/package_remote_ps_c_fargan_corpus.py`、`report/ps_20261025_20_paired_corpus_delivery_20261026.{md,json}`
- 结果：生成 200 对（192 train / 8 validation）便携语料，含 800 个数据文件；ZIP 为 `125109914` bytes，SHA-256 `956dead3c76b1e214cc6baf5a1dca0b7e083eebb2771e417b722df6e2181366c`。
- 复现命令：见 `report/ps_20261025_20_paired_corpus_delivery_20261026.md`；新目录本机解包校验输出 `PASS 200 800`。
- 限制：本轮仅修复跨电脑资产缺口；未运行训练/推理/客观评测，未宣称试听、Cortex-A9、PL、板卡或实时通过。
- 下一责任方：Hardware-A 发布私有 Release 并从 Release 空目录下载复验；通过后 Remote-PS-C 从 PR #11 继续训练与离线客观评测。

### [PS-20261025-20] 私有 Release 下载复验
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（资产交付验证）
- 状态：ACCEPTED（仅指资产交付完整性）
- 基准提交：`2888c7cb6abff1547aff451d082e8db686a6bc08`
- Release：`asset-PS-20261025-20-paired-corpus-v1`，附件 `PS-20261025-20_paired_hubert_fargan_corpus_v1.zip`
- 量化结果：GitHub 与全新下载文件均为 `125109914` bytes、SHA-256 `956dead3c76b1e214cc6baf5a1dca0b7e083eebb2771e417b722df6e2181366c`；解包后校验 `PASS 200 800`。
- 复现命令与证据：`report/ps_20261025_20_paired_corpus_delivery_20261026.{md,json}`。
- 限制：ACCEPTED 只表示 Release 可下载且逐文件完整，不表示训练、音质、试听、板卡、PL 或实时通过。
- 下一责任方：Remote-PS-C 下载校验后解除“缺配对语料”阻塞，在 PR #11 继续其独立训练和客观评测；达到客观门后标记 `WAIT_LOCAL_TEST`。

### [DOCS-20261025-01] 三写作者按候选方案分流认领
- 日期：2026-10-25
- 角色/Agent：Maintainer / Codex
- 状态：CLAIMED
- 基准提交：`c3175e8`
- 目标与本轮唯一变量：不改变第一级保底出口门，只把三位写作者从“共同看到同一开放任务”改为“同阶段、不同算法候选”固定分流，并要求启动时检查开放 PR。
- 计划分流：Hardware-A 继续 WORLD 学习型保底；Hardware-B 负责 Seed-VC 目标条件/男声残留修复；Remote-PS-C 独立负责 HuBERT teacher→FARGAN 电脑端上限，不复现或验证两名硬件方方案。
- 限制：本轮只改协作入口和任务队列，不宣称任何候选通过，不启动板卡、训练、试听或 PL。
- 下一责任方：Maintainer / Codex 更新 `AGENTS.md`、`plan.md`、`project_guide.md` 和本协作窗口后提交 PR。

### [DOCS-20261025-01] Seed-VC 分流错误纠正
- 日期：2026-10-25
- 角色/Agent：Maintainer / Codex
- 状态：CORRECTED（覆盖本任务上一条中的 Seed-VC 分配，不改写历史记录）
- 纠正依据：Seed-VC 已被真人试听明确否决为“男声残留明显、没有更像目标女声”；`report/quality_exploration_ps_round_20261019.md` 也规定不再作为质量主线。客观旧排名不能覆盖真人否决。
- 正确分流：Hardware-A 继续配对 HuBERT→WORLD 因果 GRU；Remote-PS-C 独立负责 HuBERT teacher→FARGAN；Hardware-B 负责固定男性平行数据 GMM/DIFFGMM→WORLD 的板端友好候选。
- 淘汰锁：Seed-VC、A3、direct-20D/LLVC→FARGAN 只保留历史对照，除非用户明确重新开放，否则任何写作者不得认领继续优化。
- 限制：尚未修改正式任务矩阵；本条只立即消除错误分配，避免其他协作者误领。
- 下一责任方：Maintainer / Codex 按纠正后的三路更新协作入口。

### [DOCS-20261025-01] 三写作者按候选方案分流结果
- 日期：2026-10-25
- 角色/Agent：Maintainer / Codex
- 状态：PROPOSED（待 Maintainer 合并后对所有协作者生效）
- 基准提交：`9a63aec`
- 修改路径：`AGENTS.md`、`plan.md`、`project_guide.md`、`report/candidate_lane_split_20261025.md`、`coummucation.md`。
- 结果：Hardware-A 固定负责 `PS-20261021-10` 配对 HuBERT→WORLD；Remote-PS-C 独立负责 `PS-20261025-20` HuBERT teacher→FARGAN；Hardware-B 固定负责 `PS-20261025-21` 平行 GMM/DIFFGMM→WORLD。
- 防重规则：启动时必须同时拉取 main 和检查开放 PR；只能认领分配给自己的路线，换线须 Maintainer 明确重新分配。
- 淘汰锁：Seed-VC、A3、direct-20D/LLVC→FARGAN 禁止重新认领；Seed-VC 的旧客观高分不得覆盖真人否决。
- 阶段边界：三路只在第一级电脑端音色候选阶段并行；各自五门通过前不启动该路线的 Cortex-A9、试听或 PL。Remote-PS-C 不负责复现或验证硬件方方案。
- 复现命令：`git diff --check`；`python tools/check_collaboration_policy.py --base origin/main --head HEAD`。
- 报告链接：`report/candidate_lane_split_20261025.md`。
- 下一责任方：Maintainer 合并当前 PR；三位写作者随后只认领各自任务编号。

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

### [PS-20261021-10] HuBERT→WORLD 学习式保底教师上限 Round 20 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`2ce53c5`
- 目标：冻结 HuBERT Base 内容表示，只用既定女声 Tracks 5～8 训练目标 WORLD 参数预测器，并以未参与训练或选参的 Track 9 检验目标女声重建上限；通过上限后才允许进入固定男性输入转换与因果小学生蒸馏。
- 数据边界：Tracks 5～8 为训练集，Track 9 为一次性锁定验证；固定男性录音不参与本轮目标解码器训练。不得使用源频谱残差、源频谱跳连或 Track 9 选参。
- 资产：复用本机 `交接/核心材料/neural_reference/RVC/assets/hubert_base`，`pytorch_model.bin` SHA-256 `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`；不下载或替换权重。
- 决策门：沿用身份均值 ≥0.45、P10 ≥0.35、严格源泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；目标重建上限还必须明确报告 WORLD 特征误差、Track 9 重建 SHA 和是否存在训练/验证泄漏。任一核心门失败即记录失败，不请求试听。
- PL 边界：HuBERT 只作为电脑端教师，不宣称部署到 Zynq-7020；教师上限通过后才设计只含因果卷积/线性/定点友好算子的学生与 PL 划分。
- 限制：本轮不录音、不播放、不访问板卡、不修改 v23 最大音量上电保底；无 Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。Remote-PS-C 不负责本方案板端验证。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 完成数据/特征接口审计、确定性干跑与一次冻结教师训练，按结果提交。

### [PS-20261021-10] HuBERT→WORLD 学习式保底教师上限 Round 20 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`27226b0`
- 修改路径：`build/train_hubert_world_teacher_round20_20261025.py`、`report/hubert_world_teacher_round20_20261025.{md,json}`、`coummucation.md`。
- 方案：冻结 HuBERT Base 第 9 隐层；Track 5～8 训练 361,419 参数 MLP 预测 WORLD 的 60 维 log-SP DCT、log-F0/VUV/能量和 12 维 AP DCT；无源频谱残差或跳连。Track 9 不参与 PCA、归一化、裁剪边界或训练。
- 复现命令：见 `report/hubert_world_teacher_round20_20261025.md`；checkpoint、WAV 和原始评估保存在忽略目录 `build/generated/hubert_world_round20_20261025/`。
- 量化结果：修复 VUV 概率/logit 接口后，Track 9 重建为 **0.5986/0.5691/0.1471/1.3548/0.4348**（身份/P10/固定男性泄漏/UTMOS/CER）；身份两门通过，泄漏、UTMOS、CER 失败。首次全有声错误输出为 `0.6004/0.5788/0.1391/1.3652/0.3587`，同样失败。
- 判定：拒绝当前“帧独立小 MLP直接回归完整 WORLD 参数”的教师；不请求试听、不进入固定男性转换、学生蒸馏或 PL。下一轮应先提升目标 WORLD 声学解码上限，优先时序解码和分离的 VUV/AP 目标，而不是调整板端参数。
- 数据纪律：Track 9 已完成一次失败评估并因 VUV 接口修复再次回归，现已暴露；后续只能作开发回归，不能再称最终盲测。正式接受仍需新的同目标素材或预先冻结的未触碰片段。
- 限制：未录音、未播放、未访问板卡，v23 最大音量上电保底不变；无 Cortex-A9、实时、Vivado、RTL 或 PL 新结论。Remote-PS-C 不负责本方案板端验证。
- 报告链接：`report/hubert_world_teacher_round20_20261025.md`、`report/hubert_world_teacher_round20_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交本失败轮；随后以同一任务号另行认领时序 WORLD 教师 Round 21。

### [PS-20261021-10] HuBERT 内容检索→WORLD 时序教师 Round 21 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`00990cf`
- 根因证据：Round 20 身份 `0.5986` 已过门，但 UTMOS `1.3548`、CER `0.4348`，证明帧独立 MLP 回归完整 WORLD 参数抹掉清音、瞬态和细节。
- 唯一路线变化：保持同一冻结 HuBERT、Track 5～8 目标库、WORLD 表示和无源频谱跳连约束；改为在 HuBERT 内容空间检索真实目标 WORLD 帧，并用确定性的邻居加权与时序连续性抑制跳变，不训练新的声学回归器。
- 数据纪律：Track 9 已在 Round 20 暴露，本轮只作开发回归，不得标为盲测或最终接受；固定男性输入仅在目标重建上限过门后才运行。参数只由 Track 5～8 和预先冻结常量决定。
- 止损：若 Track 9 回归的身份、泄漏、UTMOS、CER任一核心门失败，即提交失败，不请求试听、不进入学生蒸馏或 PL。
- 限制：不录音、不播放、不访问板卡、不修改 v23 最大音量上电保底；无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 完成确定性 kNN-WORLD 教师、严格评估并按结果提交。

### [PS-20261021-10] HuBERT 内容检索→WORLD 时序教师 Round 21 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`122c114`
- 修改路径：`build/run_hubert_world_retrieval_round21_20261025.py`、`report/hubert_world_retrieval_round21_20261025.{md,json}`、`coummucation.md`。
- 方案：Tracks 5～8 建立 4,953 帧目标 HuBERT/WORLD 库；k=4 内容近邻加权检索真实目标 WORLD 参数，无源频谱跳连、不训练新回归器。
- 量化结果：Track 9 已暴露回归为 **0.6749/0.6613/0.1545/1.3833/0.3261**（身份/P10/固定男性泄漏/UTMOS/CER）；身份两门通过，泄漏、UTMOS、CER 失败。相对 Round 20，身份与 CER 改善，但离门槛仍远。
- 判定：独立帧近邻能增强目标身份，但跨句拼帧连续性不足；拒绝，不通过调 k 继续搜索。后续仅允许段级/路径级连续检索或序列解码器新轮次。
- 数据纪律：Track 9 已暴露，只能作开发回归；无最终盲测结论。
- 限制：未录音、未播放、未访问板卡，v23 最大音量上电保底不变；无 Cortex-A9、实时、Vivado、RTL 或 PL 新结论。
- 报告链接：`report/hubert_world_retrieval_round21_20261025.md`、`report/hubert_world_retrieval_round21_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交失败轮并设计路径级连续检索；通过目标重建上限前不进入板端阶段。

### [PS-20261021-10] HuBERT→WORLD 路径级连续检索 Round 22 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`7672da8`
- 根因证据：Round 21 的逐帧 k=4 检索将身份提高到 `0.6749`、CER 降到 `0.3261`，但 UTMOS 仅 `1.3833`；真实目标帧有效，主要问题转为跨句独立拼帧造成的时序不连续。
- 方案：每个输入 HuBERT 帧保留固定数量候选，以动态规划选择目标帧路径；同一目标轨内近似顺序前进成本最低，跨轨或大跳转付固定惩罚，并只在路径跳点做短时特征平滑。仍直接取真实目标 WORLD 参数，无源频谱跳连。
- 选参边界：连续性惩罚与跳点平滑常量只用 Track 5～8 内部留一轨交叉验证冻结；Track 9 已暴露，仅在冻结后作一次开发回归，不参与选择。
- 止损：若相对 Round 21 未同时提高 UTMOS 与 CER，或任一严格核心门失败，则提交失败，不扩大候选数/惩罚网格，不请求试听或进入学生/PL。
- 限制：不录音、不播放、不访问板卡、不修改 v23 最大音量上电保底；无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 实现留一轨路径选择、冻结参数并运行严格回归。

### [PS-20261021-10] HuBERT→WORLD 路径级连续检索 Round 22 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`d47a86f`
- 修改路径：`build/run_hubert_world_path_round22_20261025.py`、`report/hubert_world_path_round22_20261025.{md,json}`、`coummucation.md`。
- 选参结果：仅用 Track 5～8 四折留一；惩罚 `0/0.10/0.25/0.50/1.00` 的均值分数为 `0.9917/1.0181/1.0309/1.0369/1.0454`，冻结选择 `0.0`。非零约束降低跳转率但持续增加声学误差。
- 量化结果：已暴露 Track 9 为 **0.7108/0.6894/0.1757/1.4125/0.4783**（身份/P10/固定男性泄漏/UTMOS/CER）；身份两门通过，泄漏、UTMOS、CER 失败，且 CER 相对 Round 21 恶化。
- 判定：拒绝路径级检索；不扩大候选或惩罚网格。下一轮必须改用连续序列解码器并分离建模 VUV/能量/AP。
- 限制：用户已关闭板卡；本轮未要求上电、未录音、未播放、未访问板卡，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 报告链接：`report/hubert_world_path_round22_20261025.md`、`report/hubert_world_path_round22_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交失败轮；评审序列解码器最小设计后另行认领。

### [PS-20261021-10] HuBERT→WORLD 因果 GRU 序列教师 Round 23 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`eeaf7f3`
- 根因证据：Round 20 帧独立 MLP 丢失动态，Round 21/22 检索虽将身份最高提高到 `0.7108`，但逐帧拼接或连续路径均无法兼顾内容与自然度；Round 22 CER `0.4783`、UTMOS `1.4125`。
- 方案：冻结同一 HuBERT/PCA 输入，按 5 ms WORLD 帧训练两层单向 GRU 序列解码器；谱包络、连续 log-F0、能量和 AP 用归一化回归头，VUV 用独立 BCE logit，并加入一阶动态损失。无源频谱残差、源谱跳连或未来方向 GRU。
- 数据与选择：仅 Track 5～8；每轨前 80% 训练、后 20% 内部验证并早停。Track 9 已暴露，只在模型冻结后作开发回归，不参与 PCA、归一化、早停或超参数选择。
- PL 边界：本轮只判教师声学上限；GRU 不直接宣称可上板。过门后再蒸馏为定点友好的因果 TCN/小 GRU，并单独评估 PL 资源。
- 止损：Track 9 严格五门任一失败即提交结果，不请求试听、不运行固定男性转换、不接触板卡。
- 限制：用户已关闭板卡；本轮无需上电、录音或播放，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 实现确定性训练、验证因果性并运行一次冻结回归。

### [PS-20261021-10] HuBERT→WORLD 因果 GRU 序列教师 Round 23 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`9f8e435`
- 修改路径：`build/train_hubert_world_causal_gru_round23_20261025.py`、`report/hubert_world_causal_gru_round23_20261025.{md,json}`、`coummucation.md`。
- 训练结果：477,771 参数两层单向 GRU；第 100 步内部验证最佳 `0.4007`，第 900 步早停并恢复最佳；因果前缀差异 `0.0`。
- 量化结果：已暴露 Track 9 为 **0.5622/0.5463/0.1567/1.3388/0.3804**（身份/P10/固定男性泄漏/UTMOS/CER）；身份两门通过，后三门失败。
- 判定：拒绝；谱包络误差下降但能量/AP 误差和过拟合仍严重。下一轮先验证当前 60D SP/12D AP 表示的无模型 WORLD 重建上限，不再直接更换网络。
- 限制：板卡保持关机；未录音、未播放、未访问板卡，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 报告链接：`report/hubert_world_causal_gru_round23_20261025.md`、`report/hubert_world_causal_gru_round23_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交失败轮；随后另行认领 WORLD 表示 oracle。

### [PS-20261021-10] WORLD 表示压缩上限 Round 24 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`51b689b`
- 目标：隔离判断 Round 20～23 的低自然度是否首先受当前 60 维谱包络 DCT/12 维 AP DCT 表示限制，而不是继续更换预测网络。
- 固定对照：同一已暴露 Track 9，仅比较完整 WORLD 参数重建、SP60/AP12、SP120/AP24、SP180/AP48；所有候选使用 Track 9 自身真实 F0/VUV/能量，不含 HuBERT、映射器、源频谱或目标训练。
- 决策：若完整 WORLD 过门而压缩版本失败，下一轮先重构表示；若全部版本均失败，则停止把当前 PyWorld 合成器作为学习式保底声码器。该 oracle 不是他人到目标转换成果，不请求试听。
- 限制：Track 9 已暴露，仅作组件诊断；板卡保持关机，不录音、不播放、不访问板卡，无实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 生成四个确定性重建、运行同一严格评估并提交。

### [PS-20261021-10] WORLD 表示压缩上限 Round 24 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：ACCEPTED_COMPONENT_ORACLE（仅表示上限，不是转换接受）
- 基准提交：`caf401c`
- 修改路径：`build/run_world_representation_oracle_round24_20261025.py`、`report/world_representation_oracle_round24_20261025.{md,json}`、`coummucation.md`。
- 量化结果：完整 WORLD 为 **0.8408/0.8232/0.1349/2.4801/0.0000**；SP60/AP12 为 **0.8380/0.8204/0.1266/2.4581/0.0000**（身份/P10/固定男性质心余弦/UTMOS/CER）。更高 SP120/AP24 与 SP180/AP48 无实质收益。
- 判定：保留 SP60/AP12；表示压缩不是 Round 20～23 主瓶颈，问题在 HuBERT→WORLD 参数预测。目标自重建的男性质心余弦门不适用：完整目标参数自身也为 `0.1349`，不能称源泄漏；`≤0.10` 只用于真正男性转换。
- 限制：组件 oracle，不是男性到目标转换；Track 9 已暴露，不请求试听。板卡保持关机，未录音、未播放、未访问板卡。
- 报告链接：`report/world_representation_oracle_round24_20261025.md`、`report/world_representation_oracle_round24_20261025.json`。
- 下一责任方：Hardware-A / Codex 以 SP60/AP12 固定表示重新设计有足够监督的数据路线；不得继续靠扩大特征维数优化。

### [PS-20261021-10] 扩展教师配对 HuBERT→WORLD Round 25 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`7754463`
- 依据：Round 24 证明 SP60/AP12 自重建身份 `0.8380`、UTMOS `2.4581`、CER `0`，表示上限充足；Round 20～23 的主瓶颈是仅用 99 秒目标自重建学习跨说话人映射。
- 数据：复用现有 `full_train_corpus_16k` 的 192 训练 + 8 独立验证 CosyVoice3 源/目标教师配对（约 15.6 分钟），以及 Tracks 5～8 四个目标自重建锚点；资产已本机逐项解析，源/教师各 200 个 `.f32`，无缺失。Track 9 和固定男性验证录音不参与训练或选择。
- 方案：冻结 HuBERT 内容输入，预测已通过 oracle 的 SP60/AP12 WORLD 表示；配对教师提供跨说话人内容→目标声学监督，目标锚点约束目标本人重建。先完成特征缓存、教师 WORLD oracle 抽检和确定性训练干跑，再决定长训练。
- 风险：CosyVoice3 教师波形未获真人听感接受，只能作监督，不作为验收真值；最终必须在固定男性未训练输出上通过五门和真人试听。
- 限制：板卡保持关机；本轮无需录音、播放或访问板卡，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 完成缓存与数据泄漏审计，运行教师/验证预检并按结果决定是否启动长训练。

### [PS-20261021-10] 扩展教师配对 HuBERT→WORLD Round 25 预检结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：READY_LONG_TRAIN
- 基准提交：`e5ae8ee`
- 修改路径：`build/prepare_hubert_world_pairs_round25_20261025.py`、`report/paired_hubert_world_preflight_round25_20261025.{md,json}`、`coummucation.md`。
- 资产结果：200/200 对缓存成功；训练 192 对/20 人/`888.1089 s`，验证 8 对/2 人/`46.1948 s`，说话人交集为空。缓存 200 文件、79,280,418 字节，清单 SHA-256 `57dc9d95bb4b485ca5325b4e318766ef852bdfd29d49e5c197c804de8980d053`。
- 数据纪律：Track 9 和固定男性录音未用于缓存、训练或选择；每个源/教师 `.f32` 均按既有 manifest 核对 SHA。抽检首/中/末缓存均为 `(T,768)` 内容与 `(T,75)` WORLD 目标且全部有限。
- 判定：资产与切分满足启动独立长训练轮次；本轮未启动长训练。CosyVoice3 教师未获真人接受，最终仍须固定男性五门和真人试听。
- 限制：板卡保持关机；未录音、未播放、未访问板卡，无实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/paired_hubert_world_preflight_round25_20261025.md`、`report/paired_hubert_world_preflight_round25_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交预检；随后另行认领长训练 Round 26。

### [PS-20261021-10] 扩展配对因果 GRU 长训练 Round 26 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`2606e1c`
- 方案：复用 Round 25 完整缓存，PCA/归一化只拟合 192 训练对；两层单向 GRU 在 HuBERT 20 ms 帧率预测 SP60/AP12 WORLD 参数，训练批次混入 Tracks 5～8 目标自重建锚点，VUV 独立分类并保留一阶动态损失。
- 验证与冻结：仅用 2 名未训练验证说话人的 8 对教师句早停；Track 9 不参与训练、归一化或模型选择，只在冻结后作已暴露目标重建回归。目标重建核心门失败则不运行固定男性 4/5。
- 资源边界：本轮训练教师上限，不宣称 GRU 可上板；过门后才蒸馏并评估 PL。缓存、checkpoint 和 WAV 留在忽略目录。
- 限制：板卡保持关机；不录音、不播放、不访问板卡，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 完成长训练、因果性验证和冻结 Track 9 回归。

### [PS-20261021-10] 扩展配对因果 GRU 长训练 Round 26 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED / ROUTE_EFFECTIVE
- 基准提交：`99ea180`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_gru_round26_20261025.{md,json}`、`coummucation.md`。
- 训练结果：477,771 参数两层单向 GRU；192 训练对、8 独立验证对、25% 目标锚点；8 个短训练句从裁剪池排除。第 500 步验证最佳 `0.369932`，第 1300 步早停并恢复；因果前缀差异 `0.0`。
- 量化结果：已暴露 Track 9 为 **0.6234/0.6098/0.1591/1.4628/0.1522**（身份/P10/固定男性质心余弦/UTMOS/CER）。目标自重建不应用男性泄漏门；身份两门通过，CER仅超门 `0.0022`，UTMOS仍失败。
- 对比：相对 Round 23，身份 `0.5622→0.6234`、UTMOS `1.3388→1.4628`、CER `0.3804→0.1522`，证明扩展配对监督有效，但自然度仍不足。
- 判定：不运行固定男性 4/5、不请求试听、不进入蒸馏/PL。下一轮应针对过平滑动态和教师自然度，而不是扩大模型或表示维数。
- 限制：板卡保持关机；未录音、未播放、未访问板卡，无实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 报告链接：`report/paired_hubert_world_gru_round26_20261025.md`、`report/paired_hubert_world_gru_round26_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交本轮；审计教师 WORLD 重建与预测动态差异后再定下一轮唯一变量。

### [PS-20261021-10] 配对教师与预测动态归因 Round 27 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`5aa14e7`
- 目标：在 Round 26 的 8 个独立验证句上，对同一 SP60/AP12 表示分别合成真实教师参数与冻结模型预测参数，比较 UTMOS、谱/F0/能量/AP 的帧方差和一阶动态，定位 `UTMOS=1.4628` 的主因。
- 数据边界：只读 Round 25 验证缓存和 Round 26 冻结 checkpoint；不训练、不调参、不读取 Track 9 选择结果，不使用固定男性录音。
- 决策：若教师重建 UTMOS 已低，则下一轮先处理教师质量；若教师明显合格而预测明显低且动态比收缩，则下一轮只修改动态/多分辨率损失。不得同时换教师和损失。
- 限制：板卡保持关机；不录音、不播放、不访问板卡，无实时、Cortex-A9、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 完成 8 句成对诊断并提交唯一根因结论。

### [PS-20261021-10] 配对教师与预测动态归因 Round 27 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：ROOT_CAUSE_CONFIRMED
- 基准提交：`68bcaaf`
- 修改路径：`build/audit_paired_world_dynamics_round27_20261025.py`、`report/paired_world_dynamics_audit_round27_20261025.{md,json}`、`coummucation.md`。
- UTMOS：8 个独立验证句教师 WORLD 重建均值 `2.5855`，Round 26 预测重建均值 `1.7218`，平均下降 `0.8637`；教师 7/8 句高于 2.30，预测 0/8 高于 2.30。
- 动态比：预测/教师的谱一阶动态 `0.6107`、log-F0 `0.4795`、能量 `0.7815`、AP `0.6138`；能量静态方差仍有 `0.9617`。根因为谱/F0/AP 预测动态过平滑。
- 判定：教师整体质量不是主因，SP60/AP12 已由 Round 24 排除；下一轮唯一变量为更强的多尺度动态损失，保持架构、数据、锚点比例、表示和验证切分不变。
- 限制：未训练、未使用 Track 9 或固定男性录音；诊断 WAV 未播放。板卡保持关机，无硬件结论。
- 报告链接：`report/paired_world_dynamics_audit_round27_20261025.md`、`report/paired_world_dynamics_audit_round27_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交归因；随后另行认领单变量多尺度动态训练。

### [PS-20261021-10] 多尺度动态损失 Round 28 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`a32a72c`
- 唯一变量：把 Round 26 的 `0.20 × lag-1` 一阶动态损失替换为 `0.75 × mean(lag-1, lag-2, lag-4)` 多尺度动态损失。
- 冻结项：Round 25 配对缓存与验证切分、477771 参数双层单向 GRU、SP60/AP12、25% 目标锚点、batch/crop/学习率/早停规则和客观评估器全部不变，不做权重或 lag 扫描。
- 判定：仍只按独立验证集选 checkpoint，完成后仅运行一次 Track 9；身份门 `≥0.45`、P10 `≥0.35`、UTMOS `≥2.30`、CER `≤0.15`。目标自重建不适用男性泄漏门。
- 限制：不播放、不使用固定男性输入、不触碰板卡；板卡继续关机，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 实现并运行本轮单变量训练，失败也提交完整证据。

### [PS-20261021-10] 多尺度动态损失 Round 28 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_IMPROVED
- 基准提交：`e5770df`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_multiscale_round28_20261025.{md,json}`、`coummucation.md`。
- 训练结果：固定 `0.75 × mean(lag 1/2/4)`；477,771 参数，192/8 配对，25% 锚点；第 600 步验证最佳 `0.594944`，第 1400 步早停，因果差异 `0.0`。
- Track 9：**0.6555/0.6440/0.1661/1.5966/0.1087**（身份/P10/男性质心余弦/UTMOS/CER）。目标自重建不应用男性泄漏门；身份、P10、CER 通过，UTMOS 失败。
- 对比 Round 26：身份 `+0.0321`、P10 `+0.0342`、UTMOS `+0.1338`、CER `-0.0435`；方向有效但距离自然度门仍有 `0.7034`。
- 执行说明：第一次完整训练后只在末端清单相对路径处理失败；修复后同 seed 完整重跑，日志与哈希一致。checkpoint SHA `907015ba…7d4bfc`，WAV SHA `b57db782…6f6e1`。
- 限制：未播放、未使用固定男性输入；板卡保持关机，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 报告链接：`report/paired_hubert_world_multiscale_round28_20261025.md`、`report/paired_hubert_world_multiscale_round28_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交本轮；下一轮先量化 Round 28 动态恢复，不直接扩大损失权重。

### [PS-20261021-10] Round 28 动态恢复归因 Round 29 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`b072322`
- 范围：沿用 Round 27 的 8 条说话人独立验证句、教师参数、合成器与评估器，只把冻结 checkpoint 换成 Round 28，并与 Round 26 的动态比直接比较。
- 输出：谱、log-F0、能量、AP 的帧标准差与 lag-1 动态 RMS 恢复率，以及教师/预测 UTMOS；据此冻结下一轮唯一变量。
- 限制：不训练、不重新使用 Track 9、不使用固定男性输入、不播放；板卡保持关机。
- 下一责任方：Hardware-A / Codex 完成诊断并提交结论。

### [PS-20261021-10] Round 28 动态恢复归因 Round 29 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：ROOT_CAUSE_REFINED
- 基准提交：`3af19c0`
- 修改路径：`build/audit_paired_world_dynamics_round27_20261025.py`、`report/paired_world_dynamics_recovery_round29_20261025.{md,json}`、`coummucation.md`。
- UTMOS：8 条独立验证句教师均值 `2.5855`；Round 28 预测均值 `1.8335`，比 Round 26 的 `1.7218` 提高 `0.1117`。
- 动态变化：谱 lag-1 比 `0.6107→0.6356`、能量 `0.7815→0.7994`、AP `0.6138→0.6609`；log-F0 却从 `0.4795→0.4669`。
- 根因细化：动态损失对连续维总平均，60 维谱主导，单维 log-F0/能量权重被稀释；下一唯一变量为四参数组等权的多尺度动态项，总权重和 lag 不变。
- 限制：未训练、未重新使用 Track 9、未用固定男性输入、未播放；板卡保持关机。
- 报告链接：`report/paired_world_dynamics_recovery_round29_20261025.md`、`report/paired_world_dynamics_recovery_round29_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交归因后另行认领组平衡训练。

### [PS-20261021-10] 参数组平衡动态损失 Round 30 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`7fd8a0d`
- 唯一变量：将 Round 28 的逐连续维总平均改为谱、log-F0、能量、AP 四组先各自平均、再四组等权平均。
- 冻结项：动态总权重 `0.75`、lag `1/2/4`、重建/VUV 项、Round 25 数据与切分、477771 参数 GRU、25% 锚点、优化器、早停和评估器均不变。
- 判定：仍只按 8 条独立验证句选 checkpoint，完成后 Track 9 仅运行一次；目标自重建按身份/P10/UTMOS/CER 门判断，不应用男性泄漏门。
- 限制：不播放、不使用固定男性输入、不触碰板卡；板卡继续关机。
- 下一责任方：Hardware-A / Codex 实现并运行本轮单变量训练。

### [PS-20261021-10] 参数组平衡动态损失 Round 30 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_REGRESSION
- 基准提交：`c599085`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_group_balanced_round30_20261025.{md,json}`、`coummucation.md`。
- 训练结果：四组等权、其余冻结；第 600 步验证最佳 `0.445997`，第 1400 步早停，因果差异 `0.0`。
- Track 9：**0.6427/0.6067/0.1722/1.4738/0.1304**（身份/P10/男性质心余弦/UTMOS/CER）。目标自重建不应用泄漏门；UTMOS 失败。
- 对比 Round 28：身份 `-0.0128`、P10 `-0.0373`、UTMOS `-0.1228`、CER `+0.0217`；四组完全等权回退，拒绝。
- 哈希：checkpoint `fb04feca…8b231`，WAV `c8a23c1d…ef280`。
- 限制：未播放、未使用固定男性输入；板卡保持关机，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 报告链接：`report/paired_hubert_world_group_balanced_round30_20261025.md`、`report/paired_hubert_world_group_balanced_round30_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交失败轮次；后续恢复 Round 28 基线，只隔离 F0 轨迹项。

### [PS-20261021-10] 组平衡回退归因 Round 31 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`91e6109`
- 范围：沿用 Round 27/29 的 8 条独立验证句和教师对照，仅替换为 Round 30 checkpoint，量化四组动态和 UTMOS 相对 Round 28 的变化。
- 决策：若 F0 动态恢复但整体质量下降，则停止四组等权并评估较弱 F0 专项项；若 F0 也未恢复，则停止当前动态回归加权路线。
- 限制：不训练、不重新使用 Track 9、不使用固定男性输入、不播放；板卡保持关机。
- 下一责任方：Hardware-A / Codex 完成诊断并提交路线结论。

### [PS-20261021-10] 组平衡回退归因 Round 31 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：ROUTE_STOPPED
- 基准提交：`c561201`
- 修改路径：`report/group_balance_failure_audit_round31_20261025.{md,json}`、`coummucation.md`。
- UTMOS：8 条验证句 Round 30 预测均值 `1.6838`，低于 Round 28 的 `1.8335`，下降 `0.1497`。
- 动态比：Round 30 的谱/log-F0/能量/AP lag-1 比为 `0.6233/0.4598/0.8501/0.6722`；F0 低于 Round 28 的 `0.4669`，未因四组等权恢复。
- 判定：停止动态回归权重变体；下一假设为 HuBERT-only 输入缺少因果韵律，先预检显式源 F0/能量输入与 Cortex-A9/PL 预算。
- 限制：未训练、未重新使用 Track 9、未用固定男性输入、未播放；板卡保持关机。
- 报告链接：`report/group_balance_failure_audit_round31_20261025.md`、`report/group_balance_failure_audit_round31_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交诊断；下一轮另行认领源韵律输入预检。

### [PS-20261021-10] 显式源韵律输入预检 Round 32 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线预检）
- 状态：CLAIMED
- 基准提交：`5a40f19`
- 范围：对 Round 25 的 200 对源音频逐件复核 SHA，提取并按 HuBERT 帧对齐源 log-F0、VUV、log-energy，量化其与教师目标韵律的相关性和覆盖率。
- 预算：计算把 GRU 输入从 96 维扩为 99 维的新增参数/MAC；源韵律提取只允许复用现有 WORLD/板端分析链，不把离线 PyWORLD 耗时宣称为板端实时结果。
- 成功标准：200/200 资产可追溯且有限；至少 F0 或能量提供非退化、正相关信息；增量参数和逐帧 MAC <1%，才允许下一轮训练。
- 限制：不训练、不使用 Track 9 或固定男性录音、不播放、不访问板卡；板卡保持关机。
- 下一责任方：Hardware-A / Codex 完成预检并提交是否进入源韵律条件训练的结论。

### [PS-20261021-10] 显式源韵律输入预检 Round 32 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线预检）
- 状态：READY_PROSODY_TRAIN
- 基准提交：`af3253c`
- 修改路径：`build/audit_source_prosody_round32_20261025.py`、`report/source_prosody_preflight_round32_20261025.{md,json}`、`coummucation.md`。
- 数据：200/200 源音频通过 declaration/cache 双重 SHA 校验，特征全部有限；未使用 Track 9 或固定男性录音。
- 相关性：句内 F0 轮廓 `0.5582`、F0 一阶动态 `0.1558`、能量 `0.9409`、VUV 准确率/F1 `0.8685/0.9210`；源韵律具备非退化增量信息。
- 预算：输入 `96→99`，参数 `477771→478347`，新增 576（`0.1206%`）；每帧新增 576 MAC（`0.1212%`，50 Hz 为 28800 MAC/s）。
- 判定：允许下一轮仅增加源 log-F0/VUV/log-energy 输入的训练；保持 Round 28 损失、数据、模型宽深、锚点比例与验证切分不变。
- 限制：离线提取器非因果，未做板端/PL 实测；不播放，板卡保持关机。
- 报告链接：`report/source_prosody_preflight_round32_20261025.md`、`report/source_prosody_preflight_round32_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交预检后另行认领源韵律条件训练。

### [PS-20261021-10] 显式源韵律条件训练 Round 33 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`a7aab4e`
- 唯一变量：在 Round 28 的 96 维 HuBERT-PCA 输入后追加训练集归一化的源 log-F0、VUV、log-energy 三维特征，输入变为 99 维。
- 冻结项：Round 25 配对数据与说话人切分、Round 28 的 `0.75 × mean(lag 1/2/4)` 损失、双层 192 GRU、25% 锚点、batch/crop/学习率/早停及评估器均不变。
- 防泄漏：源韵律归一化只拟合 192 训练对；验证不参与统计或选参；Track 9 只在冻结 checkpoint 后运行一次；固定男性录音本轮不使用。
- 判定：目标自重建身份 `≥0.45`、P10 `≥0.35`、UTMOS `≥2.30`、CER `≤0.15`；男性泄漏门不适用于目标自重建。
- 限制：离线特征仍非因果，不播放、不触碰板卡；通过客观门后才进入因果特征一致性和固定男性验证。
- 下一责任方：Hardware-A / Codex 实现并运行单变量训练，失败也提交。

### [PS-20261021-10] 显式源韵律条件训练 Round 33 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_IMPROVED
- 基准提交：`0922c22`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_source_prosody_round33_20261025.{md,json}`、`coummucation.md`。
- 训练：输入 99 维、478347 参数；第 800 步验证最佳 `0.594895`，第 1600 步早停，因果前缀差异 `0.0`。
- Track 9：**0.6757/0.6549/0.1754/1.7038/0.1304**（身份/P10/男性质心余弦/UTMOS/CER）。目标自重建不应用泄漏门；UTMOS 失败。
- 对比 Round 28：身份 `+0.0202`、P10 `+0.0109`、UTMOS `+0.1072`、CER `+0.0217` 且仍过门；源韵律方向有效，但距离 UTMOS 门仍有 `0.5962`。
- 哈希：checkpoint `7e3c75be…9989696`，WAV `7d8c91f1…7d5ef9`；生成物未提交。
- 限制：源韵律为离线非因果特征，未播放、未使用固定男性输入；板卡保持关机。
- 报告链接：`report/paired_hubert_world_source_prosody_round33_20261025.md`、`report/paired_hubert_world_source_prosody_round33_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交本轮；下一轮先审计独立验证集的 F0/能量/VUV 恢复，不直接增加更多输入或模型容量。

### [PS-20261021-10] 源韵律增益归因 Round 34 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`9ae9408`
- 范围：在 Round 27/29 相同的 8 条独立验证句上加载 Round 33 checkpoint，使用相同教师、合成器和评估器，量化四组动态与 UTMOS，并与 Round 28 直接比较。
- 决策：确认改进来自 F0、能量、VUV 或其他组；只据独立验证证据冻结下一单变量，不增加模型容量或再次调动态损失。
- 限制：不训练、不重新使用 Track 9、不使用固定男性输入、不播放；板卡保持关机。
- 下一责任方：Hardware-A / Codex 完成审计并提交下一路线结论。

### [PS-20261021-10] 源韵律增益归因 Round 34 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：GAIN_CONFIRMED
- 基准提交：`1b88116`
- 修改路径：`build/audit_paired_world_dynamics_round27_20261025.py`、`report/source_prosody_gain_audit_round34_20261025.{md,json}`、`coummucation.md`。
- UTMOS：8 条独立验证句预测均值 `1.9006`，高于 Round 28 的 `1.8335`，增加 `0.0671`；教师均值 `2.5855`。
- 动态比：Round 33 的谱/log-F0/能量/AP lag-1 比为 `0.6462/0.5177/0.8200/0.6750`，四组均高于 Round 28 的 `0.6356/0.4669/0.7994/0.6609`。
- 判定：源韵律增益在独立验证集成立；下一步先测 ±4 HuBERT 帧内的预测/教师固定时延，不增加容量或再调损失。
- 限制：未训练、未重新使用 Track 9、未用固定男性输入、未播放；离线源特征非因果，板卡保持关机。
- 报告链接：`report/source_prosody_gain_audit_round34_20261025.md`、`report/source_prosody_gain_audit_round34_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交本轮；下一轮另行认领有限前视必要性诊断。

### [PS-20261021-10] 有限前视必要性诊断 Round 35 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`699c5eb`
- 范围：冻结 Round 33 checkpoint，在相同 8 条独立验证句上把预测与教师目标按 `-4…+4` 个 HuBERT 帧错位比较，统计总体及谱/log-F0/能量/AP 的归一化 Smooth-L1 和逐句最佳 lag。
- 决策门：非零 lag 必须相对 lag 0 聚合改善至少 `1%`，且至少 5/8 验证句最佳 lag 方向一致，才允许下一轮有限前视训练；否则拒绝增加延迟。
- 限制：不训练、不合成、不重新使用 Track 9、不使用固定男性输入、不播放；板卡保持关机。
- 下一责任方：Hardware-A / Codex 完成 lag 审计并提交 GO/NO-GO。

### [PS-20261021-10] 有限前视必要性诊断 Round 35 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：NO_GO_LOOKAHEAD
- 基准提交：`b96a399`
- 修改路径：`build/audit_prediction_lag_round35_20261025.py`、`report/prediction_lag_audit_round35_20261025.{md,json}`、`coummucation.md`。
- 结果：8/8 独立验证句总体最佳 lag 均为 0；聚合 lag 0 损失 `0.27452`，lag -1/+1 已升至 `0.30059/0.30243`，±2～4 更差。
- 判定：非零 lag 改善 `0%`，未满足 ≥1% 且 ≥5/8 同向门；拒绝有限前视和额外 20～80 ms 延迟，保持严格零前视。
- 限制：未训练、未合成、未重新使用 Track 9、未用固定男性输入、未播放；板卡保持关机。
- 报告链接：`report/prediction_lag_audit_round35_20261025.md`、`report/prediction_lag_audit_round35_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交 NO-GO；后续仅考虑零前视下的动态分布约束，不再做时序平移。

### [PS-20261021-10] 动态欠方差一致性预检 Round 36 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线预检）
- 状态：CLAIMED
- 基准提交：`8bb733c`
- 范围：只读取 Round 34 的 8 条独立验证原始审计，统计谱/log-F0/能量/AP 的逐句 lag-1 动态比、低于教师的句数和变异系数。
- 决策门：四组都必须 8/8 句动态比 <1，且跨句变异系数 <0.25，才允许下一轮直接方差匹配；否则停止该路线。
- 限制：不训练、不推理、不合成、不使用 Track 9 或固定男性输入、不播放；板卡保持关机。
- 下一责任方：Hardware-A / Codex 完成一致性判定并提交 GO/NO-GO。

### [PS-20261021-10] 动态欠方差一致性预检 Round 36 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线预检）
- 状态：GO_VARIANCE_MATCHING
- 基准提交：`97fbd87`
- 修改路径：`report/dynamic_variance_consistency_round36_20261025.{md,json}`、`coummucation.md`。
- 结果：谱/log-F0/能量/AP 的 8/8 句 lag-1 动态比全部 <1；均值 `0.6462/0.5177/0.8200/0.6750`，变异系数 `0.0377/0.1643/0.0669/0.1170`，均通过 <0.25 门。
- 判定：允许下一轮仅增加固定 `0.05` 权重的四组 lag-1 log-RMS 匹配训练项；推理网络、参数、MAC 与延迟不变。
- 限制：未训练、推理、合成或重新使用 Track 9；未用固定男性输入、未播放，板卡保持关机。
- 报告链接：`report/dynamic_variance_consistency_round36_20261025.md`、`report/dynamic_variance_consistency_round36_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交预检后另行认领方差匹配训练。

### [PS-20261021-10] 动态方差匹配训练 Round 37 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`02c8c55`
- 唯一变量：在 Round 33 总损失上增加 `0.05 × mean_group((log RMS(Δpred)-log RMS(Δtarget))²)`，四组为谱/log-F0/能量/AP，Δ 仅用 lag 1。
- 冻结项：99 维源韵律输入、478347 参数双层 192 GRU、Round 25 数据与切分、25% 锚点、Round 28 多尺度项、优化器、早停和评估器均不变。
- 判定：仍只按 8 条独立验证句选 checkpoint，冻结后 Track 9 运行一次；目标自重建身份/P10/UTMOS/CER 门不变。
- 限制：离线源韵律非因果；不播放、不使用固定男性输入、不触碰板卡。方差项只用于训练，推理成本不变。
- 下一责任方：Hardware-A / Codex 实现并运行单变量训练，失败也提交。

### [PS-20261021-10] 动态方差匹配训练 Round 37 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_BEST_SO_FAR
- 基准提交：`0c0272a`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_variance_matching_round37_20261025.{md,json}`、`coummucation.md`。
- 训练：478347 参数不变；第 1200 步验证最佳 `0.617570`，第 2000 步停止并恢复，因果前缀差异 `0.0`。
- Track 9：**0.6954/0.6794/0.1350/1.8616/0.1087**（身份/P10/男性质心余弦/UTMOS/CER）。目标自重建不应用泄漏门；UTMOS 失败。
- 对比 Round 33：身份 `+0.0197`、P10 `+0.0245`、UTMOS `+0.1578`、CER `-0.0217`、男性质心余弦 `-0.0404`；当前配对 WORLD 路线最佳。
- 哈希：checkpoint `efcda700…3bd2a2`，WAV `cebbc5f5…355eef`；推理参数/MAC/延迟不变。
- 限制：离线源韵律非因果；未播放、未使用固定男性输入，板卡保持关机。
- 报告链接：`report/paired_hubert_world_variance_matching_round37_20261025.md`、`report/paired_hubert_world_variance_matching_round37_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交本轮；下一轮先审计独立验证动态与自然度，不直接改变方差权重。

### [PS-20261021-10] 方差匹配独立验证 Round 38 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`36372e1`
- 范围：在 Round 27/29/34 相同的 8 条独立验证句上加载 Round 37 checkpoint，以相同教师、合成器和评估器计算 UTMOS 与四组动态，并与 Round 33 直接比较。
- 决策门：UTMOS 均值必须高于 Round 33，至少 6/8 句 UTMOS 不退步，且谱/log-F0/能量/AP 聚合动态比均 ≤1.20，才保留方差匹配方向。
- 限制：不训练、不重新使用 Track 9、不使用固定男性输入、不播放；板卡保持关机。
- 下一责任方：Hardware-A / Codex 完成独立验证并提交 KEEP/REVERT。

### [PS-20261021-10] 方差匹配独立验证 Round 38 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：KEEP_VARIANCE_MATCHING
- 基准提交：`61414b9`
- 修改路径：`report/variance_matching_validation_round38_20261025.{md,json}`、`coummucation.md`。
- UTMOS：8 条验证句均值 `2.0055`，高于 Round 33 的 `1.9006`；7/8 句提高，余下一句仅约 `-0.00001`。
- 动态比：谱/log-F0/能量/AP 为 `0.7776/1.1186/0.9162/0.7582`，全部 ≤1.20；F0 已略高于教师，谱/AP 仍不足。
- 判定：保留方差匹配，但禁止整体提高 0.05 权重；后续若训练，必须分离 F0 与其余组，避免 F0 过增强。
- 限制：未训练、未重新使用 Track 9、未用固定男性输入、未播放；板卡保持关机。
- 报告链接：`report/variance_matching_validation_round38_20261025.md`、`report/variance_matching_validation_round38_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交验证；下一轮另行认领分组方差目标。

### [PS-20261021-10] 非 F0 方差匹配训练 Round 39 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`4778f7b`
- 唯一变量：方差匹配总权重保持 `0.05`，从四组等权改为只对谱/能量/AP 三组等权；F0 仍受重建和 lag 1/2/4 多尺度损失约束。
- 冻结项：99 维输入、478347 参数网络、数据切分、25% 锚点、其余损失、优化器、早停和评估器均不变；推理成本不变。
- 依据：Round 38 的 F0 动态比已为 `1.1186`，而谱/能量/AP 仅 `0.7776/0.9162/0.7582`；禁止整体加权。
- 判定：只按 8 条独立验证句选 checkpoint，冻结后 Track 9 运行一次；目标自重建四门不变。
- 限制：离线源韵律非因果；不播放、不使用固定男性输入、不触碰板卡。
- 下一责任方：Hardware-A / Codex 实现并运行单变量训练，失败也提交。

### [PS-20261021-10] 非 F0 方差匹配训练 Round 39 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_REGRESSION
- 基准提交：`c070216`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_non_f0_variance_round39_20261025.{md,json}`、`coummucation.md`。
- 训练：478347 参数不变；第 1100 步验证最佳 `0.620411`，第 1900 步早停，因果前缀差异 `0.0`。
- Track 9：**0.6863/0.6581/0.1759/1.5796/0.1304**（身份/P10/男性质心余弦/UTMOS/CER），UTMOS 失败。
- 对比 Round 37：身份 `-0.0091`、P10 `-0.0213`、UTMOS `-0.2820`、CER `+0.0217`、男性质心余弦 `+0.0409`；明显回退。
- 判定：F0 方差项不可删除；拒绝 Round39，保留 Round37 当前最佳。checkpoint `e89a27ee…ffedc4`，WAV `d89ce2e9…ae18d6`。
- 限制：未播放、未使用固定男性输入；离线源韵律非因果，板卡保持关机。
- 报告链接：`report/paired_hubert_world_non_f0_variance_round39_20261025.md`、`report/paired_hubert_world_non_f0_variance_round39_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交失败轮次；不得继续删除 F0 或整体增大方差权重。

### [PS-20261021-10] 半权 F0 方差匹配训练 Round 40 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`10407eb`
- 唯一变量：方差项保持总权重 `0.05`，谱/log-F0/能量/AP 子项权重固定为 `1/0.5/1/1`，按权重和 `3.5` 归一化；不做其他权重扫描。
- 冻结项：Round 37 的 99 维输入、478347 参数网络、数据切分、25% 锚点、其余损失、优化器、早停和评估器全部不变；推理成本不变。
- 依据：Round37 全 F0 权重为当前最佳，但验证 F0 动态比 `1.1186`；Round39 零 F0 权重严重回退，因此只测试预先固定的中点。
- 判定：仅按 8 条独立验证句选 checkpoint，冻结后 Track 9 运行一次；若不超过 Round37，则停止 F0 方差权重插值。
- 限制：离线源韵律非因果；不播放、不使用固定男性输入、不触碰板卡。
- 下一责任方：Hardware-A / Codex 实现并运行本轮，失败也提交。

### [PS-20261021-10] 半权 F0 方差匹配训练 Round 40 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_MIXED_NO_MATERIAL_GAIN
- 基准提交：`819e231`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_half_f0_variance_round40_20261025.{md,json}`、`coummucation.md`。
- 训练：478347 参数不变；第 1200 步验证最佳 `0.619410`，第 2000 步早停并恢复，因果前缀差异 `0.0`。
- Track 9：**0.6969/0.6686/0.1350/1.8639/0.0978**（身份/P10/男性质心余弦/UTMOS/CER）。目标自重建不应用泄漏门；UTMOS 失败。
- 对比 Round37：身份 `+0.0015`、UTMOS `+0.0023`、CER `-0.0109`，但 P10 `-0.0108`，验证总目标退步 `+0.001840`；无材料级净收益。
- 判定：拒绝 Round40，停止 F0 方差权重插值并保留 Round37 当前最佳。checkpoint `d9220b7b…c3b734`，WAV `dd66251d…ce811`。
- 限制：未播放、未使用固定男性输入；离线源韵律非因果，板卡保持关机。
- 报告链接：`report/paired_hubert_world_half_f0_variance_round40_20261025.md`、`report/paired_hubert_world_half_f0_variance_round40_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交失败轮次；下一轮不得继续扫描 F0 方差权重，应改查 UTMOS 短板的其他可解释因素。

### [PS-20261021-10] Round37 参数组 oracle 自然度归因 Round 41 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`a717375`
- 范围：固定 Round37 checkpoint、Track 9、裁剪边界、WORLD 合成器与严格评估器；分别仅用 Track 9 真值替换预测的谱 DCT、log-F0+VUV、能量或 AP DCT，并增加全真值 WORLD 重合成上限。
- 决策门：以同一 Round37 基线比较 UTMOS 增量；只有单组 oracle 能带来至少 `+0.10` UTMOS，才允许下一训练轮优先攻该组。oracle 仅用于归因，不是可部署候选，也不参与音色方案验收。
- 数据纪律：Track 9 已是冻结后开发回归，只用于诊断；不选 checkpoint、不训练、不使用固定男性输入、不播放。
- 限制：所有 oracle 都依赖未来真值，明确不可部署；不触碰板卡，板卡保持关机。
- 下一责任方：Hardware-A / Codex 实现一次性诊断并提交全部输出指标，失败也提交。

### [PS-20261021-10] Round37 参数组 oracle 自然度归因 Round 41 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：GO_SPLIT_F0_VUV
- 基准提交：`fa6cb57`
- 修改路径：`build/audit_round37_oracle_groups_round41_20261025.py`、`report/round37_oracle_attribution_round41_20261025.{md,json}`、`coummucation.md`。
- 可复现性：Round37 基线 WAV 逐位一致，SHA-256 `cebbc5f5…355eef`；checkpoint `efcda700…3bd2a2`。
- UTMOS：基线 `1.8616`；真值谱 `1.9156`（`+0.0540`）；真值 log-F0+VUV `1.9975`（`+0.1359`）；真值能量 `1.5683`（`-0.2933`）；真值 AP `1.8123`（`-0.0493`）；全真值 `2.5429`（`+0.6813`）。
- 判定：F0+VUV 是唯一超过预设 `+0.10` 的单组，但下一轮必须先拆分两者再选训练目标；谱暂列第二，能量/AP 不单独强化。全真值超过 UTMOS 门，证明 WORLD 合成上限足够。
- 限制：oracle 使用 Track 9 未来真值、不可部署；目标自重建不应用男性泄漏门。未训练、未播放、未用固定男性输入，板卡保持关机。
- 报告链接：`report/round37_oracle_attribution_round41_20261025.md`、`report/round37_oracle_attribution_round41_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交诊断；另行认领 log-F0 与 VUV 拆分 oracle。

### [PS-20261021-10] log-F0 与 VUV 拆分 oracle Round 42 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`b7a59ec`
- 唯一变量：在 Round41 同一逐位复现基线上，把联合 `log-F0+VUV` oracle 拆成仅真值 log-F0 和仅真值 VUV；其余预测参数、Track 9、合成器及严格评估器全部不变。
- 决策门：相对 Round37 UTMOS 增量较大的单项作为下一训练主目标；若两项各自均小于 `+0.10`、但联合仍为 `+0.1359`，则按交互问题处理，不盲目提高单项损失。
- 限制：oracle 依赖未来真值、不可部署；不训练、不播放、不使用固定男性输入、不触碰板卡，板卡保持关机。
- 下一责任方：Hardware-A / Codex 运行拆分诊断并提交指标。

### [PS-20261021-10] log-F0 与 VUV 拆分 oracle Round 42 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：GO_LOG_F0_TRAINING
- 基准提交：`10fac9f`
- 修改路径：`build/audit_round37_oracle_groups_round41_20261025.py`、`report/round37_f0_vuv_split_round42_20261025.{md,json}`、`coummucation.md`。
- 量化结果：Round37 基线 UTMOS `1.8616`；仅真值 log-F0 `2.0086`（`+0.1470`）；仅真值 VUV `1.8635`（`+0.0019`）；联合 `1.9975`（`+0.1359`）。仅 F0 同时为身份/P10/CER `0.7440/0.7157/0.0870`。
- 判定：自然度收益来自连续 log-F0，不来自 VUV；下一训练轮只增强 log-F0 回归，不提高 VUV 分类权重。
- 限制：oracle 使用 Track 9 未来真值、不可部署；目标自重建不应用男性泄漏门。未训练、未播放、未用固定男性输入，板卡保持关机。
- 报告链接：`report/round37_f0_vuv_split_round42_20261025.md`、`report/round37_f0_vuv_split_round42_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交诊断；另行认领单变量 log-F0 训练项。

### [PS-20261021-10] 有声 log-F0 辅助回归 Round 43 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`186566c`
- 唯一变量：在 Round37 总损失上增加 `0.05 × Smooth-L1(pred_logF0, target_logF0)`，只统计目标 VUV 为有声的帧；原四组方差项保持 `0.05` 等权。
- 冻结项：99 维源韵律输入、478347 参数网络、数据切分、25% 锚点、重建/VUV/多尺度/方差损失、优化器、早停、合成器和评估器全部不变；推理参数、MAC 和延迟不变。
- 依据：Round42 仅真值 log-F0 使 UTMOS `+0.1470`，仅真值 VUV 只有 `+0.0019`；使用最小同级权重，避免一次性过度强化。
- 判定：仅按 8 条独立验证句选 checkpoint，冻结后 Track 9 运行一次；目标自重建身份/P10/UTMOS/CER 门不变。若回退即拒绝，不扫描权重。
- 限制：离线源韵律非因果；不播放、不使用固定男性输入、不触碰板卡，板卡保持关机。
- 下一责任方：Hardware-A / Codex 实现并训练本轮，失败也提交。

### [PS-20261021-10] 有声 log-F0 辅助回归 Round 43 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_BEST_SO_FAR
- 基准提交：`d0c5fc0`
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/paired_hubert_world_voiced_f0_round43_20261025.{md,json}`、`coummucation.md`。
- 训练：478347 参数不变；第 1200 步验证最佳 `0.622741`，有声 F0 辅助误差 `0.092130`；第 2000 步早停并恢复，因果前缀差异 `0.0`。
- Track 9：**0.7054/0.6844/0.1424/1.9519/0.0978**（身份/P10/男性质心余弦/UTMOS/CER）。目标自重建不应用泄漏门；UTMOS 失败。
- 对比 Round37：身份 `+0.0101`、P10 `+0.0050`、UTMOS `+0.0903`、CER `-0.0109`；全部适用指标改善，更新为当前配对 WORLD 最佳。
- 哈希：checkpoint `4acf292f…15b6b`，WAV `45e74e06…94149`；推理参数/MAC/延迟不变。
- 限制：离线源韵律非因果；未播放、未使用固定男性输入，板卡保持关机。
- 报告链接：`report/paired_hubert_world_voiced_f0_round43_20261025.md`、`report/paired_hubert_world_voiced_f0_round43_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交本轮；下一轮先在独立验证句审计 F0 误差与 UTMOS 是否同步改善，不直接扫描更大权重。

### [PS-20261021-10] Round43 独立验证回归 Round 44 认领
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`c62fe48`
- 范围：在与 Round38 相同的 8 条独立验证句上加载 Round43 checkpoint，以相同教师、合成器和 UTMOS 评估器复测，并与 Round37 逐句比较；同时报告 log-F0 动态比。
- 决策门：Round43 平均 UTMOS 高于 Round37，且至少 6/8 句不退步，才允许保留 log-F0 辅助项作为后续基线；否则视为 Track 9 偶然收益并回退 Round37。
- 限制：不训练、不使用 Track 9、不使用固定男性输入、不播放；不触碰板卡，板卡保持关机。
- 下一责任方：Hardware-A / Codex 运行独立验证并提交 KEEP/REVERT。

### [PS-20261021-10] Round43 独立验证回归 Round 44 结果
- 日期：2026-10-25
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：REVERT_ROUND43_RETAIN_ROUND37
- 基准提交：`7c0e40c`
- 修改路径：`report/round43_validation_round44_20261025.{md,json}`、`coummucation.md`。
- UTMOS：Round43 在 8 条验证句均值 `2.00370`，Round37 为 `2.00545`，差 `-0.00176`；仅 `5/8` 句改善，未达到至少 `6/8` 门。最大单句回退 `-0.18786`。
- F0：标准差比由 `0.8548` 改善到 `0.9902`，动态 RMS 比由 `1.1186` 到 `1.1085`，但未稳定转化为 UTMOS。
- 判定：Round43 的 Track 9 提升不具稳定泛化，保留证据但回退 Round37 为稳健基线；禁止直接扫描更大 F0 权重。
- 限制：未训练、未使用 Track 9、未播放、未使用固定男性输入；板卡保持关机。
- 报告链接：`report/round43_validation_round44_20261025.md`、`report/round43_validation_round44_20261025.json`。
- 下一责任方：Hardware-A / Codex 提交诊断；下一轮先分析按句/说话人的 F0 归一化与收益方向，不直接训练。

### [PS-20261021-10] 多轨提示 CFG 增强 Round 14 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`cf1a079`
- 唯一变量：Round 11 的 2+2+2+4 秒提示上比较 CFG=1.25/1.40；模型、30 步、seed、起点裁切和评估器不变。
- 修改路径：`report/seed_fixed_male_cfg_round14_20261024.{md,json}`、`coummucation.md`。
- 量化结果：CFG 1.25 为 **0.5637/0.5086/0.1145/2.7476/0.0816**；CFG 1.40 为 **0.5753/0.4961/0.1343/2.7832/0.0816**（身份/P10/泄漏/UTMOS/CER），两者均泄漏失败。
- 判定：CFG 1.25 有改善但未过门，1.40 反弹；按预设止损，不继续提高 CFG。
- 报告链接：`report/seed_fixed_male_cfg_round14_20261024.md`、`report/seed_fixed_male_cfg_round14_20261024.json`。
- 限制：输出未播放，未触碰板卡，v23 保底不变；无真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 评估固定小种子库的确定性选择规则，使用允许的固定男性源画像降低扩散随机性带来的泄漏失败。

### [PS-20261021-10] 固定种子库稳健选择 Round 15 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`adb633f`
- 方案：恢复 Round 11 的 2+2+2+4 秒提示与 CFG=1.10，固定测试种子库 `{20261018, 20261019, 20261020, 20261021}`；已知 20261018 在 Round 12 泄漏失败，仅补跑后三个。
- 选择规则：使用固定男性录音 1～3 的源画像与 Track 5～8 目标画像，按现有严格评估器选“五门全部通过后目标身份最高”的候选；保底阶段允许源专用配置。规则、种子库和门槛在下一条新会话前必须冻结。
- 成功标准：Round 12 至少一个新种子五门通过；随后同一规则必须在录音 4/5 与 Round 3/7/9 上回放选择结果并全部通过，才可请求新的盲测。
- 边界：这是电脑端离线质量上限的多次扩散选择，不能宣称 Cortex-A9、板端或实时可行；不播放、不改 v23。
- 下一责任方：Hardware-A / Codex 完成固定种子库评估并按结果提交。

### [PS-20261021-10] 固定种子库稳健选择 Round 15 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`3c0088b`
- 修改路径：`report/seed_fixed_male_seedbank_round15_20261024.{md,json}`、`coummucation.md`；生成 WAV 和完整临时指标留在忽略目录。
- 量化结果：seed 20261019 为 **0.4985/0.3594/0.1020/2.7636/0.0612**；20261020 为 **0.5178/0.4043/0.1129/2.9086/0.0612**；20261021 为 **0.5683/0.4961/0.1472/2.7668/0.0408**（身份/P10/泄漏/UTMOS/CER）。加上 Round 12 已知 seed 20261018 的泄漏 `0.1250`，四个种子均无五门全过者。
- 判定：固定种子库规则无可选候选，拒绝并停止扩展到旧回归集；最接近的 seed 20261019 仅泄漏超门 `0.002018`，第三窗 `0.153405` 是主要残留来源。
- 报告链接：`report/seed_fixed_male_seedbank_round15_20261024.md`、`report/seed_fixed_male_seedbank_round15_20261024.json`。
- 限制：输出未播放，未触碰板卡，v23 最大音量上电保底不变；无真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 以 seed 20261019 为最近基线，探索只针对末段泄漏的受限后处理；必须同时保持身份、P10、UTMOS 和 CER 过门。

### [PS-20261021-10] 末段轻量升调抑漏 Round 16 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`69a64dc`
- 根因证据：Round 15 的 seed 20261019 只有泄漏 `0.102018` 略高于 `0.10`；其三个评估窗泄漏分别为 `0.088546/0.038714/0.153405`，问题集中在 12 秒后的末窗；末窗身份也最低，为 `0.301558`。
- 唯一变量：保持 seed 20261019 原始输出前 12 秒完全不变，只对 12 秒后的末段分别尝试 `+0.5/+1.0/+1.5` 半音的保时升调，并在边界做 100 ms 交叉渐变。候选数预先固定为三个，不按结果追加点位。
- 成功标准：五门必须全部通过；若多个通过，选择目标身份最高者。通过后须用同一固定后处理回归录音 4/5 与 Round 3/7/9，全部通过才可冻结并请求下一条新会话。
- 止损：任一候选出现 CER、P10 或 UTMOS 失败即不放宽门槛；三个候选均无五门全过则拒绝该路线。
- 限制：电脑端离线开发，不播放、不触碰板上 v23；Remote-PS-C 不负责验证本方案，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 实现最小后处理器并严格评估三个固定候选。

### [PS-20261021-10] 末段轻量升调抑漏 Round 16 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`e7f5218`
- 修改路径：`build/postprocess_seed_fixed_male_tail_pitch_20261024.py`、`report/seed_fixed_male_tail_pitch_round16_20261024.{md,json}`、`coummucation.md`。
- Round 12 筛选：`+0.5` 半音为 **0.5609/0.5023/0.0801/2.3096/0.0204**，五门通过；`+1.0` 泄漏 `0.1409`，`+1.5` 泄漏 `0.1794`、UTMOS `2.2956`、CER `0.2245`，均失败。
- 固定回归：录音 4 CER `0.2353` 失败；录音 5 泄漏 `0.1387`、UTMOS `2.1064` 失败；Round 3 UTMOS `2.2835` 失败；Round 7、Round 9 和 Round 12 通过。六组仅三组全过。
- 判定：固定 12 秒边界后处理不具备跨语句稳健性，拒绝作为统一方案，不请求试听。
- 报告链接：`report/seed_fixed_male_tail_pitch_round16_20261024.md`、`report/seed_fixed_male_tail_pitch_round16_20261024.json`。
- 限制：生成 WAV 未播放、未提交，未触碰板卡，v23 最大音量上电保底不变；无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 将已通过旧五组的 seed 20261018 原始候选与仅修复 Round 12 的 seed 20261019/+0.5 半音候选组成固定、门控的两候选库，验证是否能在所有已暴露数据上确定性选到五门全过输出。

### [PS-20261021-10] 两候选严格门控 Round 17 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`8238803`
- 固定候选 A：Round 11 配置，seed=20261018，Track 5～7 各 2 秒 + Track 8 4 秒、CFG=1.10、30 步、持续语音起点裁切，无后处理。
- 固定候选 B：与 A 仅 seed 改为 20261019，并对 12 秒后末段作 `+0.5` 半音保时升调与 100 ms 交叉渐变。
- 选择规则：对同一输入生成 A/B；使用固定男性录音 1～3 源画像、Track 5～8 目标画像和现有严格评估器，先剔除任一门失败者，再在五门全过者中选择目标身份均值最高者；若两者均失败则整条输入失败。不得按数据集更改候选、门槛或规则。
- 成功标准：用既有不可变指标复核录音 4/5、Round 3/7/9/12 六组，必须每组至少一个候选五门全过；形成机器可读选择清单后冻结，下一步必须采全新会话盲测。
- 边界：电脑端多候选质量上限，不宣称 Cortex-A9、板端或实时可行；不播放、不触碰 v23。Remote-PS-C 不负责验证本方案。
- 下一责任方：Hardware-A / Codex 实现确定性门控清单生成器、复核六组已有指标并提交。

### [PS-20261021-10] 两候选严格门控 Round 17 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：PROPOSED / WAIT_NEW_SESSION
- 基准提交：`daef166`
- 修改路径：`build/select_seed_fixed_male_candidates_20261024.py`、`report/seed_fixed_male_gated_bank_round17_20261024.{md,json}`、`report/seed_fixed_male_gated_bank_round17_evidence_20261024.json`、`coummucation.md`。
- 固定规则：候选 A 为 seed 20261018 原始 Round 11 配置；候选 B 为 seed 20261019 加 12 秒后 `+0.5` 半音末段处理。先剔除任一门失败者，再取目标身份最高者；无合格候选则失败。
- 量化选择：录音 4/5、Round 3 选择 A；Round 7/9/12 选择 B。六组均存在五门全过候选，机器清单 `all_datasets_pass=true`。
- 判定：已暴露开发回归通过，冻结候选、门槛和选择规则；不得据此声明新会话或真人听感通过。下一步必须使用不同文本的新会话，只生成 A/B 各一次并门控。
- 报告链接：`report/seed_fixed_male_gated_bank_round17_20261024.md`、`report/seed_fixed_male_gated_bank_round17_20261024.json`。
- 限制：电脑端多候选质量上限；生成 WAV 未播放、未提交，未触碰板上 v23；无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。Remote-PS-C 不负责验证。
- 下一责任方：现场操作者明确准备后，Hardware-A 采全新不同文本；传回电脑仍需本轮单独授权，随后冻结盲测 A/B。

### [PS-20261021-10] 两候选冻结新会话盲测 Round 18 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：CLAIMED（操作者已对本轮明确回复“准备好了”）
- 基准提交：`d4e1aad`
- 冻结候选：A 为 seed 20261018 原始 Round 11 配置；B 为 seed 20261019 并对 12 秒后末段作 `+0.5` 半音、100 ms 交叉渐变。两者均为 Track 5～7 各 2 秒 + Track 8 4 秒、CFG=1.10、30 步和持续语音起点裁切。
- 冻结门控：先剔除身份 <0.45、P10 <0.35、泄漏 >0.10、UTMOS <2.30 或 CER >0.15 的候选，再选目标身份最高者；均失败则整条输入失败。
- 朗读文本：午后的图书馆很安静，管理员把新书放进书架。窗外的树叶轻轻摇动，一辆校车停在门口，几名学生背着书包走进大厅。
- 操作范围：COM4 短暂停止 v23 服务，播放 300 ms 提示音后采集同一男性 20 秒，随即恢复 v23 最大音量上电保底。录音、转换 WAV 和串口日志只放忽略目录。
- 数据纪律：采集完成后，在把真人录音传回电脑前必须取得本轮单独明确授权；之后 A/B 各只生成一次，不按结果调参。客观全过后才请求真人试听。
- 限制：Seed-VC 不部署到板上；本轮无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。Remote-PS-C 不负责验证。
- 下一责任方：Hardware-A 完成采录、恢复板端保底并请求本轮录音传输授权。

### [PS-20261021-10] 两候选冻结新会话盲测 Round 18 客观结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：ACCEPTED_OBJECTIVE / WAIT_LISTENING
- 基准提交：`4422a94`
- 修改路径：`board/capture_fixed_male_new_session.py`、`report/seed_fixed_male_gated_blind_round18_20261024.{md,json}`、`coummucation.md`；真人录音、候选 WAV 和串口日志未提交。
- 采录与授权：操作者采录前明确准备，完成后单独授权传输。20 秒 WAV SHA-256 `dc3b4a61854e2f00b299dbe3ad0016f6cc087cc4e2ce9836366bd65fa59a5ad1`，零削波，起点裁切 3.37 秒。
- 冻结候选 A：**0.5793/0.5380/0.0846/2.8078/0.1250**（身份/P10/泄漏/UTMOS/CER），五门全过，输出 SHA-256 `4b613d2430793b0489f76a83d656817cde4dd48aac47dff975a26298291c6fe0`。
- 冻结候选 B：**0.5721/0.4765/0.0787/2.2575/0.0625**，仅 UTMOS 失败，被门控剔除。按冻结规则选择 A；未把不属于冻结 B 的原始 seed19 诊断输出用于选择。
- 判定：冻结后的不同文本新会话客观盲测通过；必须由现场操作者试听所选 A 后，才能判定目标女声相似度与男声残留。当前未播放。
- 板端状态：恢复单实例 v23，录放 PCM 长时间后检均运行；Headphone 127、Playback 255。Seed-VC 未部署，上电保底未变。
- 报告链接：`report/seed_fixed_male_gated_blind_round18_20261024.md`、`report/seed_fixed_male_gated_blind_round18_20261024.json`。
- 下一责任方：现场操作者再次明确准备后，Hardware-A 仅播放所选 A 一次并记录原话听感；随后恢复并复核 v23 最大音量。

### [PS-20261021-10] 两候选冻结新会话 Round 18 真人试听结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：REJECTED（真人目标音色失败；停止继续扩展 Seed 路线）
- 基准提交：`d45568d`
- 用户原话：“男声感强烈，感觉seed方案进行这么多轮次，效果不是很好，原来的world方案为什么不用了”。
- 播放条件：操作者明确准备；仅播放客观门控选中的 A 一次。原输出 SHA-256 `4b613d2430793b0489f76a83d656817cde4dd48aac47dff975a26298291c6fe0`；32 kHz 双声道 PCM24 兼容 WAV SHA-256 `72e6dfb9d681447c1df92aed7445e992ae396c5d52bd2fe997cae85822c8d650`，16.6255 秒，`PLAY_RC=0`、无 underrun。
- 客观/主观冲突：A 的身份/P10/泄漏/UTMOS/CER 为 **0.5793/0.5380/0.0846/2.8078/0.1250**，五门全过；但真人仍听到强烈男声感，故最终否决。客观门不能替代真人音色判断。
- 路线决策：Seed 多轮没有解决目标女声相似度，不再追加 seed、提示拼接或局部升调轮次；优化焦点返回一直保留且正在板上运行的 WORLD v23 保底。
- 板端状态：试听后单实例 WORLD v23 已恢复，录放 PCM 均运行；Headphone 127、Playback 255。Seed 从未部署，上电方案未变。
- 报告链接：`report/seed_fixed_male_gated_listening_round18_20261024.md`、`report/seed_fixed_male_gated_listening_round18_20261024.json`。
- 下一责任方：Hardware-A / Codex 复盘 WORLD 既有主客观证据，以 v23 清晰、实时、可上电为基线重新认领固定男性到既定女声的音色优化；不得用 Seed 客观分数覆盖本次真人结论。

### [PS-20261021-10] WORLD v23 固定男声 F0 映射 Round 19 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`464f148`
- 目标与本轮唯一变量：保留 v23/WORLD 的共振峰缩放 `1.0975`、无平均谱修正和原非周期分量，仅把固定倍率 F0 改为已登记固定男性到既定女性目标的有界 log-F0 映射；解决历史真人反馈“2 更清晰、音色上更像，但是音高差一点”。
- 输入与数据切分：复用已获传输授权的 Round 18 固定男性录音作已暴露开发回归；参数只能来自既有源登记和目标 Tracks 5～8，不得用 Round 18 输出反向拟合。Track 9 继续作为目标留出。
- 对照：同一输入同时生成现役 v23 固定倍率基线和本轮 F0 映射候选；生成 WAV 只留在 `build/generated/`，不提交、不播放。
- 成功门槛：身份均值 ≥0.45、P10 ≥0.35、严格源泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；并要求候选不得同时恶化身份、自然度和内容。任一门失败即拒绝，不请求试听。
- 限制：本轮不改板上 v23、不访问声卡、不采录、不播放；无 Cortex-A9、实时、Vivado、RTL 或 PL 新结论。Remote-PS-C 不负责验证本方案。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 实现最小离线对照并运行严格五门评估。

### [PS-20261021-10] WORLD v23 固定男声 F0 映射 Round 19 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`6b83909`
- 修改路径：`build/run_world_v23_f0_round19_20261024.py`、`report/world_v23_f0_round19_20261024.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/world_v23_f0_round19_20261024.md`；生成 WAV、原始清单和原始指标只在 `build/generated/world_v23_f0_round19_20261024/`，未提交。
- 对照结果：现役固定倍率为 **0.2206/0.1919/0.3287/1.7539/0.1458**（身份/P10/泄漏/UTMOS/CER），仅 CER 通过。
- 候选结果：登记式 log-F0 为 **0.2475/0.2222/0.3302/1.8271/0.0625**，同样仅 CER 通过；身份、P10、UTMOS 和 CER 优于对照，但严格泄漏微升 `0.0015`。
- 判定：身份、P10、泄漏、UTMOS 四门失败，按冻结规则不请求试听、不部署；仅替换 F0 无法消除 WORLD 的源说话人泄漏，停止继续扫 F0 强度或倍率。
- 限制：Round 18 是已暴露开发回归；本轮未播放、未改板上 v23，板上最大音量上电保底保持不变；无 Cortex-A9、实时、Vivado、RTL 或 PL 新结论。Remote-PS-C 不负责验证。
- 报告链接：`report/world_v23_f0_round19_20261024.md`、`report/world_v23_f0_round19_20261024.json`。
- 下一责任方：Hardware-A / Codex 若继续 WORLD，下一轮必须改变音色/源泄漏建模本身，而不是只调 F0；开始前另行认领。

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

### [PS-20261021-10] Round 9 冻结候选真人试听 Round 10 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：REJECTED（客观五门通过，但真人目标音色未通过）
- 基准提交：`36aa531`
- 修改路径：`report/seed_fixed_male_listening_round10_20261024.{md,json}`、`coummucation.md`；音频与串口日志在忽略目录，未提交。
- 测试条件：操作者明确准备；原始候选先因 22.05 kHz 格式被板卡拒绝且未播出，随后同一内容转换为 32 kHz/双声道/PCM24，只成功播放一次，`PLAY_RC=0`、无 underrun。
- 试听文件：原候选 SHA-256 `f6880252d63839e7ba64b5141a7d3babd6cdc2ddd451915ca99062622234d0ac`；兼容播放 WAV SHA-256 `7f595754207da7f872aae23ea478d5b2b1c3d5eec38e1f3f12c2de312433fd23`。
- 客观结果：沿用 Round 9 冻结评测 **0.5200/0.4719/0.0591/3.0789/0.1020**（身份/P10/严格泄漏/UTMOS/CER），五门通过。
- 用户原话：**“清晰度比以前好，但是没有更像目标女声，男声残留明显”**。
- 判定：真人听感具有否决权；本候选目标音色不合格，不能升级或部署。现有说话人身份/泄漏指标对可感知男声残留不充分，后续须针对目标音色和源残留继续优化。
- 板端状态：已恢复单实例 v23 最大音量保底，录放 PCM 均运行；Headphone 127、Playback 255。Seed-VC 未部署，上电方案未变。
- 报告链接：`report/seed_fixed_male_listening_round10_20261024.md`、`report/seed_fixed_male_listening_round10_20261024.json`。
- 下一责任方：Hardware-A / Codex 在电脑端分析目标条件强度与可感知源残留，形成新冻结候选；现场再次试听前另问操作者准备状态。Remote-PS-C 不负责验证本方案。

### [PS-20261021-10] 多轨目标提示听感修复 Round 11 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`a05abeb`
- 根因证据：Round 10 真人试听认为单 Track 8 十秒提示候选“清晰度比以前好，但是没有更像目标女声，男声残留明显”；客观身份与泄漏门未充分反映可感知残留。
- 方案依据：2026-10-18 的既有真人对照中，Track 5～8 各 2 秒的多轨目标提示相对单轨提示被评价为更像目标、闷感更少。Round 11 只恢复该目标提示结构并在已暴露的 Round 9 语句上筛选 CFG，不改变模型、30 步、种子、起点裁切或评估器。
- 数据纪律：Round 9 录音已暴露，只用于开发选参；新候选客观门通过后仍须新会话冻结验收，之后才可再次请求真人试听。
- 限制：只做电脑端离线开发；不改板上 v23，不产生 Cortex-A9、实时、Vivado、RTL 或 PL 结论；Remote-PS-C 不负责验证本方案。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A / Codex 运行多轨提示 CFG 筛选与已暴露回归，逐轮保存客观结果。

### [PS-20261021-10] 多轨目标提示听感修复 Round 11 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：PROPOSED / WAIT_NEW_SESSION
- 基准提交：`efcb5f2`
- 方案：Track 5～7 各取 2 秒高活动片段、Track 8 取 4 秒高活动片段，总提示 10 秒；冻结 CFG=1.10、seed=20261018、30 步和持续语音起点裁切。提示 SHA-256 `0f70b18eef37614ce0f866f989cf5376bd237e410ffb6f1e85b70ec4c2909391`。
- 修改路径：`build/run_seed_fixed_male_strict_20261024.py`、`report/seed_fixed_male_multitrack_round11_20261024.{md,json}`、`coummucation.md`。
- 量化结果：录音 4 **0.6411/0.6244/0.0887/2.7582/0.1176**；录音 5 **0.6371/0.5799/0.0952/2.9058/0.0375**；Round 3 **0.5438/0.4677/0.0646/2.7469/0.1311**；Round 7 **0.6592/0.6466/0.0714/2.7960/0.0769**；Round 9 **0.5913/0.5800/0.0762/2.9314/0.1429**（身份/P10/泄漏/UTMOS/CER），五组均五门通过。
- 对照：纯四轨各 2 秒、CFG=0.95 在录音 5 的泄漏 `0.1148`，已拒绝；折中提示将其降为 `0.0952`。相对 Round 10 被真人否决的单轨方案，Round 9 身份由 `0.5200` 升至 `0.5913`、P10 由 `0.4719` 升至 `0.5800`。
- 人体证据依据：2026-10-18 既有真人对照认为多轨提示比单轨提示更像目标、闷感更少；本轮尚未产生新的真人听感。
- 限制：五组数据均已暴露，只能作开发回归；必须再用冻结后的全新会话盲测。未播放、未录音、未改板上 v23，无 Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 报告链接：`report/seed_fixed_male_multitrack_round11_20261024.md`、`report/seed_fixed_male_multitrack_round11_20261024.json`。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：现场操作者再次明确准备后，Hardware-A 采另一条不同文本的新会话并只运行冻结候选一次；客观通过后再请求真人试听。

### [PS-20261021-10] Round 11 冻结后新会话盲测 Round 12 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：CLAIMED（操作者已对本轮明确回复“准备好了”）
- 基准提交：`1e15794`
- 冻结候选：Seed-VC V2、30 步、CFG=1.10、seed=20261018、Track 5～7 各 2 秒 + Track 8 4 秒的十秒目标提示，以及持续语音起点裁切；本轮不再调参，只运行一次。
- 朗读文本：清晨的阳光照进车站，值班员打开窗户查看时刻表。远处的列车缓缓驶来，站台上的旅客提起行李，准备开始今天的旅程。
- 操作范围：短暂停止 v23 自启动录放服务，播放 300 ms 提示音并等待 150 ms 后采集同一男性 20 秒；随后恢复同一 v23 最大音量自启动服务。
- 数据规则：录音、转换 WAV 和串口日志只放 `build/generated/` 忽略目录；把真人录音传回电脑前仍需本轮单独明确授权。
- 成功门槛：身份均值 ≥0.45、P10 ≥0.35、严格泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；任一失败不请求试听。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)。
- 下一责任方：Hardware-A 完成采录和 v23 恢复；获得传输授权后只运行冻结候选一次。

### [PS-20261021-10] Round 11 冻结后新会话盲测 Round 12 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex
- 状态：REJECTED（严格源泄漏失败；任务继续）
- 基准提交：`0daf836`
- 修改路径：`board/capture_fixed_male_new_session.py`、`report/seed_fixed_male_new_session_round12_20261024.{md,json}`、`coummucation.md`；真人录音、生成 WAV 和日志均未提交。
- 采录与授权：操作者先明确准备，再单独授权传输；20 秒 WAV SHA-256 `f61e055288a7b0dc63db256f45e4b0d6fa60ccae1d0aa382b9a45f22e90a2702`，零削波，冻结裁切起点 `2.15 s`。
- 冻结候选：Seed-VC V2、Track 5～7 各 2 秒 + Track 8 4 秒的十秒提示、30 步、CFG=1.10、seed=20261018、持续语音起点裁切；只运行一次，未调参。
- 量化结果：**0.5666/0.5082/0.1250/2.7704/0.0408**（身份/P10/严格泄漏/UTMOS/CER）；身份、P10、UTMOS、CER 通过，泄漏 `0.1250 > 0.10` 失败。第三窗泄漏最高 `0.1637`。
- 判定：不请求试听；这条新会话已经暴露，只能用于后续开发回归。用户此前感知的男声残留风险在本条严格泄漏中再次出现。
- 板端状态：恢复单实例 v23 最大音量保底，录放 PCM 均运行；Headphone 127、Playback 255。Seed-VC 未部署，上电方案未变。
- 报告链接：`report/seed_fixed_male_new_session_round12_20261024.md`、`report/seed_fixed_male_new_session_round12_20261024.json`。
- 提交或 PR：分支 `agent/Pi-debug-cmd/PS-20261021-10`，继续更新 PR [#10](https://github.com/Pi-debug-cmd/2026_FPGA/pull/10)；结果提交待回填。
- 下一责任方：Hardware-A / Codex 在电脑端用本条已暴露录音收紧目标提示，优先降低源残留，同时保持多轨目标音色依据；形成新冻结候选后再采全新会话。

### [PS-20261021-10] 多轨权重收紧 Round 13 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`ea3f005`
- 根因证据：Round 12 的 2+2+2+4 秒多轨提示在新会话严格泄漏 `0.1250`，第三窗 `0.1637`；但多轨提示有历史真人“更像目标、闷感更少”的证据，不能直接退回已被 Round 10 真人否决的纯 Track 8 提示。
- 唯一变量：保持模型、30 步、CFG=1.10、seed、起点裁切和总提示 10 秒不变；将 Track 5～7 从各 2 秒收紧为各 1 秒，Track 8 从 4 秒增加为 7 秒。
- 开发顺序：先在已暴露 Round 12 上验证泄漏是否回到 ≤0.10，再回归录音 4/5 与 Round 3/7/9；任一门失败即拒绝或继续调整，不请求试听。
- 限制：电脑端离线开发，不改板上 v23；Remote-PS-C 不负责验证本方案；无真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 实现新的十秒提示结构并运行严格评估。

### [PS-20261021-10] 多轨权重收紧 Round 13 结果
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`421fed6`
- 唯一变量：目标提示由 Track 5～7 各 2 秒 + Track 8 4 秒改为 Track 5～7 各 1 秒 + Track 8 7 秒；总时长、模型、30 步、CFG=1.10、seed、起点裁切和评估器不变。
- 修改路径：`build/run_seed_fixed_male_strict_20261024.py`、`report/seed_fixed_male_weighted_round13_20261024.{md,json}`、`coummucation.md`。
- 量化结果：Round 12 已暴露新会话为 **0.4916/0.4523/0.1382/2.6273/0.0612**（身份/P10/泄漏/UTMOS/CER），严格泄漏失败；相对原候选身份 `0.5666`、泄漏 `0.1250` 同时恶化。
- 判定：拒绝；增加 Track 8 占比不能单调降低源残留，不扩展到其他回归集、不请求试听。
- 报告链接：`report/seed_fixed_male_weighted_round13_20261024.md`、`report/seed_fixed_male_weighted_round13_20261024.json`。
- 限制：输出未播放，未触碰板卡，v23 保底不变；无真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 结论。
- 下一责任方：Hardware-A / Codex 回到 Round 11 的 2+2+2+4 秒提示，仅探索适度增强 CFG 是否能降低 Round 12 源残留且保持内容门。

### [PS-20261021-10] 多轨提示 CFG 增强 Round 14 认领
- 日期：2026-10-24
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`aa36af8`
- 方案：恢复 Round 11 的 Track 5～7 各 2 秒 + Track 8 4 秒提示；保持模型、30 步、seed 和起点裁切不变，只在已暴露 Round 12 上比较 CFG=1.25/1.40。
- 成功标准：严格泄漏必须从 `0.1250` 降到 ≤0.10，同时身份/P10/UTMOS/CER 保持过门；通过后才扩展到录音 4/5 与 Round 3/7/9 回归。
- 止损：若两个 CFG 都未降低泄漏或造成 CER 失败，本路线立即停止，不追加更高 CFG；既有 1.70 已有内容塌缩证据。
- 限制：电脑端离线开发，不播放、不改板上 v23；Remote-PS-C 不负责验证本方案。
- 下一责任方：Hardware-A / Codex 完成 CFG 筛选并按结果提交。

### [PL-20261027-01] WORLD v23 复数 exp 卸载认领
- 日期：2026-10-27
- 角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：`e507cf7`；分支：`agent/Pi-debug-cmd/PL-20261027-01`。
- 用户本轮明确停止 Deepseek，指定以已经试听认可的 WORLD v23 为基线部署 PL；本任务据此恢复 v23 加速，不宣称已通过固定目标身份、陌生多人或最终注册门。
- 协作检查：已检查开放 PR #9/#11/#13/#15，无 WORLD v23 PL 重叠；根工作区保留 10-22 未提交文件，使用独立 worktree，禁止覆盖。
- 范围：`src/rtl/synth_offload/`、新增 WORLD exp DMA 构建/驱动/报告；复用 10-22 已验证的 exp 核，PS 保留双精度 FFT。
- 复现：将随首轮报告给出完整命令；当前只完成只读核验 `sha256sum /opt/world_voice/world_budget_v23`。
- 量化：板端 v23 SHA256 为 `f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7`，与既存基线一致；历史 exp 核 49248 bins 零 LSB、100MHz OOC WNS +4.584ns，仅作历史结果，尚非本轮整机/板测。
- 限制：板端无 udmabuf 或现成 DMA 设备，必须先解决一致性内存；不改启动分区，现场录放须当轮确认。
- 下一责任方：Hardware-A / Codex 完成 AXIS/DMA 整机实现、数值与板端耗时验证；依据 `report/pl_synth_offload_route_update_20261022.md`（待导入原件）。

### [PL-20261027-01] WORLD exp 集成首轮方案与静默回归
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED。
- 基准提交：`e507cf7`；改动：`src/rtl/synth_offload/`、`src/ps/world_v23/`、`src/ps/world_exp*`、`src/kernel/world_exp*`、`build/*world_exp*`、`board/world_exp_switch.py`。
- 复现：见 `report/world_exp_round1_20261027.md`，上游及优化源SHA见同名JSON；生成物不入Git。
- 量化：随机背压RTL 49248 bins零LSB/零TLAST错误；受控标准录音1/4前5秒软件模型回归 SNR 79.06/78.57dB、最大PCM16误差3/2；ARM/host和匹配内核驱动已编译。
- 限制：整机P&R尚在运行，未加载新位流，未录放、未宣称板端提速或实测端到端延迟；原v23保留运行。
- 下一责任方：Hardware-A / Codex 完成整机实现、板端数值与耗时测试，再经当轮准备确认安排现场回归。

### [PL-20261027-01] Cortex-A9 静默 CPU 等价回归
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（仅本项文件回归）。
- 基准提交：`45b167d`，实现 `50974e2`；改动：`board/world_exp_file_trial.py`、`report/world_exp_cpu_board_20261027.{md,json}`、`coummucation.md`。
- 复现：报告内 `python3 world_exp_file_trial.py --base /tmp/codex_world_exp_20261027 --cpu-only`；输入与首轮标准录音1完全相同。
- 量化：新CPU与原v23的80000样本逐字节一致；模型相对CPU SNR79.0566dB、最大PCM16误差3、1227次零fallback；三路均零削顶。
- 恢复准备：原厂bit已核验，/tmp恢复载荷SHA `af275946c15ae958e9bed16c12f6cab45b63ebecc18645cec24176315db7fc60`；未切PL、不改启动分区。v23为稳定串口传输暂时停止，此轮无录放。
- 限制：模型ARM耗时非PL速度；分析RTF约0.55仍是瓶颈。无现场听感/PL/实测延迟通过结论。
- 下一责任方：Hardware-A / Codex 完成P&R/MCP复核并执行硬件向量和文件回归。

### [PL-20261027-01] 整机布局布线与 Vivado MCP 复核
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（仅实现门）。
- 基准提交：`69544be`；改动：`build/implement_world_exp_20261027.tcl`、`build/package_world_exp.py`、`report/world_exp_implementation_20261027.*`及四项`world_exp_routed_*_20261027.txt`。
- 复现：报告内独立Vivado构建及MCP打开完整routed DCP；未覆盖旧工程。
- 量化：100MHz WNS+1.391ns/WHS+0.036ns，零失败端点/黑盒/DRC Error；8026LUT/13283FF/6BRAM/9DSP，bus skew最小裕量+8.996ns。
- 限制：外部音频/I2C延时约束未完全签核；仍有DRC Warning/Advisory。位流已校验传输，尚未加载或进行PL板测。
- 报告：`report/world_exp_implementation_20261027.md`、同名JSON；下一责任方：Hardware-A / Codex 执行静默硬件数值与文件回归。

### [PL-20261027-01] 临时加载后的声卡就绪检查竞态
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：REJECTED（切换脚本就绪检查，非RTL数值）。
- 基准提交：`20344a5`；改动：`board/world_exp_switch.py`、`report/world_exp_load_race_20261027.json`。
- 复现：报告所记校验SHA的`world_exp_switch.py --load`；恢复位流已核验。解绑旧PL消费者后候选已成功加载、FPGA operating。
- 失败：bind返回后立即断言`/dev/snd/controlC0`，与声卡异步注册/udev生成竞态；随后只读检查card0及所有PCM节点齐全、FPGA仍operating。未打开音频或DMA，未请求现场试听。
- 修复：增加最多15秒的节点就绪等待；新增`--keep-stopped`允许静默恢复原厂位流，避免恢复服务自动提示音未经当轮确认。
- 限制：当前仍是候选位流、音频服务停止，尚未有DMA/PL语音结果；不能把就绪检查失败写成硬件加速通过。
- 下一责任方：Hardware-A / Codex 使用当前已就绪声卡完成静默DMA与文件测试；失败即静默恢复。

### [PL-20261027-01] PL首轮板端文件：数值通过、性能拒绝
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：REJECTED（性能门）。
- 基准提交：`8563cee`，实现程序`50974e2`；改动：`report/world_exp_{dma,pl}_board_round1_20261027.json`、PL同名MD及本记录。
- 复现：报告中的probe与四路径文件命令；候选位流SHA与原厂恢复SHA已核验，只在/tmp，不改启动。
- 数值：49248 bins全64bit零差异；PL与模型80000语音样本逐字节一致；相对v23 SNR79.0566dB、最大误差3、1227次零fallback。
- 性能：DMA均值90.799µs，p95 91.248µs；但PL接口总323µs/调用，渲染RTF0.339278比CPU0.326107略差；整链未提速，不能验收加速。
- 限制：没有录放或听感结论，候选临时驻留、v23服务停止；分析RTF约0.55仍为另一瓶颈。
- 下一责任方：Hardware-A / Codex 优化逐bin remainder/floor/打包并加入分项计时；同输入重复静默回归，性能过后再请求现场确认。

### [PL-20261027-01] PS接口优化 Round 2 方案
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED。
- 基准提交：`724464a`；改动：`src/ps/world_exp_hook.cpp`、`report/world_exp_round2_proposal_20261027.md`及本记录。
- 唯一主要变量：以截断+负数纠正替代逐bin floor，常用相位范围跳过remainder，新增prepare/DMA/unpack计时；PL、音频算法、量化和输入不变。
- 复现：首轮构建与`check_world_exp_quality.py`相同命令；host男声1 SNR79.0566dB/最大误差3保持一致，ARM已编译。
- 限制：新程序正在静默传输，还未有本轮板端耗时；候选位流驻留、音频服务停止，无录放。
- 下一责任方：Hardware-A / Codex 同输入板端四路径回归并提交性能结果。

### [PL-20261027-01] Round 2 精确取整优化板端结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（局部优化，非整链验收）。
- 基准提交：`3483bae`；改动：`report/world_exp_pl_board_round2_20261027.{json,md}`及本记录。
- 复现：相同文件四路径命令；PL位流不变。PL=模型逐字节一致，v23=新CPU逐字节一致；相对v23 SNR79.0566dB/最大误差3/1227次零fallback。
- 量化：PL接口0.396830→0.250069s；准备0.112455/DMA0.121293/解包0.016321s；渲染RTF0.309557，总墙钟2.792953s，分析RTF0.551393仍主导。
- 限制：只接受该局部优化，不能宣布整链高实时通过；未录放，候选驻留、音频服务停止。
- 下一责任方：Hardware-A / Codex 检查逐bin相位remainder，随后同输入回归。

### [PL-20261027-01] Round 3 相位打包与现场入口方案
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED。
- 基准提交：`ffe7189`；改动：`src/ps/world_exp_hook.cpp`、`board/live_world_trial.py`、`report/world_exp_round3_proposal_20261027.md`及本记录。
- 复现：前轮构建与host男声1回归；SNR79.0566dB/最大PCM16误差3不变。ARM新程序传输中，尚未板测。
- 唯一算法外变量：有界圈数乘减替代remainder，PL和语音算法不变；监督入口新增独立base/ALSA参数和按kind解析日志，默认保留旧配置。
- 限制：现场20秒低缓冲候选尚未执行，必须当轮确认；缓冲数值不等于实测端到端延迟。候选驻留、音频服务停止。
- 下一责任方：Hardware-A / Codex 完成静默四路径回归，性能收益确认后请求现场准备。

### [PL-20261027-01] Round 3 板端数值/性能与静默管线滞后
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（数值和局部优化），BLOCKED（整链高实时门未通过，非外部权限阻塞）。
- 基准实现：`7269c2a` / 同步`7a0f16b`；改动：`board/world_exp_latency_probe.py`、`report/world_exp_pl_board_round3_20261027.*`、`report/world_exp_paced_latency_{v23,pl}_20261027.json`及本记录。
- 复现：报告内四路径文件与定速管道命令；原始625块计时留存，未录放。
- 量化：PL=模型80000样本逐字节一致，SNR79.0566dB/最大PCM16误差3/1227次零fallback；接口总0.235515s，渲染RTF0.306332；分析RTF0.552814仍为关键路径。
- 滞后：定速文件PS管线p95原v23 115.867ms/PL115.484ms；不含ALSA/codec/模拟链，不能作为物理端到端通过证据，亦未达到100ms。
- 现场：20秒低缓冲只读preflight通过，已发当轮准备确认，尚未执行；当前候选驻留、音频服务停止，恢复镜像可用。
- 下一责任方：Hardware-A / Codex 获得现场准备确认后做短回归；随后针对分析端与参数批次的关键路径继续推进，不能把当前exp功能集成宣称整链完成。

### [PL-20261027-01] 首轮20秒现场：欠载拒绝，恢复停于非音频重绑
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：REJECTED（低缓冲稳定性），BLOCKED（等待现场复位恢复）。
- 基准提交：`8c0095c`；改动：`board/world_exp_switch.py`、`report/world_exp_live20_round1_20261027.{md,json,txt}`、`report/world_exp_restore_stall_20261027.json`及状态追加。
- 授权：操作者明确“准备好了，开始20秒PL实时测试”；仅执行一轮，没有追加录放。
- 复现：报告内20秒WORLD_EXP=pl命令；prefill100ms/period256/capture2048/playback1024/start-delay16000µs、增益4与0.6。
- 量化：子进程全0，0采集overrun/2播放underrun，0原始和输出削顶；PL3177次/0fallback，502参数提交=消费；分析RTF0.266565/渲染0.294135；仅2帧有声，不算持续语音负载。
- 恢复：原厂载荷成功加载，但非音频显示/摄像外设重绑阶段串口失去响应，尚未启动v23。Ctrl-C/换行/BREAK无响应，MCP hw_server无JTAG target；已请操作者复位或重上电，启动分区未改。电脑保留完整证据。
- 修复与限制：恢复脚本延后非音频外设至正常开机，并逐bind写journal；语法检查通过，尚未板测。不宣称原v23已恢复、听感通过或高实时验收。
- 报告：`report/world_exp_live20_round1_20261027.md`与恢复JSON；下一责任方：操作者复位；Hardware-A / Codex 随后核验原v23与PCM状态，补现场听感，再安排后续调度/分析优化。

### [PL-20261027-01] 操作者复位后原v23恢复核验
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（仅基线恢复）。
- 基准提交：`2335923`；修改：`report/world_exp_reboot_recovery_20261027.{md,json}`与三份共享记录追加。
- 操作者确认：“已重启板卡”；本轮仅只读检查，没有发起新的录放。
- 复现：读取fpga_manager、v23 SHA、/proc进程cmdline和PCM status；机器证据见报告JSON。
- 量化：FPGA operating，v23 SHA与基线一致；单组arecord645/runtime646/aplay647，PCM0p/PCM1c均RUNNING，PL测试模块未加载；prefill和ALSA恢复原配置。
- 结论：解除前轮“等待现场复位”的恢复阻塞，原v23现已运行。20秒低缓冲2次欠载的REJECTED不变；无新听感或高实时验收。
- 下一责任方：Hardware-A / Codex 后续分析关键路径/批次调度优化；任何新现场录放须当轮确认。

### [PL-20261027-01] Round 4 ARM实际算子剖析认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：`ed3624a`（按仓库入口要求rebase最新main，原结果报告内旧SHA保留作历史）。
- 当前依据：exp卸载渲染只改善约6.2%，定速PS管线p95约115ms，低缓冲现场2次欠载；不能继续用电脑端profile推断ARM热点。
- 范围：新增可复现ARM算子计时构建/脚本，先测FFT执行、FFT建表和各分析阶段，数值保持原v23；本轮暂不改音色或批次。
- 复现/量化：待本轮报告；原证据`report/world_exp_pl_board_round3_20261027.md`。原v23已由操作者复位恢复，现场录放不在本轮范围。
- 下一责任方：Hardware-A / Codex 根据真实ARM占比选下一个PL模块或移除接口开销；完成静默文件数值对齐和计时后提交PR #16。

### [PL-20261027-01] Round 4 ARM算子剖析方案提交
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED。
- 基准：`ed3624a`；改动：`src/ps/world_operator_profile.cpp`、`build/build_world_exp.ps1`、`report/world_operator_profile_round4_proposal_20261027.md`及本记录。
- 复现：`build_world_exp.ps1 -Target arm -ProfileOperators -WorldRoot <WORLD>`；ARM已编译，板端待测。
- 方法：链接器wrap FFT plan/execute及4个分析API，线程局部计数，按阶段/长度/类型细分；默认生产路径不启用。先比对原v23输出SHA，再使用剖析结果。
- 限制：原厂PL保持，只有文件测试；服务为稳定串口传输暂时停止，完成后恢复。计时有插桩开销，尚无下一算子加速结论。
- 下一责任方：Hardware-A / Codex 执行相同输入对齐与ARM计时，按占比实施下一优化。

### [PL-20261027-01] Round 4 ARM算子结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（诊断数值，非高实时验收）。
- 基准提交：`fccd97b`；改动：`board/world_operator_profile_trial.py`、`report/world_operator_profile_round4_20261027.{md,json}`及本记录。
- 复现：报告内相同5秒文件、三次profile；80000样本与板上原v23逐字节相同，profile墙钟中位2.883378s，相对单次基线2.833727s约+1.75%。
- 量化：FFT执行累计1.454058s，建表0.268492s；D4C2048执行0.324211s，合成1024执行0.654678s，均为线程累计，非墙钟加速比。
- 限制：原厂PL，服务临时停止以便静默文件和串口传输；无录放。未使用电脑端耗时推断ARM，未宣称新的PL或低延迟通过。
- 下一责任方：Hardware-A / Codex 先复用FFT计划，再验证适合double/log谱的PL FFT精度与DMA收益；保持v23声学路径。

### [PL-20261027-01] Round 5 FFT计划复用方案
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED / PROPOSED。
- 基准：`bf748af`；修改：`src/ps/world_fft_plan_cache.cpp`、构建入口、板端runner、`report/world_fft_cache_round5_proposal_20261027.md`与host JSON。
- 复现：构建`-CacheFftPlans`，板端按manifest运行`world_fft_cache_trial.py`。每线程32槽/4MiB，独立工作区；只移除重复建表，不改FFT算术。
- 量化：修复MinGW线程析构生命周期问题后，两段男声20次host文件正常退出、开关逐字节一致；ARM已编译，待静默板测。报告记录开发失败及修复，不把host计时当ARM收益。
- 限制：原厂PL，服务临时停止；无新录放或位流切换，没有高实时结论。
- 下一责任方：Hardware-A / Codex 完成ARM交错回归并发布本轮结果，再评估PL FFT。

### [PL-20261027-01] Round 5 ARM FFT复用结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（数值与文件吞吐，非高实时验收）。
- 基准实现：`35fc480`；改动：`report/world_fft_cache_board_round5_20261027.{md,json}`与恢复JSON、本记录。
- 复现：板端runner两输入×3轮×baseline/cache_off/cache_on；18次退出0，输出与原v23逐字节一致。
- 量化：male1墙钟中位2.901327→2.592240s（-10.65%），male4 2.883022→2.605723s（-9.62%）；分析RTF分别0.572398→0.507131、0.566304→0.508260；总保留工作区约283KiB。male4最大分析批次中位34.499→36.244ms，不能宣称延迟峰值改善。
- 限制与状态：只静默文件，原厂PL；已恢复原v23服务并记录SHA/PCM状态。无新现场听感或高实时结论，FFT还未上PL。
- 下一责任方：Hardware-A / Codex 用Vivado MCP FFT IP位准确模型验证1024/2048浮点精度和吞吐预算，再确定PL接入。

### [PL-20261027-01] Round 6 PL浮点FFT候选认领与方案
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED / PROPOSED。
- 基准：`9b609d4`；改动：`build/create_world_fft_probe.tcl`、`src/ps/world_fft_ip_model.cpp`、构建入口、`report/world_fft_ip_round6_proposal_20261027.md`。
- 复现：独立xfft9.1浮点/25bit twiddle/2048可变长度/100MHz，Vivado MCP已生成官方位准确C模型；host显式FftModelSdk构建成功，尚无本轮语音结果或板测。
- 范围：先验证D4C/分析/合成FFT数值，再看OOC资源和DMA收益；不沿用慢且精度不足的18bit旧核，不改变板卡PL。
- 板卡状态补充：Round5服务start后的首个立即PCM读取closed；异步启动完成后只读复核arecord954/aplay956两PCM均RUNNING，v23 pid918。无新现场测试。
- 限制：官方C模型和OOC都不能替代真实PL数值/实时性；当前未加载FFT候选，未声明高实时验收。
- 下一责任方：Hardware-A / Codex 执行位准确模型回归，数值合格再集成PS/PL。

### [PL-20261027-01] Round 6 浮点FFT位准确模型结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（模型数值门）。
- 基准：`53645ef`；改动：`build/check_world_fft_ip_quality.py`、`report/world_fft_ip_model_round6_20261027.{md,json}`。
- 复现：报告内SDK构建和质量脚本；30独立FFT方向/尺度/切换用例，相对L2最大6.60848722e-08；两受控输入完整WORLD各cpu/d4c/analysis/render/all。
- 量化：全FFT替换SNR男声1 88.876dB、男声4 87.845dB，最大PCM16误差均1；单D4C分别118.306/113.844dB。其余尺寸仍CPU，调用数完整保存。
- 限制：模型数值通过不代表资源、RTL板测或高实时；独立OOC综合进行中，未加载FFT位流、未新录放，板上原v23运行。
- 下一责任方：Hardware-A / Codex 完成FFT流接口、独立DMA和OOC/整机时序，静默板测后才请求现场试听。

### [PL-20261027-01] Round 7 FFT PS/PL集成认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准：`ecb911e`；范围：FFT AXI流配置头、独立HP2 DMA、临时root-only驱动、PS double/float适配；保留exp及音频路径。
- 依据：Round6官方位准确模型两段完整语音SNR≥87.845dB/最大PCM16误差1；独立FFT综合已完成，待读取资源与时序。
- 复现与量化：将随本轮方案报告提交；先仿真流握手、综合实现与时序，再静默板测；不提前宣称FFT板端或高实时通过。
- 限制：当前原v23/原厂PL继续运行，不修改启动分区；任何新现场录放仍需当轮确认。
- 下一责任方：Hardware-A / Codex 完成可复现候选及客观门，再安排现场。

### [PL-20261027-01] 浮点FFT独立综合资源结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（仅OOC综合预算）。
- 基准构建：`ecb911e`所含probe方案，模型实现`53645ef`；改动：`report/world_fft_core_ooc_20261027.json`及资源/时序TXT。
- 复现：Vivado MCP独立probe、open_run world_fft_probe_synth_1、report_utilization/report_timing_summary。
- 量化：7744LUT/12935FF/15.5BRAM/60DSP；100MHz综合WNS+5.043ns、WHS+0.158ns，0 Error/0 Critical Warning/4 Warning。
- 限制：非布局布线签核，不是整机时序或FFT板测；Round7独立HP2 DMA集成正在构建和RTL仿真，板上原v23未切换。
- 下一责任方：Hardware-A / Codex 完成Round7流接口数值/背压仿真与整机布局布线。

### [PL-20261027-01] Round 7 FFT PS/PL集成方案提交
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED。
- 基准：`9092e1f`；改动：FFT流包装、独立HP2 DMA Tcl、临时驱动/ioctl、PS适配/probe、构建和静默板测runner；详见`report/world_fft_integration_round7_proposal_20261027.md`及build JSON。
- 复现：报告内Vivado tclargs fft、ARM CacheFftPlans/FftPl和WSL module构建；ARM/module/probe已编译、BD已validate，RTL仿真与整机综合进行中。
- 合约：每事务64bit配置头+N复数float，输出N复数；1024/2048、forward/inverse未归一化，c2r显式补Hermitian；DMA0x40410000，独立于已有exp。
- 限制：没有加载FFT候选，板上原v23运行；只有模型和OOC资源门通过，整机时序/RTL全部向量/板测尚未完成；不宣称高实时。
- 下一责任方：Hardware-A / Codex 先完成30帧位准确/背压仿真、布局布线，再做静默文件和DMA性能门；现场录放须当轮确认。

### [PL-20261027-01] Round 7 FFT AXI RTL位准确仿真
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（仅RTL仿真）。
- 基准实现：`b551646`；改动：`report/world_fft_stream_round7_20261027.{json,txt}`。
- 复现：质量脚本生成30帧官方模型mem向量，Vivado MCP运行`run_world_fft_sim.tcl`；40960复数float词全64bit一致，含1024→2048→1024、正反向、零/脉冲/常数/随机/弱信号和输入空拍/输出背压。
- 量化：无背压稳态1024帧4293拍（42.93µs）、2048帧8389拍（83.89µs）@100MHz；只含流核，不含PS转换/DMA。整机综合完成，布局布线已启动。
- 限制：未加载FFT候选、尚无FFT板端收益或听感。下一责任方：Hardware-A / Codex 完成整机时序/DRC与静默板测。

### [PL-20261027-01] 临时高速UART尝试拒绝并自动恢复
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：REJECTED（921600串口），ACCEPTED（原基线恢复）。
- 基准：`b551646`；证据：`report/world_uart_baud_recovery_20261027.json`。
- 为缩短位流传输，停v23后临时设置921600；控制台失去响应。标准/高速重连、Ctrl-C和JTAG仅恢复UART寄存器仍未恢复；Windows PnP重启被系统权限拒绝，未执行。
- 本次JTAG已可连接（Digilent210357A7D00EA），通过XSDB系统复位并从未改动启动分区正常boot；串口115200、原v23 SHA匹配、PCM0p/PCM1c RUNNING恢复。
- 处置：撤销未提交的BaudRate参数，上传工具仍固定115200，不重试该加速传输路径。不把具体UART驱动/内核原因写成已定位；事故期间未加载FFT候选，无新现场测试。
- 下一责任方：Hardware-A / Codex 保持115200完成候选传输；继续等待已启动的整机布局布线。

### [PL-20261027-01] Round 7 FFT整机布局布线结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（整机实现门）。
- 基准实现：`b551646`；改动：打包脚本`--fft`、`report/world_fft_implementation_round7_20261027.{md,json}`和4份routed TXT。
- 复现：报告内完整Vivado tclargs fft；Vivado MCP打开impl_1复核完整设计。
- 量化：100MHz WNS+0.302ns/WHS+0.036ns，0失败端点/黑盒/DRC Error，17200LUT/29183FF/24.5BRAM/69DSP；bus skew全MET，位流swap SHA bdb4c0877e9818976dd7d9281a8ccc162018681cdf880bf117d2f55d3af72988。
- 限制：3输入/6输出缺外部IO延时，保留DRC Warning/Advisory。程序已校验传输，位流传输中；服务临时停止，没有FFT板测/听感/高实时结论。
- 下一责任方：Hardware-A / Codex 完成临时加载、128次DMA对照与两段文件全路径回归；任何新的现场录放仍先确认。

### [PL-20261027-01] Round 8 硬件FFT首轮约定检查拒绝
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：REJECTED（PS c2c适配/测试约定）。
- 实现：`b551646`，位流实现证据`a05d00c`；报告：`report/world_fft_board_round8_rejected_20261027.json`。
- 复现：按manifest上传，临时加载已签核SHA位流，insmod两个自有module，运行world_fft_pl_trial.py；probe在复数脉冲用例失败，1024 relativeL2=1.41421356，未进入语音文件测试。
- 原因：WORLD/Ooura c2c包装相对标准DFT隐含共轭输入虚部；PL和模型当前采用标准复数输入。此前语音链c2c输入为实数，模型检查未暴露此差异；30个模型RTL一致结论有效，但不能代替WORLD接口约定测试。
- 修正方向：PS适配/host模型明确共轭c2c输入，probe与原WORLD约定对齐，再完整回归；无需改RTL。r2c/c2r不套用此变更。
- 状态：FPGA候选operating，两临时module已加载、音频服务停止，无新录放或FFT板端验收。下一责任方：Hardware-A / Codex 修正并提交下一方案轮次，随后静默回归。

### [PL-20261027-01] Round 9 复数约定修正方案
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED / PROPOSED。
- 基准：`214be3e`；改动：`src/ps/world_fft_pl.cpp`、`world_fft_ip_model.cpp`、`world_fft_dma_probe.cpp`。
- 修正：仅c2c输入虚部取反以匹配WORLD/Ooura；r2c/c2r、RTL/位流/驱动不变。probe的CPU参考保留原WORLD，PL发送共轭数据，覆盖正反向随机复数及复数脉冲。
- 复现：相同ARM/host构建与完整质量脚本；修正ARM SHA2754d7d04aa874c346e362592f68dbfd88b1d6ad608ccb5d3653755d21e51904，probe SHAaddeeaf3ea941c6a697b5adb88bb26678624e14758b73f227184cb95a96fa059。
- 限制：模型语音相对旧模型仅微小变化，原Round8“c2c输入为实数”应理解为该使用路径实部占主导，不能推断所有虚部严格为零。独立复数用例是必要补充；本轮板端复测尚未执行。候选驻留，服务停止，无录放。
- 下一责任方：Hardware-A / Codex 完成同位流probe及两段语音全路径回归，按真实性能选默认模式。

### [PL-20261027-01] Round 9 修正模型数值回归
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（修正模型）。
- 基准实现：`0e557e7`；改动：`report/world_fft_model_round9_20261027.json`。
- 复现：相同官方C模型checker，30个独立方向/尺度用例及两输入各5种模式；修正c2c输入共轭。
- 量化：男声1全FFT SNR88.881dB、男声4 87.845dB，最大PCM16误差1，全部门通过；模型耗时不作硬件速度结论。
- 限制：修正ARM/probe仍在115200校验传输，尚未执行本轮板测；位流驻留、音频服务停止，无录放。
- 下一责任方：Hardware-A / Codex 同位流重跑DMA probe及两段文件全路径，失败仍独立提交。

### [PL-20261027-01] Round 9 FFT板测：数值通过、逐次DMA性能拒绝
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（数值），REJECTED（FFT卸载性能）。
- 实现：`0e557e7`；报告：`report/world_fft_board_round9_20261027.{md,json}`；复现同runner/manifest、同routed位流。
- 数值：128次硬件FFT最坏relativeL2 5.537e-8；两输入CPU逐字节相同，FFT-only最大PCM16误差1、组合3/2，所有exp零fallback/零削顶。
- 性能：1024 ioctl p50 86.538µs、2048 163.770µs；male1计划复用CPU墙钟2.591575s，fft2048 2.775234、fft_all3.274853s；male4同样退步。2048打包+DMA+解包约0.785s/3279次；全FFT互斥等待约0.73s。
- 结论：数值门通过不能抵消性能退步，不默认启用FFT。下一步先改2048实FFT传输/接口，评估时钟优化；先前6.2%exp收益和PS计划复用是独立已证据成果。
- 状态：候选临时驻留、服务停止，恢复镜像/JTAG可用，无新录放或高实时验收。下一责任方：Hardware-A / Codex 继续实现减少实际接口开销的候选并回归。

### [PL-20261027-01] Round 10 实输入FFT紧凑传输认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准：`098f57b`；范围：只减少r2c的DMA冗余零虚部与共轭半谱；不改FFT核精度/时钟/音色/批次。复杂FFT和c2r仍保留完整协议。
- 依据：Round9数值已通过，但完整N复数TX/RX和PS转换导致性能退步；2048主要用于分析r2c，没有必要从ARM发送全零虚部或回收后半共轭谱。
- 计划：头bit9为real输入、N个float打包为N/2个64bit数据，PL扩展零虚部；只返回N/2+1复数并内部排空其余，防止丢TLAST或下一帧污染。每轮测试仍独立提交。
- 限制：当前候选临时驻留、服务停止，无新录放，未宣布该优化有效；下一责任方Hardware-A / Codex做RTL全格式/背压回归后再板测。

### [PL-20261027-01] Round 10 实输入紧凑协议方案提交
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED。
- 基准：`098f57b`；改动：FFT流包装/ioctl/驱动/PS/probe、向量与TB；报告`report/world_fft_compact_round10_proposal_20261027.md`、build JSON及Round9恢复JSON。
- 复现：完整FFT构建仍tclargs fft；质量脚本生成30旧格式+15compact帧；ARM和module已编译。
- 主要变量：r2c仅传N实float、收N/2+1复数；头bit9，内部正确排空后半谱，complex/c2r格式保持。核精度/100MHz/音色/批次不变，尚未有本轮RTL或性能结果。
- 恢复：Round9后按修复脚本成功静默恢复原厂位流，先卸载两个DMA module，只重绑audio/I2C，未出现前轮显示重绑卡死。当前原厂operating、服务临时停止，无录放。
- 下一责任方：Hardware-A / Codex 完成45帧RTL逐位/背压、整机时序及192次probe和全路径文件，实际加速才保留默认。

### [PL-20261027-01] Round 10 紧凑实FFT RTL数值/背压结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（RTL门）。
- 实现：`bfbc3d0`；证据：`report/world_fft_compact_rtl_round10_20261027.{json,txt}`。
- 复现：30帧原格式+15帧compact mem官方模型对照，Vivado MCP source run_world_fft_sim.tcl；旧格式40960词、compact10255词全部float64打包逐位一致。
- 覆盖：1024→2048→1024，complex正反向与real-forward，零/复数或实数脉冲/常量/随机/弱信号；compact均有输入空拍和输出背压，半谱TLAST/内部排空/下一帧握手通过。
- 限制：仿真拍数不代表ARM到PL收益；整机综合完成，布局布线已启动；板端仍原厂PL、服务暂时停止，compact候选尚未加载，无新录放。
- 下一责任方：Hardware-A / Codex 完成新版routed签核与静默192次probe/两段文件，按性能结果选择默认。

### [PL-20261027-01] Round 10 静默管线滞后入口补充
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED（诊断入口）。
- 基准：`cf28ab1`；改动：`board/world_exp_latency_probe.py`。
- 复现：原定速128样本/8ms文件管道，新增显式binary/fft-mode/label及程序/输入SHA；默认v23/pl行为保持。可在同位流、同输入比较cache_cpu/cache_exp/cache_fft2048，结果不互相覆盖。
- 限制：语法检查通过，入口已校验上传，尚未运行；45帧RTL已过但新版布局布线仍进行中。管线滞后不包括ALSA/codec/模拟/声学，不可作为物理端到端验收。
- 下一责任方：Hardware-A / Codex 新版文件数值/性能门后执行并记录至少625个原始块计时，再决定现场候选。

### [PL-20261027-01] Round 10 紧凑实FFT完整布局布线
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（内部routed门）。
- 源实现：`bfbc3d0`；证据：`report/world_fft_compact_implementation_round10_20261027.json`及4份compact routed TXT。
- 复现：同完整FFT构建、Vivado MCP open_run impl_1，核参数/100MHz不变；17255LUT/29197FF/24.5BRAM/69DSP。
- 量化：WNS+0.283ns/WHS+0.040ns，0失败端点/黑盒/DRC Error，bus skew全MET；swap SHA9a7a45027c087a43ce2a3809945317cd892725a2ac1f891ba3db92f61cfaeee9。
- 限制：外部3输入/6输出延时仍未完全约束，DRC警告/建议保留；位流校验传输中，当前原厂PL/服务停止；尚无compact板端性能结论，无新录放。
- 下一责任方：Hardware-A / Codex 完成192次probe与全路径文件、定速滞后比较，再选择候选模式。

### [PL-20261027-01] Round 10 compact板测：数值通过、整链性能仍拒绝
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（数值/局部开销下降），REJECTED（整链性能）。
- 实现：`bfbc3d0`，签核`17df24f`；证据：`report/world_fft_compact_board_round10_20261027.{md,json}`及load JSON。
- 复现：同runner两输入各7路径；192次probe含compact，最坏relativeL2 5.617e-8；CPU输出逐字节一致、FFT最大误差1、组合3/2，零exp fallback/零削顶。
- 量化：2048接口累计0.784→0.637s（约-18.9%），但male1 cache+exp2.583090s/compact+exp2.626509s，male4 2.566616/2.604988s；仍不能默认FFT。
- 内核状态：热切换出现xlnx_formatter_pcm_remove Bad of_node_put引用告警，后续注册与全部测试成功；完整日志保留，不宣称反复热切安全。后续切换前正常重启恢复驱动状态。
- 限制：候选驻留、服务停止，无新录放或高实时验收；下一责任方Hardware-A / Codex继续静默定速滞后和DMA开销优化，必要时用JTAG/正常重启回原厂。

### [PL-20261027-01] Round 10 静默定速管线滞后结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：REJECTED（100ms实时目标）。
- 基准：`1b8e909`，入口`4513f66`；证据：`report/world_fft_paced_round10_20261027.md`及3份paced原始JSON。
- 复现：world_exp_latency_probe.py，5秒male1，128样本/8ms定速，625块；模式与输入/程序SHA在JSON中，未使用ALSA/录放。
- 量化：baseline p95 117.058676ms；cache+exp 113.992885ms；compact2048+exp 114.187369ms；FFT无显著额外收益。
- 限制：仅软件输入交付到输出到达，排除ALSA/codec/模拟/声学，不能作为物理端到端验收；无新用户听感。候选驻留、服务暂时停止。
- 下一责任方：Hardware-A / Codex继续接口开销优化，客观门后才请求新现场轮次。

### [PL-20261027-01] Round 11 PS浮点适配开销认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准：`1b8e909`；范围：只优化PS float打包/解包有限值检查与实输入循环，不改位流/驱动/精度/批次。
- 依据：compact接口仍有约0.20s prepare/unpack；ARM反汇编显示每bin std::isfinite触发VFP abs/compare/vmrs同步；改按IEEE754指数位聚合检查，仍拒绝Inf/NaN，不放弃校验。
- 复现与量化待本轮报告；先CPU逐字节和同位流PL数值/三次耗时。候选驻留、服务停止，无新录放；下一责任方Hardware-A / Codex。

### [PL-20261027-01] Round 11 浮点适配优化方案
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED。
- 基准：`6193bc8`；范围：src/ps/world_fft_pl.cpp、board/world_fft_adapter_trial.py；报告 world_fft_adapter_round11_proposal_20261027.md。
- 复现：ARM CacheFftPlans/FftPl构建已成功；binary SHA 2b9d98466955262f68462e78256fb5f8e192bc9fecb265d666f3910e80807d65。
- 变量：逐bin VFP isfinite改IEEE754指数掩码聚合，仍拒绝Inf/NaN；r2c单独打包循环；不改DMA、核/位流、音色或批次。
- 限制：无本轮板端性能结果；当前compact候选驻留、服务停止，无新录放。
- 下一责任方：Hardware-A / Codex同位流/旧程序交错三次、两输入三模式逐字节回归，结果独立提交。

### [PL-20261027-01] Round 11 适配对照：数值保持、FFT默认仍拒绝
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：ACCEPTED（数值保持），REJECTED（默认FFT性能）。
- 实现979fb89；报告report/world_fft_adapter_round11_20261027.{md,json}；同位流旧新两输入三模式各三遍，共36次，全部逐字节一致/零exp fallback。
- 量化：combined墙钟中位2.645587→2.621563s及2.658425→2.608862s；新exp_only为2.602989/2.605818s，FFT仍无可靠净收益；DMA约0.436s/3279次。
- 限制：无ALSA/新录放；候选驻留、服务停止，未过高实时门；下一责任方Hardware-A / Codex分解内核复制和DMA耗时，再优化实际瓶颈。

### [PL-20261027-01] Round 12 FFT内核阶段计时认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准8ee3902；范围src/kernel/world_fft_dma.c与小型证据，不改RTL/位流/算法；新增默认关闭的只读诊断计数。
- 依据：Round11打包节省不足，约0.436s/3279次仍在ioctl；必须区分内核复制和设备等待，再选择200MHz或接口融合方向。
- 复现：匹配5.15.0-xilinx module构建；同位流停用旧module、载入profile=1候选，probe/文件数值与关闭计时对照；量化待报告。
- 限制：静默诊断，无ALSA/新现场；服务停止、compact位流驻留。下一责任方Hardware-A / Codex。

### [PL-20261027-01] Round12 计时方案提交
- 日期：2026-10-27；Hardware-A / Codex；PROPOSED；基准8ee3902。
- 改动src/kernel/world_fft_dma.c；复现与边界见report/world_fft_kernel_profile_round12_proposal_20261027.md；module构建通过，SHA a882bc0bf3cadf7a6a89ceba3b640bd99b329db6be8eb75fe2e0a29dc1df447f。
- 量化：尚无阶段板测；默认profile=0无额外时钟，profile=1按copy_in/device/copy_out累计，stats只读。内核已有bufferable映射，不盲改WRITE_COMBINE。
- 限制：只静默诊断，候选驻留、服务停止，无ALSA/新录放；下一责任方Hardware-A / Codex完成开关对照，随后按用户方向转向阶段融合卸载。

### [PL-20261027-01] Round12 内核阶段计时通过，转向完整计算阶段融合
- 日期：2026-10-27；Hardware-A / Codex；ACCEPTED（诊断）；驱动198565e。
- 报告report/world_fft_kernel_profile_round12_20261027.{md,json}；runner board/world_fft_kernel_profile_trial.py；开关三遍两输入12次逐字节相同，两组各192次probe通过。
- 量化male1：3279调用，copy_in28.288ms/device263.459ms/copy_out132.327ms；约31%内核开销为结果复制。开启与关闭中位墙钟2.631122/2.637466秒，无显著插桩扰动。
- 用户新指令：能放PL就放PL，能全放更好；后续以WORLD分析/映射/合成完整计算阶段为迁移目标，PS先保留音频I/O与控制，避免逐算子往返。当前核资源余量不等于整链已能容纳，需HLS/RTL资源实测。
- 限制：结束profile=0；服务停止、compact候选驻留，无新录放/高实时结论；下一责任方Hardware-A / Codex检查HLS工具并认领融合实现。

### [PL-20261027-01] Round13 WORLD整链PL融合方案认领与提案
- 日期：2026-10-27；Hardware-A / Codex；状态：CLAIMED / PROPOSED；基准9eb5509。
- 用户明确要求能放PL就放PL，能全放更好。Round12显示逐FFT ioctl中回读约31%、设备事务约62%，故切换帧级融合，不再把单FFT加速当主路径。
- 提案报告：`report/world_full_pl_migration_round13_proposal_20261027.md`。分层范围：4帧前端谱→D4C批处理→合成状态→单事务融合DMA；PS保留音频I/O与控制。
- 量化门：逐层与v23 PCM16最大误差≤3、SNR≥75dB、零fallback/零削顶；每层独立HLS/RTL/资源/时序门。当前只是架构提案，无板测/试听/高实时结论。
- 下一责任方：Hardware-A / Codex 编写第一阶段frame frontend golden/HLS C-sim，随后Vivado MCP综合资源评估。

### [PL-20261027-01] Round13 最小相位融合原型方案
- 日期2026-10-27；Hardware-A / Codex；PROPOSED；基准622fbd8。
- 源码src/hls/world_minphase.cpp、host wrapper、build MinphaseModel开关、HLS tcl与24例单元；报告report/world_minphase_fused_round13_proposal_20261027.md。
- 范围：镜像log谱→两FFT→倒谱→复数指数在一个PL核；只输入谱/输出最终滤波器，减少往返；尚非完整D4C/合成。
- 复现：报告内MinphaseModel和vitis-run命令；初步host/HLS结果已产生，将独立结果提交。默认CPU不变，无新录放。
- 修正方案：随机激励必须原WORLD算法/种子/消费顺序，不能LFSR替代；STFT不能直接当CheapTrick，D4C内部FFT尺寸按原公式。
- 下一责任方Hardware-A / Codex提交完整结果，资源/周期不达标则先优化HLS，禁止提前板测通过。

### [PL-20261027-01] Round13 融合核数值通过、首版周期拒绝
- 日期2026-10-27；Hardware-A / Codex；ACCEPTED（host数值），REJECTED（首版周期）；实现2c2e2d0。
- 报告report/world_minphase_fused_round13_20261027.md、host JSON和两份HLS原始TXT；24例最大relativeL2 9.2324e-7，完整两输入PCM16最大误差1/SNR96.237及96.601dB。
- HLS RTL已生成，估算18150LUT/11213FF/3 BRAM36K/81DSP，但动态FFT循环顶层周期未知，不能直接板测或宣称加速。
- 限制：无RTL cosim/routed/板测/新听感；candidate驻留、服务停止。下一责任方Hardware-A / Codex固定循环/ROM及指数流水，逐轮提交结果。

### [PL-20261027-01] Round14 固定循环融合核优化认领
- 日期2026-10-27；Hardware-A / Codex；CLAIMED；基准49627af。
- 范围最小相位HLS：1024点固定bit reversal、每级512蝶形、float32旋转因子ROM、输出exp/sin/cos流水；不改输入/输出/算法约定。
- 依据Round13数值通过但动态循环周期未知；本轮先确定周期资源，再决定是否使用官方FFT IP替代自定义蝶形。报告与数值待本轮结果。
- 限制无新录放/板测，候选驻留、服务停止；下一责任方Hardware-A / Codex。

### [PL-20261027-01] Round14 固定周期融合核方案
- 日期2026-10-27；Hardware-A / Codex；PROPOSED；基准49627af。
- 固定每级512蝶形、预计算ROM、固定bit反转、exp输出流水；源码及生成/质量脚本见report/world_minphase_round14_proposal_20261027.md。
- 24例host最大relativeL2 8.5944e-7；完整语音/HLS进行中，后续独立结果提交；同级无地址重叠依赖声明必须RTL cosim验证。
- 限制无RTL/板测/新录放；当前compact候选驻留、服务停止；下一责任方Hardware-A / Codex完成周期/资源与数值门。

### [PL-20261027-01] Round14 host通过，HLS估算改善但待RTL门
- 日期2026-10-27；Hardware-A / Codex；ACCEPTED（host/资源估算）；实现bfb9327。
- 报告report/world_minphase_fused_round14_20261027.md、host JSON及两份HLS TXT；24例最大relativeL2 8.5944e-7，两输入PCM16误差1/SNR97.268及96.811dB。
- 量化HLS：9972LUT/7734FF/4BRAM36K/38DSP，29813拍@100MHz（估算298.13µs），非routed/实际DDR。
- 风险：工具flatten级循环，inter false约束必须禁止跨级重叠后RTL cosim；exp目标II=1未完全满足，不宣称RTL通过。
- 下一责任方Hardware-A / Codex明确LOOP_FLATTEN off并完成cosim，之后才考虑整机融合；无新录放。

### [PL-20261027-01] Round15 FFT级间依赖与RTL验证认领
- 日期2026-10-27；Hardware-A / Codex；CLAIMED / PROPOSED；基准e6d1306。
- src/hls/world_minphase.cpp明确LOOP_FLATTEN off；build/cosim_world_minphase_hls.tcl用原WORLD common/fft/matlabfunctions做24例C/RTL对照，HLS重综合后cosim。
- 目标同级蝶形并行但级间完整排空，消除Round14 flatten与inter false组合的风险；结果待生成，不预设通过。
- 限制无新板测或录放；candidate驻留/服务停止。下一责任方Hardware-A / Codex读取cosim/周期资源并独立提交。

### [PL-20261027-01] Round15 C-sim通过，RTL因Windows长路径失败；基线已恢复
- 日期2026-10-27；Hardware-A / Codex；ACCEPTED（C-sim/恢复），BLOCKED（本轮cosim工具路径）；实现e98e787。
- 报告report/world_minphase_cosim_round15_20261027.md及工具TXT/restore JSON；24例relativeL2最大8.5944e-7，HLS30229拍/10007LUT/38DSP，RTL未执行。
- 失败：浮点IP生成完整路径超过Windows260字符，非RTL数值失败；入口include引号已修正，下一轮用D盘短生成目录。
- 恢复：stop/rmmod/sync/正常reboot，原厂bit与v23 SHA匹配，FPGA operating、PCM双RUNNING、内核Not tainted、自有模块卸载。启动分区未改，无新录放。
- 下一责任方Hardware-A / Codex短路径重跑HLS/RTL并继续融合迁移。

### [PL-20261027-01] Round16 短路径HLS工具修复认领
- 日期2026-10-27；Hardware-A / Codex；CLAIMED / PROPOSED；基准3ddb50d。
- 修改两HLS入口支持WORLD_HLS_PROJECT；probe只接受新目录防覆盖历史。生成工程D:/wpl_20261027_r16/m，源码留仓库，避开260字符限制。
- 复现：设置WORLD_HLS_PROJECT后vitis-run依次probe/cosim；算法/RTL约束不变。结果待本轮报告。
- 限制：板端已恢复原厂v23运行，不再切板；无新录放；下一责任方Hardware-A / Codex验证工具修复及RTL数值。

### [PL-20261027-01] 2026-10-27 当日停止与交接
- 角色Hardware-A / Codex；状态暂停（用户“今天先到这里”）。Round16短路径综合/C-sim通过，RTL进入编译/展开但未完成，相关HLS/xelab进程已停止，未写RTL通过。
- 证据report/world_minphase_round16_paused_20261027.md及synth/cosim TXT；交接handoff_20261027_PL.md。原厂位流/v23已恢复、双PCM RUNNING，临时驱动卸载，启动分区未改，无新录放。
- 用户方向：尽量把WORLD分析/映射/合成迁入PL，PS保留I/O控制；首个最小相位融合核host两输入误差1/SNR约97dB，HLS估算38DSP/约1万LUT，尚待RTL/整机/板测。
- 下一责任方Hardware-A / Codex：用户下次要求继续后，先完成24例RTL cosim，再评估整机/板端收益。不得把估算当高实时验收。

### [PL-20261027-01] Round16 短路径 RTL cosim 恢复认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED；基准提交：`fe556e66fd5bd1a3feb0a34fbd3db2e8cb29a045`。
- 用户要求继续 WORLD v23 PL 迁移直到可用；本轮先恢复 `D:/wpl_20261027_r16/m` 的 24 例 Verilog cosim，关闭前不把 HLS 估算或未完成日志写成 RTL 通过。
- 协作边界：根工作区存在他人未提交改动，继续只使用独立工作树 `tmp/world_v23_pl_worktree`；板卡保持原厂 bit/v23，不进行录音、播放或试听。
- 成功门：24/24 RTL 输出与同一 WORLD golden 对照通过，并记录工具版本、周期与误差；通过后再评估整机资源/时序和静默板端收益。
- 下一责任方：Hardware-A / Codex 完成本轮 cosim、证据、提交和 PR 更新。

### [PL-20261027-01] Round16 短路径 RTL cosim 结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：ACCEPTED（仅 RTL cosim 门）；基准提交：`fe556e66fd5bd1a3feb0a34fbd3db2e8cb29a045`。
- 复现：设置 `WORLD_HLS_PROJECT=D:/wpl_20261027_r16/m`，运行报告中的 Vitis HLS 2026.1 命令；WORLD 0.3.5 golden 源来自根工作区忽略目录，源码与报告 SHA 见 JSON。
- 量化：24/24 Verilog RTL 用例通过，RTL 后检查最大 relative L2 `8.53141669198e-7`；延迟 `32231..32232` 拍，事务间隔 `32245..32246` 拍。HLS 估算 `10007 LUT / 7732 FF / 8 BRAM18K / 38 DSP`，尚非 routed。
- 风险：XSIM 对显式 `inter false` 依赖提示记录 6720 条动态地址冲突警告；24 例数值通过但警告保留，不能据此宣称整机时序或板端通过。
- 报告：`report/world_minphase_cosim_round16_20261029.{md,json,txt}`。本轮无板卡切换、录音、播放或试听。
- 下一责任方：Hardware-A / Codex 独立提交本轮后执行 OOC 实现与时序/资源门；通过后再设计整机 DMA 接入。

### [PL-20261027-01] Round17 最小相位融合核 OOC 实现认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED；基准提交：`12d2389`。
- 唯一变量：对 Round16 已通过 24/24 RTL cosim 的同一 HLS RTL 执行 Vivado OOC synthesis/implementation；不改算法、接口、时钟目标或测试向量。
- 成功门：`xc7z020clg400-2`、100 MHz 下 routed WNS/WHS 均非负，无 black box 或 DRC Error，并记录实际 LUT/FF/BRAM/DSP；HLS 估算不能替代 routed 结果。
- 限制：OOC 只证明核级可实现，不代表加入现有音频系统后仍收敛；本轮不加载位流、不操作板卡、不录放或试听。
- 下一责任方：Hardware-A / Codex 运行短路径 OOC 实现并独立提交成功或失败证据。

### [PL-20261027-01] Round17 最小相位融合核 OOC 实现结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：ACCEPTED（仅核级 OOC 门）；基准提交：`12d23894d308be30b44fd73292bed34cd0c18a8c`。
- 复现：设置 `WORLD_HLS_PROJECT=D:/wpl_20261027_r16/m`，运行 `vitis-run --mode hls --tcl --input_file build/impl_world_minphase_hls.tcl`；Vitis HLS/Vivado 2026.1，器件 `xc7z020clg400-2`，100 MHz。
- 量化：完成布线，WNS `+1.327 ns`、WHS `+0.053 ns`，setup/hold 失败端点均 0，未布线网络 0；实际 `4996 LUT / 5769 FF / 38 DSP / 7 BRAM18K`，black box 0、DRC Error 0。
- 限制：OOC 边界缺少顶层 `HD.CLK_SRC/HD.PARTPIN_LOCS`，且 Vivado 提示不会执行全部连接型 DRC；94 项 Warning 主要为 DSP 流水建议及 OOC `RTSTAT-10/ZPS7-1`。不宣称整机时序或板端通过。
- 报告：`report/world_minphase_ooc_round17_20261029.{md,json,txt}`；本轮未加载位流，未录音、播放或试听。
- 下一责任方：Hardware-A / Codex 接入现有 Zynq 音频设计并完成整机 address/DRC/资源/时序门，通过后再进行可恢复的静默板端向量测试。

### [PL-20261027-01] Round18 最小相位融合核整机接入认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED / PROPOSED；基准提交：`7065a2f`。
- 唯一变量：把 Round17 导出的 `xilinx.com:hls:world_minphase:1.0` 接入现有完整音频工程；保留音频 HP0 和现有 WORLD exp HP1，新增核的两个 AXI master 独占 HP2，两个 AXI-Lite 从口接 GP0 控制互联。
- 地址计划：ap_ctrl `0x43C70000`、指针参数 `0x43C80000`；输入/输出 DDR 视图均为 HP2 `0x00000000..0x3fffffff`。中断暂接 F2P bit14，首轮驱动仍采用有界轮询。
- 成功门：BD validate 通过且地址无重叠；随后完整综合/布局布线满足 WNS/WHS 非负、0 未布线、0 DRC Error，并记录整机资源。任何失败也独立提交，不覆盖历史工程。
- 限制：本轮只生成新的 `build/generated/world_minphase_20261029` 工程，不加载位流、不操作板卡、不录放或试听；导出 IP 由 `WORLD_MINPHASE_IP_REPO` 显式指定，避免把大生成物提交 Git。
- 下一责任方：Hardware-A / Codex 完成整机 validate/implementation 与证据。

### [PL-20261027-01] Round18 最小相位融合核整机实现结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：ACCEPTED（整机静态实现门）；基准提交：`7065a2f`。
- 接入：ap_ctrl `0x43C70000`、指针参数 `0x43C80000`，输入/输出 AXI master 经新互联独占 HP2；音频 HP0、既有 WORLD-exp HP1 不变。F2P bit14 保留中断，首轮驱动计划有界轮询。
- 量化：完整 routed WNS `+0.856 ns`、WHS `+0.029 ns`，setup/hold/pulse-width 失败端点 0，32,065/32,065 可路由网络完成；black box 0、DRC Error 0。整机 `13910 LUT / 20145 FF / 9.5 BRAM Tile / 47 DSP`。
- 风险：DRC 仍有 131 Warning/38 Advisory；现有音频约束仍缺 3 输入和 6 输出 I/O delay。首次长路径工程因 Windows 260 字符失败，同设计在 `D:/wpl_20261029_full/m` 通过；不能宣称外部接口完整 signoff。
- 报告：`report/world_minphase_integration_round18_20261029.{md,json,txt}`；候选 bit/bin/DCP SHA 见 JSON，生成物未入 Git。本轮未加载板卡、未录放或试听。
- 下一责任方：Hardware-A / Codex 生成 Linux 换序载荷，实现 coherent-buffer/超时轮询驱动和 WORLD 包装，再执行可恢复的静默板端向量测试。

### [PL-20261027-01] Round19 最小相位板端软件闭环认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED / PROPOSED；基准提交：`4c13edd`。
- 唯一变量：为 Round18 位流增加 Linux FPGA Manager 换序打包、`/dev/world_minphase` coherent-buffer 驱动、`GetMinimumPhaseSpectrum` ARM 包装和 24 例静默 DMA 探针；不改 HLS 算法或整机连接。
- 驱动契约：513 float32 输入、513+513 float32 输出；控制/参数基址 `0x43C70000/0x43C80000`，物理缓冲经 HP2，20 ms 有界轮询，超时后拒绝继续静默回退。
- 成功门：ARM 静态程序和匹配 5.15.0-xilinx module 构建通过；载荷换序/哈希可复现；主机编译与 ioctl ABI 检查通过。独立提交后才临时加载板卡做 24 例静默向量并验证恢复。
- 限制：本轮软件构建不加载板卡、不录放或试听；板端阶段也只做文件/向量，启动分区不修改。
- 下一责任方：Hardware-A / Codex 完成构建、证据与提交。

### [PL-20261027-01] Round19 最小相位板端软件闭环结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：ACCEPTED（仅软件构建门）；基准提交：`4c13edd`。
- 交付：确定性 FPGA Manager 换序/gzip 打包、`/dev/world_minphase` coherent DMA 模块、WORLD `GetMinimumPhaseSpectrum` 包装和 24 例静默探针；控制/参数基址 `0x43C70000/0x43C80000`，20 ms 超时后锁存失败，不静默回退。
- 构建：ARM 静态主程序/探针通过；模块 vermagic `5.15.0-xilinx SMP preempt mod_unload modversions ARMv7 p2v8`。换序 bin SHA `1bc4b3f8...29373`，确定性 gzip SHA `6a7fec99...8d98`，连续两次一致；其余哈希见 JSON。
- 报告：`report/world_minphase_board_software_round19_20261029.{md,json,txt}`。本轮未加载板卡，不能宣称板端数值、RTF 或音质通过；未录放、试听或修改启动分区。
- 下一责任方：Hardware-A / Codex 独立提交后执行可恢复的 24 例静默板测及文件转换对照，最后恢复并核对原厂 bit/v23、PCM、服务和内核状态。

### [PL-20261027-01] Round20 最小相位静默板端验证认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED；基准提交：`05d9c3a`。
- 唯一变量：临时加载 Round18/19 candidate，插入匹配模块并运行 24 例静默数值探针；通过后再做既有 male1/male4 文件转换对照。启动分区、原 v23 和真人音频不改。
- 前置门：先只读核对 COM4 上原厂 bit/v23 SHA、FPGA operating、双 PCM/服务、内核 taint 和自有模块；传输逐件 SHA。实际切换前遵守恢复脚本的当轮准备确认要求。
- 成功门：24/24 ioctl 通过、relative-L2 不超过 `2e-5`、无超时；模块计数与耗时有效；文件输出满足 SNR/峰值误差和零 fallback；最后恢复原厂 bit/v23 并核对 PCM、服务、模块、taint。
- 限制：全程静默，不录音、播放或试听；任何失败也独立提交，不能把构建或 host/RTL 结果当板端通过。
- 下一责任方：Hardware-A / Codex 完成只读预检和传输；切换门满足后执行并记录测试/恢复。

### [PL-20261027-01] Round20 最小相位静默板端验证结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：ACCEPTED（静默向量与文件门）；基准提交：`05d9c3a`。
- 板端向量：24/24 通过，最坏 relative-L2 `8.53141669193e-7`，device 平均约 `383.2 us/call`，无超时。两段 v23 文件 minphase PL SNR `97.371/96.942 dB`、最大 PCM16 误差均 1、零 fallback；新程序 CPU 与原 v23 逐字节一致。
- 性能：单次文件样本 CPU `2.845/2.823 s`、minphase PL `2.749/2.747 s`，仅为方向性证据。minphase+exp 请求与 minphase-only 逐字节一致且旧 exp calls=0，证明融合核已包含该阶段 exp/cos/sin，不应继续叠加旧逐算子路径。
- 报告：`report/world_minphase_board_round20_20261029.{md,json,txt}` 和完整遥测 `report/world_minphase_file_result_round20_20261029.json`。首次旧 exp stats 缺失与组合调用假设错误均在报告保留，最终 v3 全部通过。
- 恢复：两模块卸载后 `sync`/正常 reboot；原厂 bit/v23 SHA 匹配，FPGA operating、服务与双 PCM RUNNING、自有模块无、taint 0、临时目录清除。启动仍报既有 FAT 未正确卸载警告，本轮未写启动分区，建议维护窗口离线 fsck。
- 限制：本轮未录音、播放、试听、长稳或物理延迟测试；只接受文件使用门，不能写真人实时通过或完整 WORLD 全 PL。
- 下一责任方：Hardware-A / Codex 在操作者再次确认准备后，以 minphase PL 为唯一新增变量做有限时真实录放、听感和稳定性回归。

### [PL-20261027-01] Round21 最小相位 PL 实时监督准备认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED / PROPOSED；基准提交：`a7ea7bf`。
- 唯一变量：在已验证的 v23/200 ms/fifo_io/既有增益配置上启用 `WORLD_MINPHASE=pl`、保持 `WORLD_EXP=cpu`；监督器增加 fused backend calls/fallback 强校验和结果保存，不改变算法、mixer 或 ALSA 参数。
- 计划：先上传并逐件校验候选、模块、v24 命名程序、监督器和恢复镜像；实际切换与 20 秒真人录放必须取得新的当轮准备确认。成功门为有声、零 xrun/ALSA error/输入触顶/输出削顶、PL calls>0/fallback=0、mixer 恢复和 PCM closed。
- 限制：20 秒只作为首轮实时门，不能替代 60 秒/10 分钟/30 分钟稳定性或定量物理延迟；听感由当次操作者原话记录。
- 下一责任方：Hardware-A / Codex 完成静态预部署后请求操作者准备确认。

### [PL-20261027-01] Round21 最小相位 PL 首轮实时结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：REJECTED（可听性）；基准提交：`a7ea7bf`。
- 条件：操作者重新确认准备；20 秒/200 ms/fifo_io，既有增益与 ALSA 参数，`WORLD_MINPHASE=pl`、`WORLD_EXP=cpu`。监督器新增 minphase calls/fallback 强校验。
- 客观：子进程全 0，录放 xrun/ALSA error/输入触顶/输出削顶均 0；PL `2725 calls / 0 fallback`，output peak `0.197959`，分析/渲染 RTF `0.272714/0.277273`，最大分析 `24.116 ms`，但只有 30 有声帧。
- 用户原话：**“没听到声音”**。据此本轮硬判 REJECTED；数字链非零和零 xrun 不得覆盖用户听感。报告 `report/world_minphase_live20_round21_20261029.{md,json,txt}`，完整监督结果 `report/world_minphase_live20_result_round21_20261029.json`。
- 恢复：结果下载后模块卸载、sync、正常 reboot；原厂 bit/v23 SHA 匹配，FPGA operating、服务和双 PCM RUNNING、taint 0、自有模块无、临时目录清除。恢复后只读 codec 显示左右 DAC/PGA/HP On；不能倒推候选运行态。
- 限制与下一步：候选 active codec/DAPM 快照未在 reboot 前下载，尚未定位数字输出到模拟可听链的断点。不得直接重复 WORLD；下一次准备确认后依次做原厂参考播放、candidate 同参考播放，均可听才重跑短时 WORLD。

### [PL-20261027-01] Round22 录入提示音与准备窗口修正认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED / PROPOSED；基准提交：`f98ccc8`。
- 用户补充原话：**“因为刚刚录入的时候我没有准备好，你录入之前先给个提示音”**。因此 Round21 的“没听到声音”保留为原始反馈，但测试条件被操作者澄清为未及时准备，不能据此归因候选算法或模拟链故障。
- 修正：监督器在 mixer 配置后、启动 arecord 前播放两段上升提示音（880/1175 Hz，各 300 ms，中间 180 ms），随后固定 2 秒静默准备窗口；提示使用与正式播放相同的 32 kHz/S24_LE/双声道路径，失败即不开始录入。
- 成功门：先由操作者确认提示音可闻并按提示讲话；正式 20 秒仍要求有声、零 xrun/error/触顶/削顶、PL calls>0/fallback=0，并记录提示音 exit/帧数/准备间隔。正式测试前仍需新的准备确认。
- 下一责任方：Hardware-A / Codex 完成静态检查、独立提交和部署后请求操作者准备。

### [PL-20261027-01] Round22 录入提示音与准备窗口修正结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：PROPOSED / WAIT_LOCAL_TEST；基准提交：`f98ccc8`。
- 实现：`--prompt-tone` 在 arecord 前播放 880/1175 Hz 各 300 ms 的上升双音，中间 180 ms，32 kHz/S24_LE/双声道/12%峰值；提示后 `--ready-delay-s 2` 再开始录入，提示失败则不录入。
- 检查：Python 编译、mock aplay 24960 帧/peak0.12/delay2.0 和 `git diff --check` 通过；监督器 SHA `cecf23ad...8b69f`。报告 `report/world_minphase_prompt_round22_20261029.{md,json,txt}`。
- 限制：本轮未加载板卡或录放；Round21 原反馈与日志保留，但根据用户“录入的时候没有准备好”的补充，不作为候选可听性归因结论。
- 下一责任方：Hardware-A / Codex 独立提交后部署；新的操作者准备确认后先验提示音可闻，再进行一次 20 秒实时测试。

### [PL-20261027-01] Round23 提示音后实时复测认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED；基准提交：`9515715`。
- 操作者已明确“准备好了”。本轮复用 Round21 相同 candidate、程序、模块、200 ms/fifo_io/增益/ALSA 参数，唯一测试流程变化是录入前双提示音和 2 秒准备窗口。
- 成功门：提示音由操作者确认可闻；其后 20 秒讲话有声、零 xrun/error/触顶/削顶、PL calls>0/fallback=0，用户确认转换声音可听并评价连续性/异常；结束后恢复原厂 bit/v23。
- 限制：单次 20 秒不替代长稳或定量延迟；任何主观失败优先于客观日志。
- 下一责任方：Hardware-A / Codex 执行预检、提示音实时测试、证据下载与恢复。

### [PL-20261027-01] Round23 提示音后实时复测结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：ACCEPTED（20 秒实时可用门）；基准提交：`9515715`。
- 条件：双提示音 exit0/24960帧，随后2秒准备；20秒/200ms/fifo_io，`WORLD_MINPHASE=pl`、`WORLD_EXP=cpu`，其余参数与Round21相同。
- 客观：有声帧1079，子进程全0，录放xrun/ALSA error/输入触顶/输出削顶均0；PL `4857 calls / 0 fallback`，分析/渲染RTF `0.561150/0.310517`，最大分析 `34.605 ms`。candidate active MICB/ADC/DAC/PGA/HP均On。
- 用户原话：**“讲话时能听到转换声音，效果和ps类似”**。据此接受有限时实时可用和主观与PS相近；用户未单独评价提示音，不补写提示音听感。
- 报告：`report/world_minphase_prompt_live_round23_20261029.{md,json,txt}`；完整结果与active codec分别为`world_minphase_prompt_live20_result_round23_20261029.json`和`world_minphase_prompt_codec_active_round23_20261029.json`。
- 恢复：结果下载后模块卸载、sync、正常reboot；原厂bit/v23 SHA匹配，FPGA operating、服务和双PCM RUNNING、自有模块无、taint0、临时目录清除。
- 限制：单次20秒不替代60秒/10分钟/30分钟稳定性或物理延迟；只迁移融合最小相位阶段，并非完整WORLD全PL。下一责任方Hardware-A / Codex在新准备确认后执行同参数60秒提示音稳定性门。

### [PL-20261027-01] Round24 60 秒提示音稳定性认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED；基准提交：`e0b518e`；操作者明确“开始吧”。
- 唯一变量：复用 Round23 完全相同 candidate、程序、模块、提示音、200 ms/fifo_io、增益和 ALSA 参数，只把正式录入从 20 秒延长到 60 秒。
- 成功门：提示后有效持续讲话，零录放 xrun/ALSA error/输入触顶/输出削顶，PL calls>0/fallback=0，用户确认可听连续；保存 active codec 与结果并恢复原厂 bit/v23。
- 限制：60 秒仍不替代 10/30 分钟长稳或定量物理延迟；失败不自动重跑。
- 下一责任方：Hardware-A / Codex 部署并执行本轮测试。

### [PL-20261027-01] Round24 60 秒提示音稳定性结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：REJECTED（无有效语音，测试条件无效）；基准提交：`e0b518e`。
- 操作者原话：**“60s录入我没有准备好”**。因此本轮不能用于 60 秒真人稳定性验收，也不能把失败归因于 PL、VAD、麦克风或音频链；Round23 的 20 秒实时可用结论不变。
- 客观：提示音 exit0/24960帧/后置2秒；子进程全0，录放 xrun/ALSA error/输入触顶/输出削顶均0；PL `7883 calls / 0 fallback`，但有声帧0，监督器按 `--require-voiced` 退出1。raw peak `0.423708`、RMS `0.027869`，分析/渲染RTF `0.283794/0.278869`。
- 运行态：candidate active MICB/ADC/DAC/PGA/HP均On；驱动 device 累计`3.055748 s`、约`387.64 us/call`。报告：`report/world_minphase_prompt_live60_round24_20261029.{md,json,txt}`；完整结果与active codec已保存。
- 恢复：module卸载、sync、正常reboot；原厂bit/v23 SHA匹配，FPGA operating、服务和双PCM RUNNING、自有模块无、taint0、临时目录清除。既有FAT警告仍在，本轮未写启动分区。
- 下一责任方：Hardware-A / Codex 等待新的操作者准备确认后，使用完全相同参数重做60秒；提示后需在整个录入窗口持续讲话，失败不自动重跑。

### [PL-20261027-01] Round25 60 秒有效讲话稳定性复测认领
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：CLAIMED；基准提交：`d85bee6`；操作者明确“准备好了”。
- 唯一变量：复用 Round24 完全相同 candidate、程序、module、提示音、200 ms/fifo_io、增益和 ALSA 参数，重新执行60秒；本轮操作者将在提示后持续讲话。
- 成功门：有声帧>0，零录放 xrun/ALSA error/输入触顶/输出削顶，PL calls>0/fallback=0；保存结果与active codec，取得用户听感后恢复原厂bit/v23。
- 限制：60秒不替代10/30分钟长稳和定量物理延迟；任何失败仍单独提交，不自动重跑。
- 下一责任方：Hardware-A / Codex 部署、执行、取证并恢复。

### [PL-20261027-01] Round25 60 秒有效讲话稳定性复测结果
- 日期：2026-10-29；角色：Hardware-A / Codex；状态：REJECTED（提示音不可闻且客观门失败）；基准提交：`d85bee6`。
- 用户原话：**“我刚刚没有听到提示音”**。提示进程虽报告exit0/24960帧，但操作者没有听见，正式录入起点不可判定；不得把进程成功写成提示可闻。
- 客观：60秒采集/播放各960000样本、零xrun，PL `8803 calls / 0 fallback`；但子进程`0/6/0`、有声帧0、输出peak `2.423787`且削顶133样本，监督器exit1。本轮不能作为60秒有效讲话稳定性验收。
- 报告：`report/world_minphase_prompt_live60_round25_20261029.{md,json,txt}`；完整结果与active codec已保存。candidate active MICB/ADC/DAC/PGA/HP均On；驱动device约`386.25 us/call`。
- 恢复：module卸载、sync、正常reboot；原厂bit/v23 SHA匹配，FPGA operating、服务running，双PCM在随后复核均RUNNING，自有模块无、taint0、临时目录清除。
- 下一责任方：Hardware-A / Codex 先增加codec静音预热、更长更响三段提示和`--prompt-only`验证模式；取得新的播放准备确认并由用户明确确认可闻后，才再次申请60秒录入。
