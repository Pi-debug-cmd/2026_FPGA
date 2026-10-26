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

### [PS-20261025-20] Remote-PS-C HuBERT→目标 FARGAN 电脑端上限认领
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：CLAIMED（正在恢复可复现资产；尚未运行训练或音质评估）
- 基准提交：`ba48816b449a256bc5a331476999831b3ee444f6`（已执行 `git pull --rebase origin main`；任务分支 `agent/ymheee/PS-20261025-20`）
- 本轮目标：仅评估 HuBERT teacher→目标 FARGAN 电脑端质量上限；使用项目固定 HuBERT Base（期望 SHA-256 `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`）、批准的 Fixed-Male 1–5 和女声 Track 5–9，不改变切分或五项门槛。
- 修改路径：`coummucation.md`（本认领记录）。
- 复现命令：待固定版本资产校验和运行环境准备后补充。
- 量化结果：尚未运行训练、推理或指标评估；当前无质量分数。
- 资产/限制：D 盘可用空间约 396 GB，机器配有 RTX 4060 8 GB；当前运行时缺少 PyTorch。仅使用本地电脑，不进行板卡、Vivado、RTL、PL、实时或真人试听测试。
- PR 协调：开放 PR #9 也修改 `coummucation.md`，但与本任务分工不同；本分支只追加本任务记录，推送前将从最新 `main` 更新并检查差异。
- 报告链接：首轮资产恢复/评测完成后新增正式结果报告。
- 模型产物：无。
- 提交或 PR：暂未提交；本记录只在任务分支本地，等待资产恢复和评测结果。
- 下一责任方：Remote-PS-C 按固定来源/SHA 准备 HuBERT 与 FARGAN 运行链，随后执行电脑端五门评测。

### [PS-20261025-20] Remote-PS-C 资产恢复阻塞记录
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（网络连接与运行资产不足，未进入训练或评估）
- 基准提交：`ba48816b449a256bc5a331476999831b3ee444f6`
- 检查：初次 fetch 使用失效的本机代理失败；用命令级直连 `git -c http.proxy= fetch origin --prune` 成功，确认 `origin/main` 仍为 PR #10 合并提交 `ba48816b449a256bc5a331476999831b3ee444f6`。只读抓取并检查 PR #9；它也修改共享 `coummucation.md`，提交前须保留双方内容。
- 环境：`build/generated/remote_ps_c_env` 使用 Python 3.12.14；按项目锁文件安装全部依赖，PyTorch/torchaudio 使用官方 `2.7.1+cpu` wheel，CUDA 不可用。
- 资产：批准的 Fixed-Male 1～5、目标 Track 5～9 WAV 均在仓库。Pinned HuBERT `pytorch_model.bin` 已下载且 SHA-256 为 `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`；WeSpeaker ONNX SHA-256 与清单一致（`e7584940aeac8d5512d875e58ce6c09ba4ddad65d8128e1dac0d93aadd087ebb`）。FARGAN 官方模型/源码及 UTMOS、Whisper 权重下载受连接重置或超时影响，尚缺；旧训练语料/配对特征清单也不在本 checkout。未使用替代模型或缓存。
- 复现命令与逐项结果：见 `report/ps_20261025_20_asset_recovery_blocked_20261026.md`。
- 量化结果：未训练、未推理、未运行五项指标；无模型质量结论。未播放或录制音频，未接触板卡/Vivado/RTL/PL。
- 下一步恢复条件：补齐并校验官方 FARGAN、UTMOS、Whisper 与 teacher/配对训练语料；然后按既定冻结切分运行电脑端评测。
- 提交：本地提交 `2839e3867a81d8fb1523e8c3af39e9a3b9bf49b6`；Git push 因 Git Credential Manager 无可用凭证失败，GitHub App 创建分支 ref 返回 HTTP 403，尚无远端分支或 PR。
- 下一责任方：Remote-PS-C（需 GitHub 仓库写权限/凭证后推送本提交并创建 PR，再补齐缺失资产继续评测）。

### [PS-20261025-20] 代理恢复后远端与提交权限复查
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（网络已恢复；本机 GitHub 凭证缺失，评测运行资产仍缺）
- 基准提交：`ba48816b449a256bc5a331476999831b3ee444f6`
- 检查：命令行确认 FlClash HTTP/Mixed 代理 `127.0.0.1:7890` 正在监听；经该端口 `git fetch origin --prune` 和 `git ls-remote` 成功，远端 `main` 仍为 `ba48816b449a256bc5a331476999831b3ee444f6`。GitHub 公共 API 返回 200；唯一开放 PR 为 PR #9（协作文档任务），任务分支尚未创建在远端。
- 凭证：`git credential-manager github list` 未返回账号；非交互推送失败，明确提示无法获取密码。没有输出、读取或更改任何凭证。当前两笔任务记录提交仍仅在本地。
- 资产：复查任务 checkout 和历史固定路径，FARGAN 主模型/运行程序、配对特征语料及其清单仍缺；不以已通过的历史 FARGAN oracle 报告冒充训练数据或完整映射链。
- 复现命令：`git -c http.proxy=http://127.0.0.1:7890 fetch origin --prune`；`git -c http.proxy=http://127.0.0.1:7890 ls-remote origin HEAD refs/heads/main`；`git credential-manager github list`；`$env:GIT_TERMINAL_PROMPT='0'; $env:GCM_INTERACTIVE='Never'; git -c http.proxy=http://127.0.0.1:7890 -c credential.interactive=never push -u origin agent/ymheee/PS-20261025-20`。
- 量化结果：没有训练、推理、音频生成或五项质量评测；本轮不产生质量分数。未播放/录制音频，未做板卡、Vivado、RTL、PL、实时或真人试听。
- 报告：`report/ps_20261025_20_asset_recovery_blocked_20261026.md`（原资产缺口）、`report/ps_20261025_20_network_credential_retry_20261026.md`（本次网络/凭证复查）。
- 下一步：本机先通过 Git Credential Manager 完成 GitHub 登录并确认账号具仓库写权限；Remote-PS-C 随后刷新远端、推送本地提交、创建任务 PR。评测仍需补齐并核验官方 FARGAN 运行资产和经批准的配对训练语料，以及既定评估权重。

### [PS-20261025-20] 官方 FARGAN 资产恢复
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（FARGAN 权重已核验；配对训练语料与完整评估权重仍缺）
- 基准提交：ba48816b449a256bc5a331476999831b3ee444f6；分支 agent/ymheee/PS-20261025-20；草稿 PR #11。
- 修改路径：report/ps_20261025_20_fargan_asset_recovery_20261026.md、coummucation.md。
- 复现命令：见上述报告中的官方 Opus 模型包下载及 SHA-256 校验步骤。
- 量化结果：官方模型包 134674421 字节，SHA-256 a5177ec6fb7d15058e99e57029746100121f68e4890b1467d4094aa336b6013e；包内 FARGAN 权重 13775086 字节，SHA-256 2eb56f36f71f246174d769658b5712fa81214650bd425cf050c740c8d6b4464c，与项目清单一致。PR #11 verify-round-record 检查通过。
- 限制：没有配对 teacher 特征语料/清单和完整 UTMOS、Whisper 权重；未训练、推理或运行五项音质指标，没有质量分数。没有播放、录音、板卡、Vivado、RTL、PL、实时或真人试听结果。
- 下一责任方：Remote-PS-C 继续按固定来源和 SHA 恢复剩余资产；资产齐备后才运行本任务电脑端候选。Hardware-A/B 不据此启动板测。
### [PS-20261025-20] UTMOS 固定权重恢复
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（FARGAN 与 UTMOS 权重已核验；Whisper 权重及配对训练语料/清单仍缺）
- 基准提交：ba48816b449a256bc5a331476999831b3ee444f6；分支 agent/ymheee/PS-20261025-20；PR #11。
- 修改路径：report/ps_20261025_20_fargan_asset_recovery_20261026.md、coummucation.md。
- 复现：UTMOS 下载 URL 与 SHA 命令记录于报告；固定 SHA 为 38aa51ab79e2a4e09a1449758a4b37e9cbb2e8235a49662a732d33a9ba1e9bff。
- 量化结果：UTMOS 权重 411179119 字节，SHA 与项目清单完全一致；Whisper-small revision 973afd24965f72e36ca33b3055d56a652f456b4d 仍只有未完成缓存片段。没有训练、推理或五项评分。
- 限制：配对 HuBERT→FARGAN 训练特征及清单缺失，Whisper 评估器未完整恢复；电脑端质量结论无。未播放/录音、板卡、Vivado、RTL、PL、实时或真人试听。
- 下一责任方：Remote-PS-C 恢复批准的配对训练资产与 Whisper 固定修订权重，之后运行电脑端五门评测。
### [PS-20261025-20] Whisper-small 固定版本恢复及加载检查
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（FARGAN、UTMOS、Whisper 权重已恢复；配对训练语料/清单仍缺）
- 基准提交：ba48816b449a256bc5a331476999831b3ee444f6；分支 agent/ymheee/PS-20261025-20；PR #11。
- 修改路径：report/ps_20261025_20_fargan_asset_recovery_20261026.md、coummucation.md。
- 复现：`$env:HF_HOME='D:\fpga\.git-repair\build\generated\remote_ps_c_assets\hf_home'; $env:HF_HUB_OFFLINE='1'; build/generated/remote_ps_c_env/Scripts/python.exe -c "from transformers import WhisperProcessor,WhisperForConditionalGeneration; p='D:/fpga/.git-repair/build/generated/remote_ps_c_assets/hf_home/hub/models--openai--whisper-small/snapshots/973afd24965f72e36ca33b3055d56a652f456b4d'; q=WhisperProcessor.from_pretrained(p,local_files_only=True); m=WhisperForConditionalGeneration.from_pretrained(p,local_files_only=True); print(len(q.tokenizer),sum(x.numel() for x in m.parameters()))"`
- 量化结果：Whisper revision `973afd24965f72e36ca33b3055d56a652f456b4d`，11/11 需要文件齐全，权重 966995080 字节；离线加载成功，词表 51865，参数 241734912。只验证加载，不转写/不报 CER。固定 FARGAN 训练 corpus、expanded corpus 与原始训练 corpus 路径均不存在。
- 限制：缺少批准的 HuBERT→目标 FARGAN 配对训练特征及 manifest；没有训练、推理或五项评分，也无候选质量结论。未播放/录音、板卡、Vivado、RTL、PL、实时或真人试听。
- 下一责任方：Remote-PS-C 待恢复有来源和 SHA 的配对训练语料后，继续电脑端方案训练与客观评测。
### [PS-20261025-20] FARGAN 配对数据契约复核
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（旧配对语料缺失，当前冻结 WAV 不构成同内容训练对）
- 基准提交：ba48816b449a256bc5a331476999831b3ee444f6；分支 agent/ymheee/PS-20261025-20；PR #11。
- 修改路径：report/ps_20261025_20_fargan_asset_recovery_20261026.md、coummucation.md。
- 复现依据：阅读交接/核心材料/neural_reference/prepare_fargan_features_20261006.py、train_fargan_mapper_20261006.py；检查交接/核心材料/board_budget_20261005/fargan_corpus/manifest.json 及 recorded legacy root，均不存在。
- 量化结果：旧训练契约要求同一内容的 source_features/teacher_features 成对数据和独立 Track 5–8 target_training anchors；当前 checkout 只有 Fixed-Male 与目标 WAV，无 teacher WAV 或逐句对齐清单。没有以文件顺序、时长或非平行录音构造伪标签。
- 限制：任务仍未训练或推理，无五项评分和候选质量结论；未播放/录音或做板卡、Vivado、RTL、PL、实时、真人试听。
- 下一责任方：Remote-PS-C 获取项目批准、可校验来源的 target-style teacher 生成链及同内容配对训练样本后继续；不自行引入不匹配数据或新模型。

### [PS-20261025-20] Teacher 来源与固定运行资产恢复重试
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（数据路径已定位；固定 CosyVoice 源码/权重无法下载，未生成 teacher）
- 基准提交：`856973c6a5dfd9f1ebc8de727330dbcb7628ad22`；分支 `agent/ymheee/PS-20261025-20`；PR #11。
- 修改路径：`report/ps_20261025_20_teacher_source_recovery_20261026.md`、`coummucation.md`。
- 复现命令：见报告；任务资产目录内检查无 CosyVoice 文件，`127.0.0.1:7890` 当前无监听，直连 pinned source `git ls-remote` 返回 `Recv failure: Connection was reset`。
- 量化结果：归档中的目标 prompt 为 Track 6 前 8 秒，记录 SHA-256 `4651ab56a9b285c0d645bd6f0b94f7987e6ed8bd5171e54c37048b436e177c8f`、1,536,080 字节。由规范 Track 6 直接裁前 8 秒并保存为 PCM16 得到 1,536,044 字节、SHA-256 `9755f0cfac29bd42c0628ec6707f0df7dcd09c15149a95db3d1d4729261f7361`，未匹配归档文件，故不冒称其为原件。男声 1～5 与目标 Track 5～9 均在仓库且受控批准。
- 固定版本：CosyVoice source `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc`、模型 `29e01c4e8d000f4bcd70751be16fa94bf3d85a18`；本机未找到对应源码/权重。现有 PyTorch 环境为 CPU 版。
- 限制：未生成 teacher WAV/配对训练样本、未训练、未推理、未运行五项指标，无模型质量结论。未播放/录音、板卡、Vivado、RTL、PL、Cortex-A9 或实时测试。
- 下一责任方：Remote-PS-C 在本机网络恢复后获取且校验固定 CosyVoice 源码/权重，再按原固定切分生成 teacher pairs；Track 9 保持锁定，不替换模型或数据。

### [PS-20261025-20] 网络与提交重试
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：BLOCKED（7890 无监听；FlClash 启动后立即退出；提交未推送）
- 基准提交：`ee3316a057094ad7ebe7859884043cdc7c8dc026`；分支 `agent/ymheee/PS-20261025-20`；PR #11。
- 修改路径：`report/ps_20261025_20_network_retry_20261026.md`、`coummucation.md`。
- 复现命令：见报告；配置仍声明 `127.0.0.1:7890`，启动 `D:\FlClash\FlClash.exe` 返回 0 但无进程/监听；无代理直连 push 报 `getaddrinfo() thread failed to start`。
- 量化结果：无新增训练、推理、音频或五门指标；本地分支仍比远端任务分支多 1 个提交。
- 限制：固定 CosyVoice 源码/权重与历史配对语料仍缺，未使用替代数据或模型；无板卡、Vivado、RTL、PL、Cortex-A9、实时或真人试听结论。
- 下一责任方：恢复可工作的代理或直接网络及 GitHub 凭证后，推送现有提交并继续固定 teacher 资产恢复。

### [PS-20261025-20] Remote-PS-C 接收 PR #12 配对语料并纠正网络结论
- 日期：2026-10-26
- 角色/Agent：Remote-PS-C / Codex
- 状态：ACCEPTED_ASSET_ONLY / CLAIMED（训练链恢复；尚无候选质量结果）
- 基准提交：main `9c42263`，本任务分支已合并同步；保留此前发布历史，继续 PR #11。
- 检查：系统级确认 FlClashCore 监听 `127.0.0.1:7890`，经代理 GitHub HTTP 200，现有 Git 凭据账号 `ymheee` 可用。此前受限命令不可见的结果不能证明代理退出或凭据缺失；前两条网络阻塞结论由本条纠正。开放 PR #9/#11/#13 已核对，未覆盖其他候选。
- 量化结果：PR #12 Release 附件 125109914 bytes、SHA-256 `956dead3c76b1e214cc6baf5a1dca0b7e083eebb2771e417b722df6e2181366c`；本机独立下载/解包校验 `PASS 200 800`。辅助语料 192 train/8 validation；Fixed-Male 1–3/4/5、女声 Track 5–8/9 切分不变。
- 改动路径与复现：`report/ps_20261025_20_corpus_receipt_20261026.md`、`coummucation.md`、`team_project/project_status.md`、`report/ai_worklog.md`。
- 限制：仅解除语料和网络阻塞；未训练/推理/五门评分，teacher 未获真人质量验收；未播放、录音或进行板卡/Vivado/RTL/PL/Cortex-A9/实时测试。
- 下一责任方：Remote-PS-C 恢复电脑端 FARGAN 合成与 HuBERT 内容特征，按辅助 train split 训练独立候选，仅先筛选男声验证录音 4；录音 5 与 Track 9 保持锁定。

### [PS-20261025-20] HuBERT→目标 FARGAN v1 首轮电脑端筛选
- 日期：2026-10-26；角色/Agent：Remote-PS-C / Codex。
- 状态：REJECTED（源泄漏、CER 未过；不进入 WAIT_LOCAL_TEST）。
- 基准提交：`86afcf8d105c74538664d6ea405a790316ee563e`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；继续 PR #11，开放 PR #9/#11/#13 已检查，无任务分配改动。
- 修改路径：`build/build_remote_ps_c_fargan.py`、`build/remote_ps_c_hubert_fargan.py`、共享 strict evaluator 的可选资产路径参数、`report/ps_20261025_20_hubert_fargan_v1_20261026.{md,json}`、依赖锁、状态及工作日志。
- 数据/训练：已验证历史辅助 192 train/8 validation，仅辅助 train 拟合 PCA/统计/权重，辅助 validation 选择第 400 步；双向 GRU 1136852 参数，第 1200 步早停，训练 266.703 秒。未对固定男性 1～3 做源专用训练；只筛选录音 4。男声 5/目标 Track 9 保持锁定；语料尾帧按物理时长截断 319 帧，不做时长扭曲。
- 复现命令：报告包含 host GCC 构建、`remote_ps_c_hubert_fargan.py cache/train/infer` 以及既定 strict evaluator 的完整 PowerShell 命令；五门计算与门槛未改。
- 量化结果：身份均值 0.778814512（≥0.45）、P10 0.751711670（≥0.35）、严格源泄漏 0.252929151（要求≤0.10，FAIL）、UTMOS 2.418009599（≥2.30）、CER 0.235294118=16/68（要求≤0.15，FAIL）。18.2 秒音频本机全链含加载耗时 2.187 秒，RTF 0.120165；不代表板端实时。
- 限制：全句 HuBERT+双向 GRU 非因果；当前 Opus 源码不是历史归档的逐位同版，已固定归档/逐源 SHA 并保留 smoke 差异。该轮只发布方案/客观证据，Release 与干净目录接收复现作为随后独立测试轮提交。无播放、录音、真人试听、板卡、Vivado、RTL、PL、Cortex-A9 或实时时延验收。
- 下一责任方：Remote-PS-C 将该失败候选打包到私有 Release 并做干净下载推理以便追溯；Hardware-A/B 不据此启动试听或板测。

### [PS-20261025-20] 可移植交付命令首测及相对路径修复
- 日期：2026-10-26；角色：Remote-PS-C / Codex；基准：`74b16db6afe4a76def817e9f643a156b7b8389c0`。
- 状态：BLOCKED_DELIVERY；候选质量仍 REJECTED。仓库 API 返回 `private=false`，与 ARTIFACTS.md 第 18 行及交付说明第 39 行要求私有 Release 冲突；尚未创建 Release/上传附件/改仓库可见性，已请求用户指定私有位置或明确允许公开。
- 测试：新建 D: receive-check 独立检出及 Python 环境，逐件验证本地包 466 项，使用 `infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe`。模型推理已生成音频，但输出清单写入时因相对 `--output` 与绝对 ROOT 的 `relative_to` 不兼容而异常退出；此命令首测失败，不冒称交付通过。
- 修改：`build/remote_ps_c_hubert_fargan.py` 将 CLI 资产/输出/程序路径在入口统一 resolve；不改模型、统计、音频或评价计算。代码编译和绝对默认路径已有结果仍有效；随后在新干净检出重新测试该相对路径命令。
- 报告：`report/ps_20261025_20_portable_first_smoke_20261026.md`；下一责任方 Remote-PS-C 修复后重打包并复测，线上交付位置等待用户决定。未播放/录音/触碰硬件。

### [PS-20261025-20] 修复版完整归档与干净目录本地复现
- 日期：2026-10-26；角色：Remote-PS-C / Codex；基准/模型源码：`94d2aa2237d9053d76616f22bc166ac1b7f92437`。
- 状态：本地包复现 PASS；质量 REJECTED；线上交付 BLOCKED_PRIVATE_RELEASE。不是 WAIT_LOCAL_TEST，不安排 Hardware-A/B 试听或板测。
- 资产：`PS-20261025-20_hubert_fargan_v1_windows_cpu.zip`，198734997 bytes，SHA-256 `9532fe32d5ab707a51662b224f82a95abba901d9fc4fcc4276cedd0cf2ca4e6a`；466 个内部文件逐项校验，包含完整推理权重/统计/host 程序/源码审计/依赖/说明；不含 WAV/训练集/缓存。预定标签 `model-PS-20261025-20-hubert-fargan-v1` 尚未创建。
- 测试：新干净检出+空模型目录解包，独立 venv（复制锁定依赖库，未冒称重新 pip 安装），以 `infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe` 运行；审计禁止读取原生成目录，无违规访问。退出 0，输出 291200 samples/16kHz/mono PCM16，SHA-256 `ee548f1aef80fc9a032e3557b08090091d1bb91f05a512b20b1b654ed56af109` 与原评价 WAV 完全相同。
- 量化：封装进程 7.7018374 秒，推理报告 2.563 秒/RTF 0.140824176；Python 峰值工作集 1111027712 bytes、峰值 pagefile 2381021184 bytes（不含 native 子进程，非板端预算）。原质量五门保持 0.778814512/0.751711670/0.252929151/2.418009599/0.235294118，泄漏/CER 失败。
- 报告/路径：`report/ps_20261025_20_model_archive_local_smoke_20261026.md`、`report/model_delivery_PS-20261025-20_hubert_fargan_v1_20261026.json`、原始 smoke TXT、状态/日志。完整复现命令与全部文件 SHA 在报告/清单中。
- 阻塞：仓库实际公开（API `private=false`），与 ARTIFACTS.md:18/交付说明:39 的私有 Release 要求冲突。未上传附件或更改仓库可见性/规则；已请求用户指定允许的私有交付位置或明确允许当前公开仓库发布。当前仅本地归档复现，未声称 GitHub 下载或跨电脑交付通过。
- 下一责任方：Remote-PS-C 在用户明确交付位置后发布此精确包并从空目录下载推理，提交独立接收记录。质量失败仍阻止任何试听/硬件阶段。无播放/录音/真人/硬件/实时验收。


### [PS-20261025-20] 用户授权公开 Release 与 GitHub 干净下载复现
- 日期：2026-10-26；角色：Remote-PS-C / Codex；基准分支提交 `58f85c02c16d404a11c03cd359887e1ee337e5dc`；模型源码 `94d2aa2237d9053d76616f22bc166ac1b7f92437`。
- 状态：交付 VERIFIED_GITHUB_DOWNLOAD_AND_INFERENCE；质量仍 REJECTED（泄漏/CER 失败），不进入 WAIT_LOCAL_TEST。
- 授权：用户明确回复“授权在当前公开仓库发布完整模型包”。此轮按该授权解决此前私有 Release 约束冲突；仓库仍公开，没有改任务分配、规则或可见性。
- 资产：https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/model-PS-20261025-20-hubert-fargan-v1；附件 `PS-20261025-20_hubert_fargan_v1_windows_cpu.zip`，198734997 bytes，SHA-256 `9532fe32d5ab707a51662b224f82a95abba901d9fc4fcc4276cedd0cf2ca4e6a`；GitHub server digest/标签目标/下载大小与 SHA/466 内部文件全核对。
- 测试：空 github-download 目录从 GitHub 下载，download-code 新干净精确检出+空模型目录解包，独立 venv（复制锁定依赖，未测试新 pip 安装），文件访问审计无原生成目录访问。相对路径 infer 命令退出 0；16kHz mono PCM16/291200 samples，输出 SHA `ee548f1aef80fc9a032e3557b08090091d1bb91f05a512b20b1b654ed56af109` 与原评价相同。
- 量化：推理 2.734 秒，RTF 0.150219780，封装耗时 8.387427 秒，Python 峰值工作集 1111740416 bytes/pagefile 2381811712 bytes（不含 native 子进程）。原五门 0.778814512/0.751711670/0.252929151/2.418009599/0.235294118；WAV 完全相同故未重复评分。
- 改动/复现：`report/ps_20261025_20_github_model_receipt_20261026.md`（完整下载/校验/环境/推理命令）、同名 JSON、原始 smoke TXT、model_delivery JSON（保留历史本地测试）、状态/工作日志、`coummucation.md`。
- 限制：同一电脑隔离接收测试，不是第二台实体电脑实测；非因果离线候选，电脑速度/内存不代表板端。男性 5/Track9 保持锁定。无播放/录音/试听/板卡/Cortex-A9/Vivado/RTL/PL/实时验收。
- 下一责任方：Remote-PS-C 保存失败 v1 与完整交付证据；Hardware-A/B 不据此启动试听或板测，后续仍须独立通过全部客观门。

### [PS-20261025-20] v1 配对标签及动态误差诊断认领
- 日期：2026-10-26；角色：Remote-PS-C / Codex；状态：CLAIMED；基准 `fdade89b7cbf2aa6e8d1546e957535aca8ec7ae8`，main `9c42263ea3aa12898ad451f3c00915e816f039c4`。已 fetch 并核对 PR #9/#11/#13，无同路线新增冲突；保留已发布分支历史，不 rebase。
- 范围：只诊断本任务 v1；逐项校验既有配对资产，以同一 host 分析器重新提取 source/teacher 特征，检查标签一致性及能量时移；在既有辅助 validation 8 对上比较冻结 mapper 与 train-mean 基线的逐维误差/方差/一阶差分。固定 ±300ms 能量相关仅作诊断，不据此自动对齐或选参。
- 路径/复现：拟新增 `build/diagnose_remote_ps_c_fargan_v1.py`，命令 `build/generated/remote_ps_c_env/Scripts/python.exe build/diagnose_remote_ps_c_fargan_v1.py`；小型证据进入 `report/ps_20261025_20_feature_diagnostic_20261026.{json,md}`，生成物留 `build/generated/remote_ps_c_diagnostic_v1/`。
- 量化结果：待运行；不训练新权重，不重复 Fixed-Male4 选参，不读取 Male5/Track9；五项门槛保持原样，v1 质量仍 REJECTED。
- 限制/下一责任方：Remote-PS-C 按证据提出单变量下一轮；不播放、录音、试听或运行板卡/Cortex-A9/Vivado/RTL/PL，不进入 WAIT_LOCAL_TEST。

### [PS-20261025-20] v1 配对标签及动态误差诊断结果
- 日期：2026-10-26；角色：Remote-PS-C / Codex；基准 `fdade89b7cbf2aa6e8d1546e957535aca8ec7ae8`；状态：诊断 PASS，候选质量仍 REJECTED。
- 改动/复现：`build/diagnose_remote_ps_c_fargan_v1.py`；执行 `build/generated/remote_ps_c_env/Scripts/python.exe build/diagnose_remote_ps_c_fargan_v1.py`；报告 `report/ps_20261025_20_feature_diagnostic_20261026.{md,json,txt}`，状态/日志同步追加。报告含已交付包+配对 corpus 重建缓存步骤。
- 数据结果：800 个资产大小/SHA 匹配、200 个缓存 target 与 teacher 截断前缀逐元素相同。400 次重提取的逐句 MAE 均值 source 0.0007785375 / teacher 0.0005537752；倒谱 0–17 MAE 1.39e-7/1.92e-7，但全局最大差 1.702459217/1.282008648，逐句最大差全部落在音高/周期相关维度，不能宣称历史逐位一致。
- 对齐结果：200 对零时移能量相关均值 0.862052121，最佳时移绝对值中位数 0ms/P90 10ms/最大 20ms；只作固定 ±300ms 诊断，没有移动训练标签，不能证明逐音素对齐。
- 模型结果：冻结辅助 validation 8 对/4616 帧，归一化 MAE 0.452730745 vs 训练均值基线 0.806939065；20 维 MSE 均优于常数基线。维度 14–18 的差分 RMS 比 teacher 为 0.266/0.270/0.329/0.228/0.263，提示动态偏弱，但未证明这是 CER/泄漏根因，也不能排除 teacher 分析抖动。最终退出 0、26.734 秒；此前 WinError623 与诊断类型错误已保留原始失败记录并修正执行/输入类型。
- 限制：没有新权重、训练或新五门评分；原身份/P10/泄漏/UTMOS/CER 仍 0.778814512/0.751711670/0.252929151/2.418009599/0.235294118，泄漏/CER 失败。未读取 Fixed-Male/目标 WAV，Male5/Track9 锁定；无试听/硬件/实时验收，非 WAIT_LOCAL_TEST。
- 下一责任方：Remote-PS-C；下一候选可只改 delta loss 权重 0.25→1.0，沿用其余训练规则，在辅助 validation 选 checkpoint 后仅做一次 Male4 原口径筛选；该候选本轮尚未训练。Hardware-A/B 不据此进入板测。

### [PS-20261025-20] v2 单变量 delta=1.0 实验认领
- 日期：2026-10-26；角色：Remote-PS-C / Codex；状态：CLAIMED；基准 e8bb8e016caf987ad0f2dc99521794c97b8fd192；main 9c42263ea3aa12898ad451f3c00915e816f039c4。已 fetch 并核对开放 PR #9/#11/#13，无本任务冲突；保留已发布历史，不 rebase/force push。
- 假设/范围：只把一阶时间差分 SmoothL1 权重从 0.25 调到 1.0，检验动态监督是否改善；其余数据切分、seed、PCA、结构、优化器、检查点选择、五项门槛不变。200 份既有缓存按 SHA 校验复用；v1 权重/统计/Release 不覆盖。
- 路径/复现：build/remote_ps_c_hubert_fargan.py 最小共享入口调整；新增 build/remote_ps_c_hubert_fargan_v2.py；train --cache-root build/generated/remote_ps_c_hubert_fargan_v1 后 infer；build/evaluate_seed_fixed_male_strict_20261024.py 对 v2 evaluation_manifest.json 仅筛选一次。生成物进入 build/generated/remote_ps_c_hubert_fargan_v2/；正式报告 report/ps_20261025_20_hubert_fargan_v2_20261026.*。
- 量化：待运行；只在辅助 validation 8 对选检查点，再做一次 Fixed-Male4 原五门；不因结果追加本轮参数扫描。Male5/Track9 保持锁定。
- 限制/下一责任方：Remote-PS-C 完成此轮、失败同样提交 PR #11；未全过不进入 WAIT_LOCAL_TEST。无录音/播放/试听/板卡/Cortex-A9/Vivado/RTL/PL/实时验收，不改分配或规则。


### [PS-20261025-20] v2 delta=1.0 单变量结果
- 日期：2026-10-26；角色：Remote-PS-C / Codex；状态：REJECTED；基准 e8bb8e016caf987ad0f2dc99521794c97b8fd192；main 9c42263ea3aa12898ad451f3c00915e816f039c4；开放 PR #9/#11/#13 无本任务冲突。
- 路径/复现：build/remote_ps_c_hubert_fargan_v2.py train --cache-root build/generated/remote_ps_c_hubert_fargan_v1，然后 infer，再运行原 strict evaluator；report/ps_20261025_20_hubert_fargan_v2_20261026.md/JSON/TXT 保存完整命令/日志/转写/哈希。共享入口只增加版本输出名与显式缓存复用；状态/工作日志追加。
- 唯一训练变量：delta loss 0.25→1.0；其余配置逐项相同，200 缓存 SHA 已核验，重算统计数组与 v1 完全相同；v1 权重/统计/缓存不变。辅助 validation 最优step400、停止step1200、损失0.2605001032、272.828秒；跨权重总损失不可直接比较。
- 一次 Male4 原五门：身份 0.778145609 / P10 0.755978229 / 泄漏 0.255133692 / UTMOS 2.574109713 / CER 0.235294118；通过项 {'identity': True, 'identity_p10': True, 'leakage': False, 'utmos': True, 'cer': False}。输出SHA 9e7f37895e8188b96909edad73b140fbcf5e7a14ebd3c1202605a27b339745e7；mapper 610f592539fd51420409ca413e04232f3cd20da57f885957d050c6157569791c。
- 限制/下一责任方：仅电脑端；辅助192train/8validation，未拟合Fixed-Male1–3；Male5/Track9锁定；无参数扫描/门槛更改/录音/播放/试听/板卡/ARM/Vivado/RTL/PL/实时验收。Remote-PS-C 完成版本化模型归档与干净下载；未全过不进入 WAIT_LOCAL_TEST，不给Hardware-A/B启动板测。

### [PS-20261025-20] v2 完整模型 Release 与干净下载认领
- 日期：2026-10-26；角色：Remote-PS-C / Codex；状态：CLAIMED；基准/模型源码 0a8ae4e261cc098cc8c489a12865d9c28452fe64；PR #11。
- 范围/授权：按用户已授权“授权在当前公开仓库发布完整模型包”，发布唯一新标签 model-PS-20261025-20-hubert-fargan-v2 的完整推理包，不覆盖 v1。包包含 mapper/statistics/HuBERT/native/源码与许可/配置/依赖锁/说明，不含 WAV/训练语料/缓存。
- 路径/复现：生成物 build/generated/remote_ps_c_release_v2_fixed/；GitHub 下载到全新 D:/fpga/receive-check/PS-20261025-20-hubert-fargan-v2/；精确检出上述源码并逐文件校验，独立环境执行 build/remote_ps_c_hubert_fargan_v2.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe。证据 report/ps_20261025_20_github_model_receipt_v2_20261026.*、model_delivery_PS-20261025-20_hubert_fargan_v2_20261026.json。
- 量化：待打包/下载/推理；仅验证交付和输出 SHA 与原评价相同，不重新选五门或调参；v2 质量仍 REJECTED，泄漏0.255133692/CER0.235294118失败。
- 限制/下一责任方：同机隔离复验，非第二台实体电脑；Remote-PS-C 回填 PR #11 与交流/状态/日志。无试听/硬件/实时验收，非 WAIT_LOCAL_TEST；Male5/Track9锁定，不改规则/分配/可见性。


### [PS-20261025-20] v2 完整 Release 与干净下载结果
- 日期：2026-10-26；角色：Remote-PS-C / Codex；基准/源码 0a8ae4e261cc098cc8c489a12865d9c28452fe64；状态：交付 VERIFIED_GITHUB_DOWNLOAD_AND_INFERENCE，质量 REJECTED；PR #11。
- 授权/资产：沿用用户“授权在当前公开仓库发布完整模型包”；https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/model-PS-20261025-20-hubert-fargan-v2；附件 PS-20261025-20_hubert_fargan_v2_windows_cpu.zip，198735391 bytes，SHA a669cb614dc4f71090b898da48e7fc127fbf016892dc3d655be1a535042a4441。标签指向精确源码，server digest/下载大小/SHA及466个内部文件全匹配；无WAV/语料/缓存，v1未改。
- 路径/复现：report/ps_20261025_20_github_model_receipt_v2_20261026.md/JSON/TXT（完整下载/校验/依赖/推理命令）；model_delivery_PS-20261025-20_hubert_fargan_v2_20261026.json（逐文件SHA）；独立新目录执行 build/remote_ps_c_hubert_fargan_v2.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe。状态/工作日志同步追加。
- 量化：干净GitHub下载推理exit0，2.750s/RTF0.151098901，封装53.756680s；16kHz mono PCM16/291200 samples，输出SHA 9e7f37895e8188b96909edad73b140fbcf5e7a14ebd3c1202605a27b339745e7 与本轮五门原WAV完全相同，未重新评分。Python峰值工作集1110630400 bytes/pagefile2384629760 bytes，不含native子进程。
- 失败保留：首次上传后/下载前缺少接收父目录报WinError3；创建父目录后核对同一附件，未覆盖发布。日志保留失败及最终成功；独立venv复制锁定库，未测试新pip安装；同机隔离复验，非第二台实体电脑。
- 限制/下一责任方：身份0.778145609/P10 0.755978229/泄漏0.255133692/UTMOS2.574109713/CER0.235294118，泄漏/CER仍失败，非WAIT_LOCAL_TEST。Remote-PS-C保存证据，Hardware-A/B不启动试听/板测；Male5/Track9锁定，无录音/播放/真人/ARM/Vivado/RTL/PL/实时验收，未改分配/规则/可见性。

### [PS-20261025-20] 冻结教师→声码器→映射器内容归因诊断认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准 04819add786e0c07f9772afadaf7a2ba67f565d7；main 9c42263ea3aa12898ad451f3c00915e816f039c4。已 fetch 并检查开放 PR #9/#11/#13、PR #11 评论和 reviews，无新增审核/同任务冲突；保留已发布分支历史。
- 范围：只使用现有辅助 validation 8 对，冻结 v1/v2 检查点、统计、缓存及 native。按共同整帧时长比较 source、现有 CosyVoice3 teacher PCM、teacher20D→FARGAN oracle 和 v1/v2→FARGAN；Whisper-small 转写对 source ASR 与清单文本分别计算 CER。辅助源声纹使用同说话人其它 validation 句的留一质心；目标只用 Track5–8。此为训练验证集内诊断，不能替代固定男性五门或人耳验收。
- 路径/复现：拟新增 build/diagnose_remote_ps_c_fargan_chain.py；输出 build/generated/remote_ps_c_chain_diagnostic_20261027/；正式 report/ps_20261025_20_chain_diagnostic_20261027.md/JSON/TXT。运行已有 D: Python 环境执行该诊断脚本，完整参数与资产 SHA 随结果记录。
- 量化/停止条件：固定8对、5种波形，不训练、不选五门、不扫描超参；完成转写及声纹描述即停止本轮并提交/推送。D盘余量378859724800 bytes，C盘92122632192 bytes；现有资产足够，无新增下载。Male1–5不读取，Track9锁定，无录音/播放/真人/ARM/Vivado/RTL/PL/实时验收。
- 下一责任方：Remote-PS-C 根据原始诊断回填证据及 PR #11；v1/v2 保持 REJECTED，不交硬件方现场测试。


### [PS-20261025-20] 冻结教师→声码器→映射器诊断结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：DIAGNOSTIC_COMPLETE，v1/v2 质量仍 REJECTED，非 WAIT_LOCAL_TEST；基准 04819add786e0c07f9772afadaf7a2ba67f565d7；main 9c42263ea3aa12898ad451f3c00915e816f039c4（提交前再次 fetch，保持祖先）；PR #11，未改分工/规则。
- 路径/复现：build/diagnose_remote_ps_c_fargan_chain.py；report/ps_20261025_20_chain_diagnostic_20261027.md/JSON/TXT。项目根目录执行 build/generated/remote_ps_c_env/Scripts/python.exe -m py_compile build/diagnose_remote_ps_c_fargan_chain.py，再以 -u 运行同脚本；完整 PowerShell 命令、资产前提及 SHA 见报告。固定现有辅助 validation 8 对/2 人/4616 帧、5 条件共40波形；冻结模型/统计/缓存，无训练或新权重。
- 量化：source/teacher PCM/teacher features oracle/v1/v2 的 CER（相对源自动转写）为0/150、15/150、16/150、20/150、20/150；相对清单文本为21/152、22/152、25/152、28/152、31/152。目标身份均值0.186086690/0.868033508/0.799975958/0.780120042/0.778752680；描述性源相似度均值0.842271856/0.234730201/0.242190654/0.225207688/0.229753263。
- 验证：exit0、90.219秒；8对/40条件/4616帧、有限值、CER及均值重算、127个不同文件大小/SHA及WAV格式/时长核对PASS。权重/统计未变；保留原ASR警告。运行后D余量378846371840 bytes/C92113235968 bytes；生成物留D项目忽略目录，无下载。
- 限制：辅助集已用于选检查点；清单未经本轮人工复核，源ASR与清单已有13.82%差异。源画像逐句留一且不同于Fixed-Male验收，不能套用泄漏门；未算UTMOS，指标差值不能证明因果或固定男性失败根因。v2无内容改善。原五门数值/拒绝结论不变，不继续delta扫描；未读Fixed-Male音频/Track9，Python保护非OS全量审计；无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时验收。
- 下一责任方：Remote-PS-C提交本轮证据及更新PR #11，维护者审核；既有v1/v2模型Release保持不变，Hardware-A/B不由本轮启动试听或板测。本轮停止，不新增训练。

### [PS-20261025-20] v3 PCA192 单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准60364cb333dc0f3474797f05222a8948bbcb9e26；已fetch main9c42263ea3aa12898ad451f3c00915e816f039c4，开放PR #9/#11/#13无同任务冲突，保留已发布历史。
- 假设/控制：v1 PCA96保留训练方差0.749045423，未知被丢弃分量是否有助内容；只将v1 pca_dim96→192，delta_weight恢复/保持v1的0.25，其余配置、数据、损失、seed、2000步上限/每100步验证/patience8、native和原五门不变。维度变化必然改变首层形状/参数量及随机数消耗，不宣称同初始化；不作维度扫描。
- 路径/复现：拟新增build/remote_ps_c_hubert_fargan_v3.py；train --cache-root build/generated/remote_ps_c_hubert_fargan_v1，再infer和原strict evaluator；输出build/generated/remote_ps_c_hubert_fargan_v3/，正式report/ps_20261025_20_hubert_fargan_v3_20261027.*。复用现有SHA已固定语料/缓存，不新增真人音频或教师数据。
- 量化/停止：辅助192train/8validation选检查点后只做一次Male4原五门；无结果前不承诺改善。Male1–3仅原评价源画像、不拟合；Male5/Track9锁定。先保存训练/评价轮次，再独立提交版本化交付轮次。预计完整包约200MB、独立接收环境数GB；D余量378838573056 bytes/C92046622720 bytes，全部大型资产/缓存在D项目总目录。
- 限制/下一责任方：Remote-PS-C完成本轮和PR #11；失败同样提交，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明，未全过不进入WAIT_LOCAL_TEST。沿用用户已授权当前公开仓库发布完整模型包，不改规则/分配/可见性。


### [PS-20261025-20] v3 PCA192 单变量结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准60364cb333dc0f3474797f05222a8948bbcb9e26；main9c42263ea3aa12898ad451f3c00915e816f039c4，开放PR #9/#11/#13无冲突。
- 路径/复现：build/remote_ps_c_hubert_fargan_v3.py、build/run_remote_ps_c_hubert_fargan_v3.py；report/ps_20261025_20_hubert_fargan_v3_20261027.md/JSON/TXT。驱动固定train复用v1缓存、infer、原strict evaluator一次五门；完整命令与资产SHA见报告。
- 唯一配置变量：相对v1 pca_dim96→192，delta0.25不变；保留训练方差0.862445935（v1为0.749045423），参数1155284；维度改变初始化随机数消耗，非同初始化。训练/验证192/8，最佳step400、停止1200、loss0.1972120106、271.313s。mean/y统计/分位、投影前96和旧模型/缓存保持一致。
- 一次Male4五门：身份0.763920106/P100.747006375/泄漏0.261376895/UTMOS2.508168141/CER0.558823529；通过项{'identity': True, 'identity_p10': True, 'leakage': False, 'utmos': True, 'cer': False}。输出SHAd1fb89990a7c5cdc2a57174d1f1e0f5b5c3715239fd19c5e07594469c39cf703，mapper836a4595e6fc2bc8992107645b58a6ffd97ecdb724ef91186093009058b397aa。各阶段exit0，语法/有限JSON/格式/哈希/原评估器口径检查PASS；首次启动自动审核超时、未启动进程，重试一次成功。
- 限制/下一责任方：辅助集选检查点，Male4开发筛选非独立验收；Male1–3只作源画像，Male5/Track9锁定。Python保护非OS全量审计，无录音/播放/真人/硬件/ARM/Vivado/RTL/PL/实时验收，不改规则/分工。Remote-PS-C另轮发布完整模型与干净下载；未全过不进入WAIT_LOCAL_TEST，不据结果追加本轮维度扫描。


### [PS-20261025-20] v3 完整模型 Release 与干净下载认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准/模型源码 ce4f2c7e9e7b3bc09b8c37532dbfb3f8d258c1bb；PR #11，main9c42263ea3aa12898ad451f3c00915e816f039c4，开放PR #9/#11/#13无同任务冲突。
- 范围/授权：沿用用户“授权在当前公开仓库发布完整模型包”，仅创建新标签 model-PS-20261025-20-hubert-fargan-v3 的完整推理包，不改既有版本或规则/分工/仓库可见性。v3质量仍REJECTED，源泄漏0.261376895/CER0.558823529失败，不进入WAIT_LOCAL_TEST。
- 路径/复现：build/generated/remote_ps_c_release_v3_fixed/；新<workspace>/receive-check/PS-20261025-20-hubert-fargan-v3/，从GitHub下载/逐项SHA/精确检出ce4f2c7e9e7b3bc09b8c37532dbfb3f8d258c1bb，独立环境运行build/remote_ps_c_hubert_fargan_v3.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe。正式report/ps_20261025_20_github_model_receipt_v3_20261027.*及model_delivery JSON。
- 量化/停止：只验证交付与输出SHA d1fb89990a7c5cdc2a57174d1f1e0f5b5c3715239fd19c5e07594469c39cf703，不重新五门/训练/调参；预计200MB包与数GB接收环境，大型内容均在非系统盘项目目录。
- 限制/下一责任方：Remote-PS-C记录成功或失败并提交PR #11；同机隔离复验，非第二台实体电脑；Male5/Track9锁定，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时验收，Hardware-A/B不启动现场步骤。


### [PS-20261025-20] v3 完整 Release 与干净下载结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；基准/源码 ce4f2c7e9e7b3bc09b8c37532dbfb3f8d258c1bb；状态：交付 VERIFIED_GITHUB_DOWNLOAD_AND_INFERENCE，质量 REJECTED；PR #11。
- 授权/资产：沿用用户“授权在当前公开仓库发布完整模型包”；https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/model-PS-20261025-20-hubert-fargan-v3；附件 PS-20261025-20_hubert_fargan_v3_windows_cpu.zip，199369174 bytes，SHA 02d6a414f68d220916718dbaf6402ad8a73dd1d6d84a698151816353a19b76ae。标签指向精确源码，server digest/下载大小/SHA及466个内部文件全匹配；无WAV/语料/缓存，v1未改。
- 路径/复现：report/ps_20261025_20_github_model_receipt_v3_20261027.md/JSON/TXT（完整下载/校验/依赖/推理命令）；model_delivery_PS-20261025-20_hubert_fargan_v3_20261027.json（逐文件SHA）；独立新目录执行 build/remote_ps_c_hubert_fargan_v3.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe。状态/工作日志同步追加。
- 量化：干净GitHub下载推理exit0，2.563s/RTF0.140824176，封装49.830876s；16kHz mono PCM16/291200 samples，输出SHA d1fb89990a7c5cdc2a57174d1f1e0f5b5c3715239fd19c5e07594469c39cf703 与本轮五门原WAV完全相同，未重新评分。Python峰值工作集1113186304 bytes/pagefile2382503936 bytes，不含native子进程。
- 验证边界：发布/下载/校验/推理日志完整保留；独立venv复制锁定库，未测试新pip安装；同机隔离复验，非第二台实体电脑。
- 限制/下一责任方：身份0.763920106/P10 0.747006375/泄漏0.261376895/UTMOS2.508168141/CER0.558823529，泄漏/CER仍失败，非WAIT_LOCAL_TEST。Remote-PS-C保存证据，Hardware-A/B不启动试听/板测；Male5/Track9锁定，无录音/播放/真人/ARM/Vivado/RTL/PL/实时验收，未改分配/规则/可见性。
- 公开证据处理：自动审批阻止发布本机容量/绝对路径后，新增交付收据只保留通用项目路径；原始日志/容量检查留本地，模型/指标/哈希未变。
