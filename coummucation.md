# Agent 协作窗口

### [PS-20261021-10] 输出层源专用适配 Round 96 结果
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`890e283`
- 配置：Round88、train1～3、仅输出层、`1e-4`、100步、gain1.6。
- 量化结果：loss`.8404→.8154`；五门`.6975/.6843/.1168/2.2291/.2500`，泄漏、UTMOS、CER失败。
- 判定：冻结内容网络只恢复部分CER，输出层100步仍过强；继续更低剂量与教师子集消融。
- 修改/报告：`report/fixed_male_teacher_finetune_round96_20261029.{md,json}`、`coummucation.md`。
- 限制：录音5、Track9未使用，未播放、未接触板卡。
- 下一责任方：Hardware-A / Codex 继续Round97。

### [PS-20261021-10] 输出层源专用适配 Round 96 认领
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`99c480f`
- 唯一变量：冻结Round88输入层和两层GRU，只训练输出线性层100步；train1～3、`1e-4`、损失、gain1.6不变。
- 成功标准：五门全过；否则检验冻结内容网络能否避免Round94/95的CER和UTMOS退步。
- 限制：录音4开发评估；录音5、Track9锁定，未播放、未接触板卡。
- 下一责任方：Hardware-A / Codex 完成Round96。

### [PS-20261021-10] 源专用超低剂量微调 Round 95 结果
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`59e4bac`
- 配置：Round88、train1～3、全参数、`1e-4`、25步、gain1.6。
- 量化结果：loss `.8404→.7789`；五门`.6957/.6789/.1169/2.2371/.2941`，泄漏、UTMOS、CER失败。
- 判定：全模型低步数适配仍全面退步，停止该方向；Round96冻结内容网络，只训输出层。
- 修改/报告：`report/fixed_male_teacher_finetune_round95_20261029.{md,json}`、`coummucation.md`；复现使用已提交微调脚本。
- 限制：录音5、Track9未使用，未播放、未接触板卡。
- 下一责任方：Hardware-A / Codex 认领Round96输出层适配。

### [PS-20261021-10] 源专用超低剂量微调 Round 95 认领
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`50b1fa7`
- 唯一变量：相对Round94把全模型微调从100步降到25步；Round88基线、train1～3、学习率`1e-4`、损失、gain1.6和评估器不变。
- 成功标准：五门全过；否则要求UTMOS和CER不低于Round88且泄漏改善，才允许保留该剂量方向。
- 限制：录音4开发评估；录音5和Track9锁定，不播放、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成Round95训练评估并提交。

### [PS-20261021-10] 源专用教师低剂量微调 Round 94 结果
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`0201aee`
- 修改路径：`build/finetune_fixed_male_hubert_world_20261029.py`、`report/fixed_male_teacher_finetune_round94_20261029.{md,json}`、`coummucation.md`。
- 配置：Round88 checkpoint，train1～3，全部参数，学习率`1e-4`，100步，gain1.6；录音4严格评估。
- 量化结果：配对loss `.8404→.7274`；身份/P10/泄漏/UTMOS/CER=`.6864/.6758/.1001/2.1615/.2794`，泄漏、UTMOS、CER失败。
- 判定：拒绝。相对Round88仅泄漏略降，自然度和CER退步；Round95将适配剂量降至25步。
- 报告链接：`report/fixed_male_teacher_finetune_round94_20261029.md`、`report/fixed_male_teacher_finetune_round94_20261029.json`。
- 限制：录音4只用于开发评估；录音5、Track9未使用，未播放、未接触板卡。
- 下一责任方：Hardware-A / Codex 认领Round95低步数适配。

### [PS-20261021-10] 源专用教师低剂量微调 Round 94 认领
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`7f26744`
- 唯一变量：从Round88 checkpoint继续训练，仅用Round93三条固定男声→目标女声配对，AdamW学习率`1e-4`、100步；模型、损失、gain1.6和严格评估器保持不变。
- 成功标准：录音4五门全过；若未过，比较CER、泄漏和UTMOS相对Round88的方向，再决定Round95增加适配步数或止损。
- 限制：录音1～3用于训练，录音4只用于严格开发评估；录音5和Track9锁定，不播放、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成微调、录音4严格评估和单轮提交。

### [PS-20261021-10] 固定男声教师配对预检 Round 93 结果
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：ACCEPTED_PREFLIGHT
- 基准提交：`4a95ae9`
- 修改路径：`build/prepare_fixed_male_teacher_pairs_20261029.py`、`report/fixed_male_teacher_pairs_round93_20261029.{md,json}`、`coummucation.md`。
- 复现命令：使用冻结教师generation.json运行配对缓存脚本；输出位于忽略目录`build/generated/fixed_male_teacher_pairs_20261029/`。
- 量化结果：train1/2/3均为样本数严格一致、901/837/975个20ms帧且可裁128帧；最佳能量时移`+5/0/0 ms`，相关`.8839/.8815/.9288`。教师对源ASR micro CER `.2190`，内容监督有噪声。
- 判定：配对与时序预检通过，允许Round94低剂量源专用微调；教师内容不完美，后续必须以录音4严格五门止损。
- 报告链接：`report/fixed_male_teacher_pairs_round93_20261029.md`、`report/fixed_male_teacher_pairs_round93_20261029.json`。
- 限制：未使用录音4/5或Track9，未播放、未接触板卡。
- 下一责任方：Hardware-A / Codex 认领Round94，对Round88 checkpoint执行低剂量源专用微调。

### [PS-20261021-10] 固定男声教师配对预检 Round 93 认领
- 日期：2026-10-29
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`1c77a80`
- 范围：承接远端已完成的 Round92 和教师资产恢复证据，核验录音1～3与原生 CosyVoice3 教师输出的SHA、时长、HuBERT/WORLD帧数和局部时序对齐，并建立源专用训练缓存。
- 成功标准：三对资产校验通过、特征有限、帧数一致且可形成至少一个完整训练crop；若教师局部对齐或内容证据不支持训练，则本批在预检处止损并如实报告。
- 限制：只读取固定男声训练录音1～3及其教师输出；不使用录音4/5或Track9，不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成Round93预检并单独提交，再按结果认领Round94。

### [PS-20261021-10] 源清浊时序融合 Round 56 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED / USER_STOP
- 基准提交：`2fef469`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/fixed_male_source_vuv_round56_20261026.{md,json}`、`coummucation.md`。
- 复现命令：冻结 Round37 checkpoint 与 gain1.6，在录音4运行 `--source-vuv-alphas 0 0.25 0.5 0.75 1.0 --experiment-round 56`，再运行严格评估器。
- 量化结果：alpha0/0.25/0.5/0.75/1.0 的身份为 `.6946/.6954/.7013/.7013/.7013`，泄漏为 `.1046/.1138/.1171/.1171/.1171`，UTMOS为 `2.2746/2.2283/2.3003/2.3003/2.3003`，CER为 `.2500/.3971/.2647/.2647/.2647`；五门均未全过，alpha0.5/0.75/1.0输出PCM完全相同。
- 判定：拒绝。源VUV既未降低CER又增加源泄漏，严格选择仍是alpha0；录音5保持锁定。
- 报告链接：`report/fixed_male_source_vuv_round56_20261026.md`、`report/fixed_male_source_vuv_round56_20261026.json`。
- 限制：只使用录音4；未播放、未录音、未接触板卡。用户要求本轮完成后停止，因此Round57未认领、未启动。
- 下一责任方：暂停，等待用户后续指令。

### [PS-20261021-10] 源清浊时序融合 Round 56 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`b832fe8`
- 唯一变量：冻结 Round51 的 gain1.6 和全部目标谱/F0/AP，只把模型预测VUV概率与源WORLD VUV按 `0/0.25/0.5/0.75/1.0` 融合，测试源清浊边界能否改善辅音与CER；不注入源谱或源音高。
- 成功标准：录音4严格身份 `>=0.45`、P10 `>=0.35`、泄漏 `<=0.10`、UTMOS `>=2.30`、CER `<=0.15` 全过；只有全过才允许下一轮打开锁定录音5。
- 限制：不使用录音5或 Track 9，不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 实现VUV单变量网格并独立提交结果。

### [PS-20261021-10] 零均值源谱动态残差 Round 55 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`26a31ad496dddfff26c4f396771bb8cec4c3aff0`
- 唯一变量：冻结 Round51 的 gain1.6，在固定男性 validation 录音4上把源 WORLD 谱 DCT `8:60` 去除逐维时间均值后的动态残差按 `0/0.1/0.2/0.3/0.4` 注入；不注入男性平均谱、F0、能量或AP。
- 选择门：按身份/P10/泄漏/UTMOS/CER五门最小比例排序；只有五门全过才允许 Round56 打开锁定录音5。
- 限制：只使用录音4选参，不使用录音5或 Track 9；不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成固定残差比例网格并单独提交。

### [PS-20261021-10] Round43 跨句 F0 收益归因 Round 45 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`9c42263ea3aa12898ad451f3c00915e816f039c4`
- 范围：承接既有 44 轮，从 Round37/Round43 的同一 8 条独立验证证据分析逐句、逐说话人 F0 动态误差与 UTMOS 收益方向；本次新增轮次固定编号为 Round 45～54，达到客观可用门则提前停止。
- 唯一变量：本轮只做归因，不训练、不改变 checkpoint；不得继续扫描更大 F0 权重。
- 判定：只有能在两个验证说话人上同向解释 UTMOS 差异的归一化/误差项，才允许进入下一训练轮；否则回到 Round37 并优先研究非 F0 参数协同。
- 限制：不使用固定男性锁定句或 Track 9 选参，不播放、不录音、不接触板卡；板卡可保持关机。
- 下一责任方：Hardware-A / Codex 完成 Round45 报告并单独提交；随后按结论认领 Round46。

### [PS-20261021-10] Round43 跨句 F0 收益归因 Round 45 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：NO_GO_F0_NORMALIZATION
- 基准提交：`aa6dcad`
- 修改路径：`report/round43_f0_gain_attribution_round45_20261026.{md,json}`、`coummucation.md`。
- 量化结果：Round43 相对 Round37 的 UTMOS 在 `SSB0434/SSB0080` 上分别为 `-0.04219/+0.03868`；UTMOS 增量与 F0 标准差/动态比更接近教师的相关系数为 `-0.4296/-0.6819`，不存在跨说话人同向解释。
- 判定：禁止继续扫描 F0 权重或加入说话人/句子自适应 F0 归一化；回退 Round37，Round46 研究验证集选择的可部署非 F0 参数协同后处理。
- 限制：未训练、推理、合成或重新使用 Track 9；未使用固定男性输入、未播放，板卡保持关机。
- 报告链接：`report/round43_f0_gain_attribution_round45_20261026.md`、`report/round43_f0_gain_attribution_round45_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round45；另行认领 Round46 单变量后处理验证。

### [PS-20261021-10] 非 F0 时间对比度后滤波 Round 46 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`7e4b22e`
- 唯一变量：冻结 Round37 checkpoint，只对预测的谱/能量/AP 三组相对各句时间均值的偏差施加同一个增益；log-F0、VUV、模型和合成器不变。
- 选择集与门：只用原8条独立 validation 句比较固定网格 `1.0/1.1/1.2/1.3/1.4`；候选必须总体 UTMOS 提高且两个验证说话人都不退步，才允许 Round47 在 Track 9 单次回归。
- 限制：不使用 Track 9、固定男性锁定句、真人试听或板卡；这是推理后处理探索，不宣称已经可用。
- 下一责任方：Hardware-A / Codex 实现并运行验证网格，失败也单独提交。

### [PS-20261021-10] 非 F0 时间对比度后滤波 Round 46 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：GO_GAIN_1_4
- 基准提交：`a57b54d`
- 修改路径：`build/sweep_world_temporal_postfilter_round46_20261026.py`、`report/world_temporal_postfilter_round46_20261026.{md,json}`、`coummucation.md`。
- 量化结果：8句 UTMOS 从 gain1.0 的 `2.0055` 单调升至 gain1.4 的 `2.4082`；`SSB0080/SSB0434` 分别提升 `+0.4166/+0.3889`，通过两个说话人均不退步门。
- 判定：冻结 gain `1.4`，不扩展验证网格；Round47 仅在 Track 9 做一次严格身份/P10/UTMOS/CER回归。
- 限制：未使用 Track 9 或固定男性输入；未播放、录音或接触板卡，尚未宣称保底可用。
- 报告链接：`report/world_temporal_postfilter_round46_20261026.md`、`report/world_temporal_postfilter_round46_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round46；另行认领 Round47 冻结留出回归。

### [PS-20261021-10] gain1.4 冻结 Track 9 回归 Round 47 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线测试）
- 状态：CLAIMED
- 基准提交：`cea7c0c`
- 唯一变量：把 Round46 已冻结的非 F0 时间对比度 gain `1.4` 应用于 Round37 的 Track 9 重建；不得调整增益或其他参数。
- 验收：用既定严格评估器报告身份、P10、UTMOS、CER；目标自重建不应用男性泄漏门。四项全部过门才允许进入固定男性转换，否则保留证据并继续 Round48。
- 限制：Track 9 仅作冻结后一次回归，不参与训练或重新选参；不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 合成并严格评测，单独提交结果。

### [PS-20261021-10] gain1.4 冻结 Track 9 回归 Round 47 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线测试）
- 状态：REJECTED_BEST_SO_FAR
- 基准提交：`ed10a65`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/world_temporal_postfilter_track9_round47_20261026.{md,json}`、`coummucation.md`。
- 量化结果：Round37 基线逐位一致；gain1.4 的身份/P10/UTMOS/CER 为 `0.7138/0.6973/2.2853/0.0978`，UTMOS 相对基线 `+0.4237` 但距门槛仍差 `0.0147`。
- 判定：身份、P10、CER 通过，UTMOS 未过；不进入固定男性转换。目标自重建不应用男性泄漏门。
- 限制：Track 9 只在冻结后使用一次；未使用固定男性输入、未播放、录音或接触板卡。候选合成前峰值 `2.0804`，下一轮回到 validation 研究限制策略。
- 报告链接：`report/world_temporal_postfilter_track9_round47_20261026.md`、`report/world_temporal_postfilter_track9_round47_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round47；另行认领 Round48 峰值策略验证。

### [PS-20261021-10] 峰值限制可归因性 Round 48 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：CLAIMED
- 基准提交：`52ccc7e`
- 范围：审计 `synthesize()` 的峰值限制和严格 UTMOS 输入归一化，判断 Round47 的 `peak_before_limit=2.0804` 是否会造成波形失真或可通过换限制器提升指标。
- 判定：只有现有限制器改变相对波形或与评估归一化不等价时，才允许尝试限制策略；若只是全局线性缩放，则 NO-GO，下一轮回 validation 扩展冻结增益网格。
- 限制：只读代码与既有证据，不训练、不合成、不使用 Track 9 新结果、固定男性输入、播放或板卡。
- 下一责任方：Hardware-A / Codex 完成数学与代码路径核对并单独提交。

### [PS-20261021-10] 峰值限制可归因性 Round 48 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线诊断）
- 状态：NO_GO_LIMITER_TUNING
- 基准提交：`a443ee7`
- 修改路径：`report/world_peak_limiter_audit_round48_20261026.{md,json}`、`coummucation.md`。
- 量化/代码结果：合成器只做全局 `0.98/peak` 线性缩放；UTMOS 前处理再归一到 RMS `0.04`，正比例增益严格抵消，预期 UTMOS 改变量为 `0`。
- 判定：不调峰值限制器；Round49 回到原8条 validation，预声明扩展 gain `1.5～1.8`，仍执行两个说话人均不退步门。
- 限制：只读代码与既有证据；没有训练、合成新音频或重新使用 Track 9，未用固定男性输入、播放或板卡。
- 报告链接：`report/world_peak_limiter_audit_round48_20261026.md`、`report/world_peak_limiter_audit_round48_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round48；另行认领 Round49 扩展增益验证。

### [PS-20261021-10] 非 F0 增益扩展验证 Round 49 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`2040f3b`
- 唯一变量：保持 Round46 全部流程，只把预声明验证增益扩展为 `1.5/1.6/1.7/1.8`，并保留 `1.0/1.4` 对照；不改变参数组、checkpoint、评估器或选择规则。
- 选择门：总体 UTMOS 最大且 `SSB0080/SSB0434` 都不低于1.0基线；若最优仍位于1.8边界，本阶段停止继续外推，避免无限追涨。
- 限制：只用8条 validation 选参，不使用 Track 9 或固定男性输入，不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 跑完整固定网格并单独提交。

### [PS-20261021-10] 非 F0 增益扩展验证 Round 49 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：GO_GAIN_1_6
- 基准提交：`7970f5e`
- 修改路径：`build/sweep_world_temporal_postfilter_round46_20261026.py`、`report/world_temporal_gain_extension_round49_20261026.{md,json}`、`coummucation.md`。
- 量化结果：gain1.6 的8句 UTMOS 为 `2.4833`，`SSB0080/SSB0434=2.6352/2.3314`；1.7和1.8总体回落，1.6是内部最优。
- 判定：冻结 gain `1.6`，停止外推；Round50 在 Track 9 做一次严格回归。
- 限制：未使用 Track 9 或固定男性输入；未播放、录音或接触板卡。
- 报告链接：`report/world_temporal_gain_extension_round49_20261026.md`、`report/world_temporal_gain_extension_round49_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round49；另行认领 Round50 冻结留出回归。

### [PS-20261021-10] gain1.6 冻结 Track 9 回归 Round 50 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线测试）
- 状态：CLAIMED
- 基准提交：`d728aba`
- 唯一变量：使用 Round49 已冻结 gain `1.6` 替换 Round47 的 `1.4`；Round37 checkpoint、参数组、Track 9、合成与严格评估全部不变。
- 验收：目标自重建身份≥0.45、P10≥0.35、UTMOS≥2.30、CER≤0.15；全部通过才允许 Round51 转换固定男性 validation 录音4。
- 限制：不再根据 Track 9 调参；目标自重建不应用男性泄漏门。不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成一次冻结回归并单独提交。

### [PS-20261021-10] gain1.6 冻结 Track 9 回归 Round 50 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线测试）
- 状态：PASS_TARGET_RECONSTRUCTION
- 基准提交：`6b32195`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/world_temporal_gain_track9_round50_20261026.{md,json}`、`coummucation.md`。
- 量化结果：身份/P10/男性质心余弦/UTMOS/CER=`0.6847/0.6643/0.0863/2.3814/0.1087`；目标重建适用四门全部通过，基线逐位一致。
- 判定：目标参数预测与WORLD合成链首次达到电脑端门；Round51 冻结同一候选转换固定男性 validation 录音4，届时男性泄漏门正式适用。
- 限制：本轮不是固定男性转换，不能宣称保底方案已通过；未播放、录音或接触板卡。
- 报告链接：`report/world_temporal_gain_track9_round50_20261026.md`、`report/world_temporal_gain_track9_round50_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round50；另行认领 Round51 固定男性 validation 转换。

### [PS-20261021-10] 固定男性 validation 转换 Round 51 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线测试）
- 状态：CLAIMED
- 基准提交：`394ffbb`
- 唯一变量：输入从目标 Track 9 改为冻结的 `人物音频资料/男声/标准录音 4.wav`；Round37 checkpoint、gain1.6、目标锚点、合成器和严格评估器全部不变。
- 验收：正式应用身份≥0.45、P10≥0.35、男性泄漏≤0.10、UTMOS≥2.30、CER≤0.15五门；全部通过才允许 Round52 使用锁定录音5。
- 限制：录音4是 validation，不得据其结果重新调 gain；不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成固定男性 validation 文件转换并单独提交。

### [PS-20261021-10] 固定男性 validation 转换 Round 51 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线测试）
- 状态：REJECTED_CONTENT
- 基准提交：`5600cda`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/fixed_male_validation_round51_20261026.{md,json}`、`coummucation.md`。
- 量化结果：录音4身份/P10/泄漏/UTMOS/CER=`0.6946/0.6766/0.1046/2.2746/0.2500`；身份两门通过，泄漏和UTMOS轻微未过，CER明显未过。
- 判定：不得进入锁定录音5或试听；Round52 仅在录音4上选择固定男性专用 gain，按五门最小比例而非单项最高值决定。
- 限制：未使用 Track 9 或锁定录音5；未播放、录音或接触板卡。
- 报告链接：`report/fixed_male_validation_round51_20261026.md`、`report/fixed_male_validation_round51_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round51；另行认领 Round52 固定男性 validation gain 选择。

### [PS-20261021-10] 固定男性专用 gain 选择 Round 52 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`65e0549`
- 唯一变量：固定男性 validation 录音4上比较同一非 F0 后滤波的 gain `1.0/1.2/1.4/1.6/1.8`；checkpoint、参数组、目标锚点、合成器和评估器不变。
- 选择门：先按五门最小达成比例，再按平均达成比例排序；只有五门全过才允许 Round53 打开锁定录音5。网格完成后不再插值或外推。
- 限制：只使用录音4选固定男性专用配置；不使用录音5、Track 9、播放、录音或板卡。
- 下一责任方：Hardware-A / Codex 完成固定网格与严格评测并单独提交。

### [PS-20261021-10] 固定男性专用 gain 选择 Round 52 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_GAIN_ONLY
- 基准提交：`d19fa04`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/fixed_male_gain_sweep_round52_20261026.{md,json}`、`coummucation.md`。
- 量化结果：gain1.4 的 UTMOS `2.3109` 通过但泄漏/CER=`0.1306/0.25` 失败；gain1.8 是唯一泄漏通过点 `0.0960`，但 UTMOS/CER=`2.2371/0.3382` 失败。无候选五门全过。
- 判定：停止 gain-only 路线；Round53 冻结 gain1.8，只扫描源高阶谱 DCT `20:60` 的细节注入比例 `0～0.4`，针对CER且保留低阶目标音色。
- 限制：只用录音4，未使用录音5或 Track 9；未播放、录音或接触板卡。
- 报告链接：`report/fixed_male_gain_sweep_round52_20261026.md`、`report/fixed_male_gain_sweep_round52_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round52；另行认领 Round53 高阶谱细节验证。

### [PS-20261021-10] 源高阶谱细节注入 Round 53 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`0432a9d`
- 唯一变量：冻结 gain1.8，只把录音4源 WORLD 谱 DCT 高阶 `20:60` 按 `0/0.1/0.2/0.3/0.4` 比例注入预测；目标低阶谱 `0:20`、log-F0、VUV、能量、AP、checkpoint和评估器不变。
- 选择门：五门最小达成比例优先；只有身份/P10/泄漏/UTMOS/CER全过才允许最后 Round54 打开锁定录音5，否则 Round54 记录10轮停止结论而不污染锁定集。
- 限制：只用录音4选参，不使用录音5或 Track 9；不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成固定细节网格并单独提交。

### [PS-20261021-10] 源高阶谱细节注入 Round 53 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_HIGH_ORDER_DETAIL
- 基准提交：`5b88ca4`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/fixed_male_source_detail_round53_20261026.{md,json}`、`coummucation.md`。
- 量化结果：alpha0.2 的身份/P10/泄漏/UTMOS/CER=`0.6506/0.6252/0.0920/2.2579/0.3235`；alpha0.4 UTMOS最高 `2.2849`、泄漏 `0.0881`，但CER `0.3382`。
- 判定：高阶20:60细节不解决内容门；Round54 冻结 gain1.8/alpha0.4，仅把谱注入起点比较 `20/16/12/8`，然后结束本批10轮。
- 限制：只用录音4，未使用录音5或 Track 9；未播放、录音或接触板卡。
- 报告链接：`report/fixed_male_source_detail_round53_20261026.md`、`report/fixed_male_source_detail_round53_20261026.json`。
- 下一责任方：Hardware-A / Codex 提交 Round53；另行认领本批最后 Round54 中阶谱验证。

### [PS-20261021-10] 源中阶谱细节注入 Round 54 认领
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`8f1cb04`
- 唯一变量：冻结 gain1.8 和 source-detail alpha0.4，只比较谱 DCT 注入起点 `20/16/12/8`，终点均为60；其余参数及评估器不变。
- 选择/停止门：仍按五门最小比例；若五门全过，候选仅获得打开锁定录音5的资格；否则不打开录音5。本轮是本批 Round45～54 的第10轮，结果提交后停止继续试参。
- 限制：只用录音4，不使用录音5或 Track 9；不播放、不录音、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成固定网格、提交本轮和十轮总结。

### [PS-20261021-10] 源中阶谱细节注入 Round 54 与十轮结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED_BATCH_STOP
- 基准提交：`7ca75db`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/fixed_male_spectral_cutoff_round54_20261026.{md,json}`、`report/fallback_rounds_45_54_summary_20261026.json`、`coummucation.md`。
- 量化结果：Round54 cutoff16 最佳为身份/P10/泄漏/UTMOS/CER=`0.6441/0.6276/0.0974/2.2640/0.2941`，身份/P10/泄漏通过，UTMOS/CER失败；cutoff继续下移无过门趋势。
- 十轮结论：Round45～54已全部完成。Round50 使目标Track9重建首次四门全过，但固定男性 validation 的最佳CER仍 `0.2941`；未达到“能用”，不打开锁定录音5、不请求试听、不启动Cortex-A9/PL/板卡。
- 限制：本批只做电脑端离线诊断/测试；未播放、录音或接触板卡，录音5保持锁定。
- 报告链接：`report/fixed_male_spectral_cutoff_round54_20261026.md`、`report/fixed_male_spectral_cutoff_round54_20261026.json`、`report/fallback_rounds_45_54_summary_20261026.json`。
- 下一责任方：Maintainer/用户审核本批；若继续，应新认领内容保持机制，不再扫描 gain、F0权重或谱注入比例。

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

### [PS-20261021-10] 零均值源谱动态残差 Round 55 结果
- 日期：2026-10-26
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`47667df`
- 修改路径：`build/apply_world_temporal_postfilter_round47_20261026.py`、`report/fixed_male_centered_residual_round55_20261026.{md,json}`、`coummucation.md`。
- 复现命令：在 Round37 checkpoint 与 Round25 cache 上运行后滤波脚本，固定 gain1.6，参数 `--source-residual-alphas 0 0.1 0.2 0.3 0.4 --source-residual-cutoff 8 --source-relative 人物音频资料/男声/标准录音 4.wav`，再运行严格评估器。
- 量化结果：alpha0.0/0.1/0.2/0.3/0.4 的身份为 `.6946/.6976/.7001/.7037/.7059`，泄漏为 `.1046/.1101/.1131/.1197/.1214`，UTMOS为 `2.2746/2.3042/2.3390/2.3722/2.3991`，CER为 `.2500/.2500/.3235/.3088/.2941`；五门均未全过。
- 判定：拒绝。中心化谱残差可提高身份和自然度，但单调增加源泄漏且未修复内容；录音5保持锁定。
- 报告链接：`report/fixed_male_centered_residual_round55_20261026.md`、`report/fixed_male_centered_residual_round55_20261026.json`。
- 限制：只使用录音4；未使用录音5或 Track 9，未播放、未录音、未接触板卡。
- 下一责任方：Hardware-A / Codex 在 Round56 只测试源VUV时序融合，判断清辅音边界能否降低CER且不引入音色谱。

### [PS-20261021-10] HuBERT/WORLD Round 69 结果
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`6998adb9683e2c13d37f4acb80b116f91cc7dfe7`
- 唯一变量：多尺度动态损失权重由 0.75 改为 1.65；固定种子 20261025、2000 步、source prosody、variance matching、锚点概率 0.25 和 gain 1.6。
- 输入：仅男声标准录音 4 验证，SHA-256 `f4a026e5c97f3bf25447876101dce71a6a160e8ebc81b9b488c7d3a41c62d68c`；配对缓存清单 SHA-256 `4d34669259834bd30219f34af4730712c9aa7c4cf8fa8bc3c5ccde9ee3cc5bc5`。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7054/0.6786/0.1037/2.3743/0.2206`；泄漏与 CER 未过门。Checkpoint SHA-256 `3a045e8571e77eedacf0b408ccfb9395b1bf212bf221956a8202288dad552cca`；候选 PCM16 SHA-256 `c33eb00a6bf4d49de3d465dc729b562ac1143ac633675f855deda357411765d6`。
- 修改路径：`build/train_paired_hubert_world_gru_round26_20261025.py`、`report/fixed_male_hubert_world_round69_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round69_20261027.json`；训练入口支持 `--multiscale-weight`，并以 `--skip-locked-target-regression` 在保存 checkpoint 后停止。
- 限制：严格评估注入 identity OpenCC shim，源 Whisper 转写也有识别错误；录音 5 与 Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round69_20261027.md`、`report/fixed_male_hubert_world_round69_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续调整同一电脑端方案并逐轮评估。

### [PS-20261021-10] HuBERT/WORLD Round 70 结果
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`726a0318f5ce7e6daa969afee9453c9b112fe8a3`
- 唯一变量：多尺度动态损失权重由 Round69 的 1.65 改为 1.70；其他训练参数、录音4验证、gain1.6 和评估器不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7009/0.6733/0.1046/2.3363/0.2647`；泄漏与 CER 未过门。Checkpoint SHA-256 `a297ea51273b137f0a65924d6c4cbc092f6a253da83b8373cb6fac23ca20f236`；候选 PCM16 SHA-256 `a4ffd96e0c41a3dffc6cc8560a22c8dd936fc99b296219518bb5a504bd6598ae`。
- 修改路径：`report/fixed_male_hubert_world_round70_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round70_20261027.json`。
- 限制：严格评估使用 identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round70_20261027.md`、`report/fixed_male_hubert_world_round70_20261027.json`。
- 下一责任方：Hardware-A / Codex 在 Round71 测试回落权重并继续逐轮评估。

### [PS-20261021-10] HuBERT/WORLD Round 71 结果
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`647548bd4040a803d00a477c0a77fdfc9d4ce255`
- 唯一变量：多尺度动态损失权重为 1.55；2000 步、固定种子、source prosody、variance matching、gain1.6 和评估器不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7055/0.6785/0.1088/2.3419/0.2647`；泄漏与 CER 未过门。Checkpoint SHA-256 `4b28e786c853ed4237d5cdb17a700c0e79df736d24249cc65824ef0e80c42d88`；候选 PCM16 SHA-256 `734ded9562ea37a8c766218198f9f812e03bcac1c5e966946db4c1bea87a5133`。
- 修改路径：`report/fixed_male_hubert_world_round71_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round71_20261027.json`。
- 限制：严格评估使用 identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round71_20261027.md`、`report/fixed_male_hubert_world_round71_20261027.json`。
- 下一责任方：Hardware-A / Codex 测试 Round69-71 权重之间的低端区间。

### [PS-20261021-10] HuBERT/WORLD Round 72 结果
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`5ed22b20a57df1168d19c4c4a864df4bcb3dbfa4`
- 唯一变量：多尺度动态损失权重为 1.45；2000 步、固定种子、source prosody、variance matching、gain1.6 和评估器不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7045/0.6792/0.1028/2.3635/0.2647`；泄漏与 CER 未过门。Checkpoint SHA-256 `8cc81ef4e25ca63c7d1df36a64bf737ffaa53cd7fef9564a05fc2156f9fadd4b`；候选 PCM16 SHA-256 `03c4e244c53dd9c46065796c006fd9d1bf6ecbb7025a13f6649ba52d7c051394`。
- 修改路径：`report/fixed_male_hubert_world_round72_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round72_20261027.json`。
- 限制：严格评估使用 identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round72_20261027.md`、`report/fixed_male_hubert_world_round72_20261027.json`。
- 下一责任方：Hardware-A / Codex 用 Round69 checkpoint 验证目标减漏方向，不再连续扫描相邻训练权重。

### [PS-20261021-10] HuBERT/WORLD Round 73 后滤波验证
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`a0fe2000c9486e335aff17f00ae6e6c9244e3da6`
- 唯一变量：Round69 checkpoint 的非 F0 动态后滤波 gain 从 1.6 降至 1.5；这是已暴露录音4的单轮客观回归，不产生新 checkpoint。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7224/0.7013/0.1133/2.3663/0.2206`；泄漏与 CER 未过门。Checkpoint SHA-256 `3a045e8571e77eedacf0b408ccfb9395b1bf212bf221956a8202288dad552cca`；候选 SHA-256 `0a24d19c018b155546131ab962032fe0f5d9d591c4ee32cebd8b08ad9a339ba2`。
- 修改路径：`report/fixed_male_hubert_world_round73_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round73_20261027.json`。
- 限制：使用 identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round73_20261027.md`、`report/fixed_male_hubert_world_round73_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续 PS 方案探索。

### [PS-20261021-10] HuBERT/WORLD Round 74 后滤波验证
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`91e513c0e9e48a56a13a4d5b58f1cbb7ac301c47`
- 唯一变量：Round69 checkpoint 的非 F0 后滤波 gain 由 1.6 降至 1.3。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7450/0.7298/0.1355/2.2570/0.3824`；仅身份两门通过，其他三门失败。Checkpoint SHA-256 `3a045e8571e77eedacf0b408ccfb9395b1bf212bf221956a8202288dad552cca`；候选 SHA-256 `23d30e3e30f1dd22ef5308c68a1074ba3d09356c4d0e3f4932049b5eee173ac5`。
- 修改路径：`report/fixed_male_hubert_world_round74_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round74_20261027.json`。
- 限制：identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round74_20261027.md`、`report/fixed_male_hubert_world_round74_20261027.json`。
- 下一责任方：Hardware-A / Codex 改变训练数据的目标锚点比例。

### [PS-20261021-10] HuBERT/WORLD Round 75 目标锚点比例
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`ccc53f98a0519b14b5089f4b63b3ad3ee39a6bf7`
- 唯一变量：目标自重建锚点采样概率由 0.25 降至 0.15；动态权重 1.25、固定种子和其他结构不变。验证 early stopping 在 step1200 选 checkpoint，训练历史到 step1600 停止。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.6839/0.6559/0.1117/2.3876/0.5000`；泄漏与 CER 未过门。Checkpoint SHA-256 `da359e8caa8a03f27211cd1fc02a2a509e2fad50e44565365c98649c24af6104`；候选 PCM16 SHA-256 `23b61c5ebbab4b4a16170baca47d44f812f4e301ca8fa618d7ef878531f51623`。
- 修改路径：`report/fixed_male_hubert_world_round75_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round75_20261027.json`；本轮锚点概率为训练运行时改写为 0.15。
- 限制：identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round75_20261027.md`、`report/fixed_male_hubert_world_round75_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续电脑端固定男性方案探索。

### [PS-20261021-10] HuBERT/WORLD Round 76 移除源韵律
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`1c1dced5ddf6d8179338f50ea28a52e4cf4311dd`
- 唯一变量：从 Round37 衍生配置中移除 source prosody 输入；动态损失权重 1.25、锚点概率 0.25、固定种子、gain1.6 不变；验证 early stopping 在 step1400 停止。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.6860/0.6648/0.1611/2.1773/0.4118`；源泄漏、UTMOS、CER 失败。Checkpoint SHA-256 `6d3c276ad5345a0ea5302191476ba446d95615d7ba41e4174582c63b58d36cb8`；候选 PCM16 SHA-256 `b2a7afe0414eba2a0e4a2c5fb46259c70de38927d9fa97f2eabf2f2497ed964b`。
- 修改路径：`report/fixed_male_hubert_world_round76_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round76_20261027.json`。
- 限制：identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round76_20261027.md`、`report/fixed_male_hubert_world_round76_20261027.json`。
- 下一责任方：Hardware-A / Codex 保留 source prosody、测试移除 variance matching。

### [PS-20261021-10] HuBERT/WORLD Round 77 移除方差匹配
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`629a65dc45cd22ae07225fa26634885f4e853078`
- 唯一变量：保留 source prosody，移除 variance matching；动态损失权重1.25、锚点概率0.25、固定种子与gain1.6不变；step1600 early stop。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.6987/0.6740/0.1451/2.2132/0.3971`；泄漏、UTMOS、CER失败。Checkpoint SHA-256 `e71e7999dda6f0d2c86dd626bb1eb91b12322467b39741b46f3d5a98a60d2433`；候选 PCM16 SHA-256 `108895adf5b6e2b7ad56565671083fe649b1d4d8601dc2ea46dfd509e07e90ac`。
- 修改路径：`report/fixed_male_hubert_world_round77_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round77_20261027.json`。
- 限制：identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round77_20261027.md`、`report/fixed_male_hubert_world_round77_20261027.json`。
- 下一责任方：Hardware-A / Codex 保留 source prosody 与 variance matching，测试独立的 VUV BCE 权重变化。

### [PS-20261021-10] HuBERT/WORLD Round 78 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`e6d0c57fa4a08fb73d48d6f58d85a8b477d0d726`
- 唯一变量：VUV BCE 系数由0.35升至0.70；保留 source prosody 和 variance matching，动态权重1.25、锚点0.25、gain1.6不变；step1600 early stop。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.6967/0.6721/0.1134/2.3254/0.2794`；源泄漏与 CER 未过门。Checkpoint SHA-256 `f3ebc219a32883027d26b2f1f6818545159e67351adc74d306006b0867fc891c`；候选 PCM16 SHA-256 `b2082fca1f4d73f2324085a7a54bb57903b8f3c66ae988089102a6399866ba31`。
- 修改路径：`report/fixed_male_hubert_world_round78_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round78_20261027.json`。
- 限制：identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round78_20261027.md`、`report/fixed_male_hubert_world_round78_20261027.json`。
- 下一责任方：Hardware-A / Codex 测试降低 VUV BCE 权重。

### [PS-20261021-10] HuBERT/WORLD Round 79 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`b2a26fa971cca004adbcf5aad3d650f9bcbfe94a`
- 唯一变量：VUV BCE 系数由0.35降至0.15；其余训练结构、source prosody、variance matching、动态权重1.25、锚点概率0.25与gain1.6不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7080/0.6891/0.1088/2.3807/0.4412`；泄漏与 CER 未过门。Checkpoint SHA-256 `257cb1d3fa86ab61adffe06ab9258105c38384442d73addfb19f180c244fa131`；候选 PCM16 SHA-256 `4ae7617ee724798347f7528048b9d7dabac7307b2a67f6edd3c0e9712c94fcbf`。
- 修改路径：`report/fixed_male_hubert_world_round79_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round79_20261027.json`。
- 限制：identity OpenCC shim；录音5、Track 9 未用于选参；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL 或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round79_20261027.md`、`report/fixed_male_hubert_world_round79_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续围绕保留源韵律条件的模型改进低泄漏与CER。

### [PS-20261021-10] HuBERT/WORLD Round 80 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`05f07ba`
- 唯一变量：以 Round79 的 VUV BCE 系数0.15为基准，仅提高至0.50；source prosody、variance matching、动态权重1.25、锚点概率0.25、gain1.6、随机种子和早停策略保持不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7022/0.6817/0.1142/2.3071/0.2353`；泄漏高于门槛0.0142，CER高于门槛0.0853。检查点训练2000 step，最佳验证step1200；checkpoint SHA-256 `de268f4a915970f8dbe0298696301cd0b88dded3160eefbaffa27bde68d8a9ca`；候选 PCM16 SHA-256 `ee897bca071686a624f5631a0322238b0d1988cc9f7452900bdbb85d1d0b4c91`。
- 修改路径：`report/fixed_male_hubert_world_round80_20261027.{md,json}`、`coummucation.md`。
- 复现命令：见 `report/fixed_male_hubert_world_round80_20261027.json`；运行时训练脚本唯一系数改动及SHA亦记录在报告中。
- 限制：identity OpenCC shim不执行简繁转换；CPU训练启动器虽写出并通过独立检查的checkpoint，但最后返回码为1；录音5和Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round80_20261027.md`、`report/fixed_male_hubert_world_round80_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续测试 VUV BCE 系数0.40，以在0.15、0.50、0.70之间收窄低CER与低泄漏的折中区间。

### [PS-20261021-10] HuBERT/WORLD Round 81 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`ca86719`
- 唯一变量：以 Round80 的 VUV BCE 系数0.50为基准，仅降低至0.40；source prosody、variance matching、动态权重1.25、锚点概率0.25、gain1.6、随机种子和早停策略保持不变。
- 成功标准：固定录音4严格身份均值≥0.45、P10≥0.35、源泄漏≤0.10、UTMOS≥2.30、CER≤0.15五门全部通过；通过后立即停止算法训练并转入本地验证门。
- 数据边界：只用男性标准录音4评估；训练仍限男性录音1～3及目标Track5～8；锁定录音5和Track9不得用于训练、选参、早停或筛选。
- 复现入口：`build/train_paired_hubert_world_gru_round26_20261025.py`、`build/apply_world_temporal_postfilter_round47_20261026.py`、`build/evaluate_seed_fixed_male_strict_20261024.py`；结果报告记录缓存与资产SHA及严格评测命令。
- 限制：identity OpenCC shim的简繁归一化有限；不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮训练、严格评估并提交单轮结果。

### [PS-20261021-10] HuBERT/WORLD Round 85 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`d6bbebf`
- 唯一变量：冻结Round82配置，仅将训练VUV BCE系数由0.30改为0.35；其余参数不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.6997/0.6769/0.0996/2.2724/0.2647`；身份、P10、泄漏通过，UTMOS与CER失败。检查点SHA-256 `f3fa1f9b5619ed79fc204ebc8e6e731363a4cec99d165ed60e4238f7e01c45e2`；候选SHA-256 `43fc85bcff9b5973dfe8be8168584b088ac9faff35703cfd8a0db513c752505b`。
- 修改路径：`report/fixed_male_hubert_world_round85_20261027.{md,json}`、`coummucation.md`。
- 限制：identity OpenCC shim；录音5、Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round85_20261027.md`、`report/fixed_male_hubert_world_round85_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续测试不注入源VUV的内容保持变量。

### [PS-20261021-10] HuBERT/WORLD Round 86 源谱动态残差后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`4160ab9`
- 唯一变量：冻结Round85 checkpoint与gain1.6，仅把录音4源WORLD谱DCT动态残差按alpha=0.05注入；不注入源VUV、音高、能量或AP，不重训。
- 成功标准：固定录音4严格身份均值≥0.45、P10≥0.35、源泄漏≤0.10、UTMOS≥2.30、CER≤0.15五门全部通过；否则记录并拒绝。
- 数据边界：只用男性标准录音4评估；Track9和录音5继续锁定，不用于选择或训练。
- 复现入口：`build/apply_world_temporal_postfilter_round47_20261026.py --source-residual-alphas 0.05` 与严格评测器。
- 限制：不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮候选生成、严格评估并提交单轮结果。

### [PS-20261021-10] HuBERT/WORLD Round 87 源谱动态残差后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`43d2b70`
- 唯一变量：冻结Round85 checkpoint与gain1.6，仅将录音4源WORLD谱DCT零均值动态残差alpha设为0.02；无源VUV/F0/能量/AP，无重训。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7011/0.6794/0.1011/2.2824/0.2647`；身份、P10通过，泄漏、UTMOS、CER失败。候选SHA-256 `984939d4f10b6be67e6c147ef912ed8b9d03a986b6f7e714a506cb59961b6531`。
- 修改路径：`report/fixed_male_hubert_world_round87_20261027.{md,json}`、`coummucation.md`。
- 限制：identity OpenCC shim；录音5、Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round87_20261027.md`、`report/fixed_male_hubert_world_round87_20261027.json`。
- 下一责任方：Hardware-A / Codex 停止源谱残差注入，恢复训练变量探索。

### [PS-20261021-10] HuBERT/WORLD Round 88 多尺度动态损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`75940f6`
- 唯一变量：冻结Round85配置，VUV BCE系数0.35不变，仅把多尺度动态损失权重从1.25降至1.20；source prosody、variance matching、锚点概率0.25、gain1.6、种子和早停策略保持不变。
- 成功标准：固定录音4严格身份均值≥0.45、P10≥0.35、源泄漏≤0.10、UTMOS≥2.30、CER≤0.15五门全部通过；通过即停止训练。
- 数据边界：只用男性标准录音4评估；训练仍限男性录音1～3及目标Track5～8；录音5和Track9锁定。
- 复现入口：`build/train_paired_hubert_world_gru_round26_20261025.py --multiscale-weight 1.20`、candidate生成器和严格评测器。
- 限制：不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮训练、严格评估并提交单轮结果。

### [PS-20261021-10] HuBERT/WORLD Round 86 源谱动态残差后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`02995a5`
- 唯一变量：冻结Round85 checkpoint与gain1.6，仅将录音4源WORLD谱DCT零均值动态残差按alpha=0.05注入；无源VUV/F0/能量/AP，无重训。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7026/0.6828/0.1021/2.2968/0.2647`；身份、P10通过，泄漏、UTMOS、CER失败。候选SHA-256 `4da876bf25cc41250cf1d280452805d0b8fe8f863ac56c43893ef01872db61d7`。
- 修改路径：`report/fixed_male_hubert_world_round86_20261027.{md,json}`、`coummucation.md`。
- 限制：identity OpenCC shim；录音5、Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round86_20261027.md`、`report/fixed_male_hubert_world_round86_20261027.json`。
- 下一责任方：Hardware-A / Codex 测试更小谱残差alpha=0.02。

### [PS-20261021-10] HuBERT/WORLD Round 87 源谱动态残差后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`b5003d4`
- 唯一变量：冻结Round85 checkpoint与gain1.6，仅将录音4源WORLD谱DCT零均值动态残差alpha由0改为0.02；无源VUV/F0/能量/AP，无重训。
- 成功标准：固定录音4严格五门全部通过；否则记录泄漏、CER和自然度变化并拒绝。
- 数据边界：只用男性标准录音4评估；Track9和录音5继续锁定，不用于选择或训练。
- 复现入口：`build/apply_world_temporal_postfilter_round47_20261026.py --source-residual-alphas 0.02` 与严格评测器。
- 限制：不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮候选生成、严格评估并提交单轮结果。

### [PS-20261021-10] HuBERT/WORLD Round 82 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`47b132e`
- 唯一变量：VUV BCE系数由Round81的0.40降至0.30；其余训练结构、source prosody、variance matching、动态权重1.25、锚点0.25、gain1.6、种子不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7003/0.6726/0.1006/2.3312/0.2941`；泄漏、CER未过门。检查点SHA-256 `2d69a00d00c21674de7578c03185d325294386504fe7100e242253a04ca0fc9b`；候选SHA-256 `681a830407284cddb03aa1ad9c9ce6f357ac96489cc20b445375cfaaa37b7d39`。
- 修改路径：`report/fixed_male_hubert_world_round82_20261027.{md,json}`、`coummucation.md`。
- 限制：identity OpenCC shim；CPU启动器返回码为1但产物已独立核验；录音5、Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round82_20261027.md`、`report/fixed_male_hubert_world_round82_20261027.json`。
- 下一责任方：Hardware-A / Codex 转向内容保持后处理的单变量测试，优先围绕Round82模型评估可逆的VUV/内容平滑设置。

### [PS-20261021-10] HuBERT/WORLD Round 83 源VUV后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`671ddd3`
- 唯一变量：冻结Round82 checkpoint与gain1.6，仅将预测VUV与录音4源WORLD VUV按源权重0.10混合；不重训、不注入源谱/音高/能量/AP。
- 成功标准：固定录音4严格五门全部通过；否则记录泄漏、CER和自然度变化并拒绝。
- 数据边界：只用男性标准录音4评估；Track9和录音5继续锁定，不用于选择或训练。
- 复现入口：`build/apply_world_temporal_postfilter_round47_20261026.py --source-vuv-alphas 0.1` 与严格评测器；结果报告记录候选SHA。
- 限制：不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮候选生成、严格评估并提交单轮结果。

### [PS-20261021-10] HuBERT/WORLD Round 84 源VUV后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`b86397d`
- 唯一变量：冻结Round82 checkpoint与gain1.6，仅将预测VUV与录音4源WORLD VUV按源权重0.05混合；不重训、不注入源谱/音高/能量/AP。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7012/0.6747/0.1005/2.3238/0.2500`；泄漏、CER未过门。候选SHA-256 `1d7320b567dd30f41dcdc7b1a96049146c8dca8c3efdbd9c05334185fd62e4c1`。
- 修改路径：`report/fixed_male_hubert_world_round84_20261027.{md,json}`、`coummucation.md`。
- 限制：identity OpenCC shim；录音5、Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round84_20261027.md`、`report/fixed_male_hubert_world_round84_20261027.json`。
- 下一责任方：Hardware-A / Codex 回到不注入源VUV的内容保持后处理或训练变量。

### [PS-20261021-10] HuBERT/WORLD Round 85 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`8dda03d`
- 唯一变量：冻结Round82配置，仅将训练VUV BCE系数由0.30改为0.35；source prosody、variance matching、动态权重1.25、锚点概率0.25、gain1.6、随机种子和早停策略保持不变。
- 成功标准：固定录音4严格身份均值≥0.45、P10≥0.35、源泄漏≤0.10、UTMOS≥2.30、CER≤0.15五门全部通过；通过后立即停止算法训练并转入本地验证门。
- 数据边界：只用男性标准录音4评估；训练仍限男性录音1～3及目标Track5～8；锁定录音5和Track9不得用于训练、选参、早停或筛选。
- 复现入口：`build/train_paired_hubert_world_gru_round26_20261025.py`、`build/apply_world_temporal_postfilter_round47_20261026.py`、`build/evaluate_seed_fixed_male_strict_20261024.py`。
- 限制：不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮训练、严格评估并提交单轮结果。

### [PS-20261021-10] HuBERT/WORLD Round 83 源VUV后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`671ddd3`
- 唯一变量：冻结Round82 checkpoint与gain1.6，仅将预测VUV与录音4源WORLD VUV按源权重0.10混合；不重训、不注入源谱/音高/能量/AP。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.6990/0.6764/0.0993/2.3515/0.3235`；身份、P10、泄漏、UTMOS通过，CER失败。候选SHA-256 `746879f49f330f33e81facfe133f3eeb7c581281f2682a457167b29b5bf9c404`。
- 修改路径：`report/fixed_male_hubert_world_round83_20261027.{md,json}`、`coummucation.md`。
- 限制：identity OpenCC shim；录音5、Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round83_20261027.md`、`report/fixed_male_hubert_world_round83_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续针对内容保持，优先测试不注入源VUV的输出内容后处理。

### [PS-20261021-10] HuBERT/WORLD Round 84 源VUV后处理
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`9c3384b`
- 唯一变量：冻结Round82 checkpoint与gain1.6，仅将预测VUV与录音4源WORLD VUV按源权重0.05混合；不重训、不注入源谱/音高/能量/AP。
- 成功标准：固定录音4严格五门全部通过；否则记录泄漏、CER和自然度变化并拒绝。
- 数据边界：只用男性标准录音4评估；Track9和录音5继续锁定，不用于选择或训练。
- 复现入口：`build/apply_world_temporal_postfilter_round47_20261026.py --source-vuv-alphas 0.05` 与严格评测器；结果报告记录候选SHA。
- 限制：不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮候选生成、严格评估并提交单轮结果。

### [PS-20261021-10] HuBERT/WORLD Round 81 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：`449c2ba`
- 唯一变量：VUV BCE系数由Round80的0.50降至0.40；其余训练结构、source prosody、variance matching、动态权重1.25、锚点0.25、gain1.6、种子不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = `0.7020/0.6843/0.1140/2.2540/0.2353`；泄漏、UTMOS、CER未过门。检查点SHA-256 `3640730e8c350277688aeaea43391f0c355d5b421cc67b935ceb56df7be9aaa4`；候选SHA-256 `7ecdeba5335682dbb7226fb12e84ad306b7b4140c33083b0d3c2fa30189b2fad`。
- 修改路径：`report/fixed_male_hubert_world_round81_20261027.{md,json}`、`coummucation.md`。
- 限制：identity OpenCC shim；CPU训练/候选启动器返回码为1但输出和checkpoint已独立核验；录音5、Track9未用于训练或筛选；未播放、未接触板卡，无真人听感、Cortex-A9、RTL/PL或实时结论。
- 报告链接：`report/fixed_male_hubert_world_round81_20261027.md`、`report/fixed_male_hubert_world_round81_20261027.json`。
- 下一责任方：Hardware-A / Codex 继续围绕VUV BCE权重与输出后处理单变量试验。

### [PS-20261021-10] HuBERT/WORLD Round 82 VUV 损失权重
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：`43a4ea2`
- 唯一变量：以 Round81 的 VUV BCE 系数0.40为基准，仅降低至0.30；source prosody、variance matching、动态权重1.25、锚点概率0.25、gain1.6、随机种子和早停策略保持不变。
- 成功标准：固定录音4严格身份均值≥0.45、P10≥0.35、源泄漏≤0.10、UTMOS≥2.30、CER≤0.15五门全部通过；通过后立即停止算法训练并转入本地验证门。
- 数据边界：只用男性标准录音4评估；训练仍限男性录音1～3及目标Track5～8；锁定录音5和Track9不得用于训练、选参、早停或筛选。
- 复现入口：`build/train_paired_hubert_world_gru_round26_20261025.py`、`build/apply_world_temporal_postfilter_round47_20261026.py`、`build/evaluate_seed_fixed_male_strict_20261024.py`；结果报告记录缓存与资产SHA及严格评测命令。
- 限制：identity OpenCC shim的简繁归一化有限；不播放、不录音、不接触板卡，不声明试听、Cortex-A9、RTL/PL或实时通过。
- 下一责任方：Hardware-A / Codex 完成本轮训练、严格评估并提交单轮结果。


### [PS-20261021-10] HuBERT/WORLD Round 88 结果与训练数据用途更正
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：45cab049b3ad4d1179596adab70a68166056793b
- 唯一变量：以Round85为基准，仅将多尺度动态损失权重1.25改为1.20；VUV BCE=0.35、source prosody、variance matching、锚点0.25、gain1.6和种子不变。
- 量化结果：身份均值/P10/泄漏/UTMOS/CER = 0.6988806643/0.6764631763/0.1049895034/2.3280673822/0.2647058824；泄漏、CER失败。2000 step完成，checkpoint内最佳step=1200，验证loss=0.7921773791；checkpoint SHA-256 e21d8175cb56a5aa3f3e7ac75578705b5deb8cb40fea07a5a73ef87d38586faa；WAV SHA-256 a49aa55a3d9677ef42cf6d03daf63f2d4a52e451af62d3f2688c1966ea3969eb。
- 数据用途更正：Round25缓存声明fixed_male_audio_used=false，192条公共配对训练、8条独立验证；女声Track5～8作自重建锚点。此前认领记录中“男性录音1～3用于训练”的文字不准确，实际它们用于评测源身份质心；本轮只评测录音4，未读取录音5或Track9。
- 修改路径：build/reproduce_hubert_world_round88_20261027.py、report/fixed_male_hubert_world_round88_20261027.{md,json}、coummucation.md。
- 复现命令：见JSON内reproduction四阶段命令；prepare与py_compile通过，evaluate入口重跑得到相同指标；原始checkpoint已独立加载并核对历史、权重有限值、缓存SHA、WAV SHA。
- 限制：identity OpenCC shim不执行简繁转换，原始评测protocol文字与实际不符已披露；源ASR文字非人工真值。训练启动器写出产物后退出1；未播放、未录音、未接触板卡，无真人试听、PS/PL/实时结论。
- 报告链接：report/fixed_male_hubert_world_round88_20261027.md、report/fixed_male_hubert_world_round88_20261027.json。
- 下一责任方：Hardware-A / Codex；后续先针对CER与训练数据覆盖做诊断，避免继续重复无收益的微小权重扫描。Round59～88计30轮，剩余额度20轮；五门全过即停止。

### [PS-20261021-10] HuBERT/WORLD Round 89 长片段训练认领
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：816b1ddc4b7a88d5ec39f7f6b55b1b7fe0fea551
- 唯一变量：以Round88为基准，CROP从128增加到192帧（约2.56秒至3.84秒），测试更长上下文对CER的影响；VUV BCE=0.35、动态损失1.20、锚点0.25、种子、source prosody、variance matching、gain1.6和2000 step上限不变。
- 数据与限制：沿用Round25公共配对缓存，192训练/8验证，目标Track5～8锚点。长度筛选使可抽样训练条数由184/192降为140/192，报告此混杂因素；固定男声1～3仍只用于评测源质心，只评测录音4，不读录音5和Track9。
- 成功标准：身份均值>=0.45、P10>=0.35、泄漏<=0.10、UTMOS>=2.30、CER<=0.15；实际仍用identity OpenCC兼容评测，不能宣称完整归一化协议通过。
- 修改路径：build/reproduce_hubert_world_round88_20261027.py（增加固定Round89配置）、coummucation.md；结果写report/fixed_male_hubert_world_round89_20261027.{md,json}。
- 复现命令：python build/reproduce_hubert_world_round88_20261027.py prepare --experiment-round 89 --asset-root <asset-root>；随后相同入口train/candidate/evaluate；评测使用Python3.12，训练和生成使用既有yolo Python。
- 已验证证据：Round25清单content_frames长度计数128帧合格184，192帧合格140；当前分支与main同步、PR13归本任务，无同路线新认领。
- 现场边界：不播放、不录音、不接触板卡，不声明PS/PL或实时通过。
- 下一责任方：Hardware-A / Codex 训练、严格评测、直接从产物提取证据并单轮提交。


### [PS-20261021-10] HuBERT/WORLD Round 89 长片段训练结果
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：REJECTED
- 基准提交：4ec44eb；Round88结果基线816b1ddc4b7a88d5ec39f7f6b55b1b7fe0fea551。
- 改动：CROP128→192；其余Round88超参数不变。长度筛选使训练可用条数184→140（总192），存在覆盖率混杂。
- 量化结果：身份/P10/泄漏/UTMOS/CER=0.6777270597/0.6568020193/0.1228567630/2.0558493137/0.3676470588；后三门失败，比Round88退步。早停step1300，最佳step500，验证loss0.8019716069。
- 证据：checkpoint SHA-256 5846de735d14ddeccb44257901abc551efdb994c136a8d3dfc7005d60ff4761a；候选SHA-256 48095635b1a4e21fc5c23659ee0fafbc5c16c788dba23c1ae9f575c479329c6b；独立加载检查有限权重、训练历史、缓存及WAV SHA通过。
- 修改路径与报告：report/fixed_male_hubert_world_round89_20261027.{md,json}、coummucation.md、team_project/project_status.md、report/ai_worklog.md。
- 复现：build/reproduce_hubert_world_round88_20261027.py prepare/train/candidate/evaluate --experiment-round 89 --asset-root <asset-root>；具体解释器和命令见JSON。
- 限制：identity OpenCC shim不执行简繁转换，CER源参考是ASR而非人工真值；训练及生成启动器产物完成后退出1，评测退出0。公共配对192训练/8验证，男性1～3仅评测质心；仅评测录音4，录音5/Track9保持锁定。无播放、录音、板测或PS/PL/实时结论。
- 下一责任方：Hardware-A / Codex。恢复Round88的128帧基线，诊断PCA压缩瓶颈；Round59～89共31轮，剩19轮，五门全过即停止。


### [PS-20261021-10] HuBERT/WORLD Round 90 PCA内容瓶颈认领
- 日期：2026-10-27
- 角色/Agent：Hardware-A / Codex（电脑端离线算法）
- 状态：CLAIMED
- 基准提交：783e78d3ff5667119c10a24c19eb59ce79277e9d；算法对照Round88。
- 唯一变量：HuBERT PCA_DIM96→192，源韵律拼接后输入99→195。保持GRU hidden192/2层、CROP128、BATCH8、STEPS2000、早停、VUV0.35、动态1.20、方差损失、锚点0.25、seed和gain1.6不变。输入线性层随维度变大，属同一变量的必要结构变化。
- 依据：Round89增加上下文反而退步；过去多轮微调损失或源谱注入没有解决CER。检验96维压缩是否限制内容保留，不能预先宣称效果改善。
- 数据：同一Round25缓存192公共配对训练/8验证；PCA和归一化仅拟合训练集，128帧可用184/192；目标Track5～8锚点。男性1～3仅评测源质心，录音4验证，录音5和Track9锁定。
- 成功标准：身份>=0.45、P10>=0.35、泄漏<=0.10、UTMOS>=2.30、CER<=0.15全部通过；兼容评测identity OpenCC shim不得宣称完整归一化协议通过。
- 修改路径：build/reproduce_hubert_world_round88_20261027.py、coummucation.md；结果报告report/fixed_male_hubert_world_round90_20261027.{md,json}。
- 复现：入口prepare/train/candidate/evaluate --experiment-round 90 --asset-root <asset-root>。准备后检查base/prior均PCA192、trainer仍CROP128；训练前py_compile。
- 限制：保持CPU既有解释器；无播放、录音、板测、PS/PL或实时结论。
- 下一责任方：Hardware-A / Codex 完成本轮训练和客观评测并单轮提交。此轮完成后为32/50，最多至Round108。


### [PS-20261021-10] Round90 评测依赖修正说明
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED（随Round90结果提交）。
- 基准提交：ceae77a；修改路径：build/reproduce_hubert_world_round88_20261027.py、Round90报告。
- 改动：补齐本地opencc-python-reimplemented==0.1.7，Round90默认使用真实t2s转换；Round88/89默认保留历史identity口径供复现，新增--cer-normalizer可显式选择。
- 复现：Python3.12 -m pip install --target <asset-root>/build/generated/eval_opencc_deps_20261027 --no-cache-dir opencc-python-reimplemented==0.1.7；评测入口evaluate --experiment-round 90 --cer-normalizer opencc。
- 量化证据：简繁转换smoke通过；从已提交的Round88/89保存ASR文本重算，CER分别仍为18/68=0.2647058824、25/68=0.3676470588；不改写历史报告，不重新读取音频。这是评测环境修复，不算额外训练轮次。
- 限制：CER源参考仍是Whisper识别而非人工校对；未因此放宽门槛、读取录音5/Track9或执行现场测试。
- 下一责任方：Hardware-A / Codex 完成Round90真实OpenCC评测并在JSON同时记录raw CER和normalized CER、依赖版本及上述核对证据。


### [PS-20261021-10] HuBERT/WORLD Round 90 PCA内容瓶颈结果
- 日期：2026-10-27；角色：Hardware-A / Codex（离线算法）；状态：REJECTED。
- 基准提交：ceae77a94a77e7cc2bbb5701b9d80256ec0171f1；算法基线Round88。
- 变量：PCA96→192，输入99→195，GRU其余配置保持Round88；参数量496779。128帧训练可用184/192，与Round88一致。
- 量化结果：身份/P10/泄漏/UTMOS/CER=0.6439841784/0.6157650156/0.1262829402/2.1855001450/0.4558823529；后三门失败。最佳step600，完成step1400；增加PCA维度未改善录音4内容。
- 证据：checkpoint SHA-256 2a29d614f6995fd0a4d3d4d349d2860fbe07a2017d988bfc6b853d82e43eab95；WAV SHA-256 fb8bc99c9a5319c58c96f6c0e2684fe69c36863918efc3119f899a5ef50c6c52；有限权重、PCA(768,192)、输入(192,195)、训练历史与缓存/WAV SHA核验通过。
- 修改路径与报告：build/reproduce_hubert_world_round88_20261027.py、report/fixed_male_hubert_world_round90_20261027.{md,json}、coummucation.md、team_project/project_status.md、report/ai_worklog.md。
- 复现：入口prepare/train/candidate/evaluate --experiment-round 90 --asset-root <asset-root>；evaluate实际使用OpenCC0.1.7 t2s，raw CER与normalized CER同为0.4558823529。报告含依赖安装、历史文本重算核对与完整命令。
- 限制：源ASR非人工真值；训练和生成完成产物后退出1，独立检查通过，评测退出0。公共配对192训练/8验证，目标Track5～8锚点；固定男性1～3只作评测源质心，录音4验证，录音5/Track9锁定。无播放、录音、板测或PS/PL/实时结论。
- 下一责任方：Hardware-A / Codex；恢复Round88并测试提高锚点概率，避免继续扩PCA。Round59～90共32轮，剩18轮。


### [PS-20261021-10] HuBERT/WORLD Round 91 提高目标锚点认领
- 日期：2026-10-27；角色：Hardware-A / Codex（电脑端离线算法）；状态：CLAIMED。
- 基准提交：3f6504562efcf2c403e33406597cad3cd6e1bb62；算法配置恢复Round88，撤销Round89长crop和Round90 PCA增加。
- 唯一训练变量：目标自重建锚点采样概率0.25→0.50；PCA96、GRU hidden192/2层、CROP128、BATCH8、STEPS2000、seed、早停、VUV0.35、动态1.20、方差损失、source prosody、gain1.6不变。更多锚点意味着相同step预算下公共配对采样减少，将如实报告。
- 依据：Round75将锚点概率降至0.15时CER恶化到0.50；Round89/90增加上下文或保留维度均退步。测试更强目标自重建约束是否改善内容，尚无收益结论。
- 数据：同一192公共配对训练/8验证，PCA和归一化仅训练集；128帧可用184/192，目标Track5～8锚点。固定男声1～3仅评测源质心，录音4验证，录音5/Track9锁定。
- 成功标准：身份>=0.45、P10>=0.35、泄漏<=0.10、UTMOS>=2.30、CER<=0.15全部通过即停止训练；真实OpenCC0.1.7 t2s，与Round88保存文本重算CER相同。
- 修改路径：build/reproduce_hubert_world_round88_20261027.py、coummucation.md；正式报告report/fixed_male_hubert_world_round91_20261027.{md,json}。
- 复现：入口prepare/train/candidate/evaluate --experiment-round 91 --asset-root <asset-root>，评测--cer-normalizer opencc；具体解释器沿用Round90。
- 验证：准备后核对PCA96、CROP128、ANCHOR_PROBABILITY0.50与runtime语法，结果从产物直接提取。
- 限制：ASR源参考非人工真值；无播放、录音、板测、PS/PL/实时结论。
- 下一责任方：Hardware-A / Codex 完成本轮训练、评测、独立检查并逐轮提交。完成后33/50，最多Round108。


### [PS-20261021-10] HuBERT/WORLD Round 91 提高目标锚点结果
- 日期：2026-10-27；角色：Hardware-A / Codex（离线算法）；状态：REJECTED。
- 基准提交：1fe6b2d25c4adf452a609b98233eb1dc8bdc1106；算法基线Round88。
- 唯一变量：目标自重建锚点概率0.25→0.50；其余恢复Round88，PCA96、CROP128、hidden192。相同步数下公共配对抽样相应减少。
- 量化结果：身份/P10/泄漏/UTMOS/CER=0.6936297194/0.6723958308/0.1130648930/2.2011870543/0.3088235294；后三门失败，未优于Round88。完成step1800，最佳step1000，验证loss0.8054647967。
- 证据：checkpoint SHA-256 fbc00a21c1360c3b57d900a521d8303d29b8fa0595caeac49ebf7f6335ecee2f；候选SHA-256 a7f803ac6791dd4f30e9e801737486cee37321505c68c5c3f0f281965703199f；有限权重、输入/PCA维度、缓存SHA、候选SHA核验通过。
- 补充诊断：仅录音1～3提取源韵律，三列log-F0/VUV/log-energy的每段均值偏移均小于训练1σ；未发现严重均值分布越界，未改候选或选择校准。逐录音SHA和统计在JSON，复现build/audit_fixed_male_prosody_round91_20261027.py --asset-root <asset-root>。
- 修改路径与报告：build/audit_fixed_male_prosody_round91_20261027.py、report/fixed_male_hubert_world_round91_20261027.{md,json}、coummucation.md、team_project/project_status.md、report/ai_worklog.md。
- 复现：build/reproduce_hubert_world_round88_20261027.py prepare/train/candidate/evaluate --experiment-round 91 --asset-root <asset-root>，evaluate真实OpenCC0.1.7，具体解释器与命令见JSON。
- 限制：ASR源参考非人工真值；训练/生成启动器产物完成后退出1，客观评测退出0；诊断启动器亦在写出有效JSON后退出1。公共配对192/8、目标Track5～8锚点；男性1～3未参与本轮模型训练，只用于评测源质心和上述只读诊断；仅录音4验证，录音5/Track9锁定。无现场或PS/PL/实时结论。
- 下一责任方：Hardware-A / Codex；恢复Round88并测试GRU容量，保持五门。Round59～91共33轮，剩17轮，最多Round108。


### [PS-20261021-10] HuBERT/WORLD Round 92 GRU容量认领
- 日期：2026-10-27；角色：Hardware-A / Codex（离线算法）；状态：CLAIMED。
- 基准提交：f92387488fefe90b966ecefde67cd6f3df4e9dcb；算法基线恢复Round88。
- 唯一训练变量：两层因果GRU hidden192→384，输入PCA96+源韵律3维仍99；相关输入/输出线性层随hidden同步扩大。CROP128、BATCH8、STEPS2000、seed、早停、锚点0.25、VUV0.35、动态1.20、方差损失、gain1.6不变。
- 依据：长片段、更大PCA、更多锚点均未改善录音4CER；源1～3韵律均值未严重越界。测试网络容量能否缓解声学重建不足；更大模型是否过拟合或可部署均未下结论。
- 复现修正：prepare阶段所有任务模块只从当轮runtime/build导入，防止未来asset-root/build出现同名脚本时遮蔽当轮补丁；当前asset-root无这三个训练同名脚本，未发现此前结果受遮蔽。
- 数据：同一公共配对192训练/8验证，训练PCA/归一化，128帧可用184/192；目标Track5～8锚点。男性1～3只作评测源质心；录音4验证，录音5/Track9锁定。
- 成功标准：身份>=0.45、P10>=0.35、泄漏<=0.10、UTMOS>=2.30、CER<=0.15全部通过即停止；保持真实OpenCC0.1.7。
- 修改路径：build/reproduce_hubert_world_round88_20261027.py、coummucation.md；报告report/fixed_male_hubert_world_round92_20261027.{md,json}。
- 复现：prepare/train/candidate/evaluate --experiment-round 92 --asset-root <asset-root>，评测--cer-normalizer opencc；训练前核对PCA96、hidden384、anchor0.25、CROP128与语法。
- 限制：ASR参考非人工真值；当前仅电脑端质量试验，不因容量增加而宣称Cortex-A9/PL预算或现场通过。无播放、录音、板测。
- 下一责任方：Hardware-A / Codex 完成本轮训练、客观评测、独立核验及提交；完成后34/50，最多Round108。


### [PS-20261021-10] HuBERT/WORLD Round 92 GRU容量结果
- 日期：2026-10-27；角色：Hardware-A / Codex（离线算法）；状态：REJECTED。
- 基准提交：adbba4bf2cd2b1f89df18b88d84924046db298c6；算法基线Round88。
- 唯一变量：GRU hidden192→384，相关输入/输出层同步扩大，参数1841355；PCA96、CROP128、anchor0.25及其他配置保持Round88。
- 量化结果：身份/P10/泄漏/UTMOS/CER=0.6774789683/0.6523689563/0.1209129382/2.2483020624/0.3823529412；后三门失败。完成step1300，最佳step500，验证loss0.7960573882。step500后验证损失回升，训练重建误差下降，存在过拟合迹象；不能把更低训练误差当作音质通过。
- 证据：checkpoint SHA-256 457765a9bbc117dfc8316f3c105ab543f67e988241a5e7c46a48040da2381f1b；候选SHA-256 a10739d25b3a668fb13cb06975b1804d0996e5218170e3727a0912efdb24ecba；有限权重、PCA(768,96)、输入(384,99)、GRU权重(1152,384)、训练历史、缓存与WAV SHA核验通过。
- 修改路径与报告：report/fixed_male_hubert_world_round92_20261027.{md,json}、coummucation.md、team_project/project_status.md、report/ai_worklog.md。
- 复现：build/reproduce_hubert_world_round88_20261027.py prepare/train/candidate/evaluate --experiment-round 92 --asset-root <asset-root>；evaluate真实OpenCC0.1.7，完整命令见JSON。
- 限制：训练/生成启动器产物完成后退出1，评测退出0；ASR参考非人工真值。公共配对192训练/8验证，Track5～8锚点，固定男性1～3仅评测源质心；仅录音4验证，录音5/Track9锁定。无播放、录音、板测、Cortex-A9/PL预算或实时结论。
- 下一责任方：Hardware-A / Codex；针对宽模型过拟合测试层间dropout。Round59～92共34轮，剩16轮，最多Round108。


### [PS-20261021-10] HuBERT/WORLD Round 93 宽GRU正则化认领
- 日期：2026-10-27；角色：Hardware-A / Codex（离线算法）；状态：CLAIMED。
- 基准提交：95a62a4ee769ddfe629b24b75742533bd34bea0f；算法基线Round92。
- 唯一算法变量：hidden384两层GRU增加层间dropout0.20；PCA96、输入99、CROP128、BATCH8、STEPS2000、seed、早停、anchor0.25、VUV0.35、动态1.20、方差项、gain1.6保持Round92。
- 必要模式修复：validate会设置eval，原训练循环没有恢复train；历史GRU dropout0且无BatchNorm，因此此前前向不因模式变化。新dropout必须在每次训练前model.train()，验证和生成保持eval；该变化作为dropout生效必需部分，不声称仅声明dropout参数即可。
- 依据：Round92 step500后训练误差下降、验证损失回升，且录音4CER0.3824；检查正则化是否缓解过拟合，不预判收益。
- 数据：同公共配对192训练/8验证，128帧184可用，Track5～8自重建锚点；男性1～3仅评测质心，录音4验证，录音5/Track9锁定。
- 成功标准：身份>=0.45、P10>=0.35、泄漏<=0.10、UTMOS>=2.30、CER<=0.15全过即停止；真实OpenCC0.1.7。
- 修改路径：build/reproduce_hubert_world_round88_20261027.py、coummucation.md；报告report/fixed_male_hubert_world_round93_20261027.{md,json}。
- 复现：prepare/train/candidate/evaluate --experiment-round 93 --asset-root <asset-root>，evaluate --cer-normalizer opencc；准备后核对hidden384、dropout0.20、model.train与语法。
- 限制：CPU离线，ASR参考非人工真值；无播放、录音、板测、Cortex-A9/PL或实时结论。
- 下一责任方：Hardware-A / Codex 完成训练评测并单轮提交。完成后35/50，最多Round108。


### [PS-20261021-10] 历轮收益复盘与Round93中止
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED / ROUND93_ABORTED。
- 基准提交：a0a2b4e；用户要求从近百轮提取经验，停止无收益的小步调参。
- 事实：Round93在特征准备阶段中止，进程34436已退出，未产出checkpoint/候选/指标；不计作完成音质评测，不扩充50轮预算。Round59～92已完成34轮。
- 修改路径与报告：report/training_progress_retrospective_20261027.md、coummucation.md。
- 复现：逐项读取报告内所列Round23/26/28/33/37/46/47/49/52及69/88～92；本次为既有证据复盘，无新训练。
- 量化结论：扩展配对监督CER0.3804→0.1522（多变量混杂）；多尺度监督0.1522→0.1087；方差匹配UTMOS1.7038→1.8616；gain1.4验证UTMOS2.0055→2.4082。近期增crop/PCA/锚点/宽度均退步，不能继续局部扫描。
- 更正：Seed9/18历史上客观过五门，但用户试听否决；当前无最终验收通过方案，不等于从未客观过门。目标自重建与真正男转女证据必须区分。
- 限制：历史部分轮次无独立报告，未声称所有轮次统一复算；CER参考为ASR，不能替代人工真值或听感。无新音频、锁定集、现场或RTL/PL操作。
- 下一责任方：Hardware-A / Codex 先审计非锁定公共教师内容上限、错误时段和源专用监督覆盖，获得机制证据后才提出下一训练轮；不自动启动dropout或进一步调权。


### [PS-20261021-10] 公共配对教师内容诊断认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：1a8954c；本次为收益复盘后的根因诊断，不新增训练或参数扫描。
- 范围：仅现有公共配对8条validation，核对源/教师SHA，以同一Whisper-small分别识别并与manifest声明文本比较，同时报告teacher对source-ASR的CER，避免源识别错误被隐藏。
- 修改路径：build/audit_paired_teacher_content_20261027.py、report/paired_teacher_content_audit_20261027.{json,md}、coummucation.md。
- 复现：Python3.12 build/audit_paired_teacher_content_20261027.py --asset-root <asset-root> --output <generated>/teacher_content_audit.json。
- 判据：先查教师是否保留内容；若教师自身明显错漏，不继续以优化学生权重解决教师缺陷。若教师内容良好，下一步定位学生预测和时间对齐。
- 限制：声明文本仍需独立人工核验；非最终五门验收，不读录音4/5或Track9，不播放、不训练、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成诊断、记录逐句证据、推送后据此决定下一项机制验证。


### [PS-20261021-10] 公共配对教师内容诊断结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED / DIAGNOSIS_ONLY。
- 基准提交：1a8954c；修改路径：build/audit_paired_teacher_content_20261027.py、report/paired_teacher_content_audit_20261027.{md,json}、coummucation.md。
- 量化结果：8验证对源/教师SHA和样本数通过；对声明152字，源21编辑CER0.1381579，教师22编辑CER0.1447368。SSB04340118源0/17而教师3/17，其他句也有教师更好的情况；不能仅凭总分判定教师完全可靠或普遍破坏内容。
- 复现：Python3.12 build/audit_paired_teacher_content_20261027.py --asset-root <asset-root> --output <generated>/teacher_content_audit.json；退出0，真实OpenCC0.1.7。
- 报告：report/paired_teacher_content_audit_20261027.md与JSON保留逐句文本、SHA、编辑数及脚本SHA。
- 限制：专名、数字书写与ASR错误混合，声明文本未经独立人工校对；等长不证明音素对齐。未读录音4/5或Track9，不训练、不播放、不接触板卡；不是五门验收。
- 下一责任方：Hardware-A / Codex 在同8句分离教师原音、WORLD压缩重建、冻结学生的内容误差，不恢复无机制依据的参数扫描。


### [PS-20261021-10] 同句内容链诊断认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：77dff33；冻结Round88模型，gain1.6，不训练、不扫描。
- 范围：同8条公共validation，比较教师原音、SP60/AP12 5ms重建、训练缓存20ms再插值重建、学生预测+既有gain1.6。前两重建分支不用目标裁剪以隔离表示/时间压缩；学生保持生产裁剪。各分支还保留既有合成器平滑和峰值规则，不能把差异归因于单独DCT。
- 修改路径：build/audit_content_chain_20261027.py、report/paired_content_chain_audit_20261027.{json,md}、coummucation.md。
- 复现：yolo Python运行generate；Python3.12运行evaluate，均--asset-root <asset-root> --output <generated>/paired_content_chain_20261027；需先完成教师内容诊断。
- 判据：若WORLD真值路径仍保留内容而预测路径恶化，优先诊断映射/对齐及监督；若20ms重建即退化，优先修复时间表示。不按结果直接扫描更多权重。
- 限制：声明文本非人工核验，自动ASR差异非听感结论；不读录音4/5或Track9，不播放、不训练、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成逐句证据并提交。


### [PS-20261021-10] 同句内容链诊断结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED / DIAGNOSIS_ONLY。
- 基准提交：77dff33；模型冻结Round88，未训练和调参。
- 量化结果：同8句152字，源21、教师22、WORLD5ms24、缓存20ms25、学生gain1.6为44编辑，CER依次0.138158/0.144737/0.157895/0.164474/0.289474。最大观察增量在缓存重建到学生管线，不支持20ms压缩本身为主要原因。
- 修改路径与报告：build/audit_content_chain_20261027.py、report/paired_content_chain_audit_20261027.{md,json}、coummucation.md。
- 复现：yolo Python入口generate，Python3.12入口evaluate，--asset-root <asset-root> --output <generated>/paired_content_chain_20261027；前置上一教师内容诊断，完整命令见JSON。
- 核验：checkpoint SHA e21d8175cb56a5aa3f3e7ac75578705b5deb8cb40fea07a5a73ef87d38586faa；缓存/源/教师SHA通过；8行24WAV二次核对哈希，生成产物后退出1，评测退出0。
- 限制：ASR差异不是因果可加误差分解；学生分支包含目标裁剪和gain，锚点使用5ms统计而非生产20ms插值，不声称录音4逐位复现；声明文本非人工核验。WORLD分支保留合成器平滑/VUV/峰值规则。无录音4/5、Track9、播放、训练或板端结论。
- 下一责任方：Hardware-A / Codex 优先量化源/教师时间对齐、预测裁剪和动态误差，再选择有机制依据的监督修复；不恢复参数扫描。


### [PS-20261021-10] 时序与裁剪诊断认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：20ebd6a；冻结Round88，仅公共8句validation，无训练或选参。
- 范围：源/教师能量包络±200ms相关，测全局错位代理；预测、gain1.6及裁剪后的谱/F0/能量/AP动态比和标准化误差、越界率；锚点沿生产20ms插值统计。
- 修改路径：build/audit_alignment_clipping_20261027.py、report/alignment_clipping_audit_20261027.{json,md}、coummucation.md。
- 复现：yolo Python build/audit_alignment_clipping_20261027.py --asset-root <asset-root> --output <generated>/alignment_clipping.json。
- 判据：区分明显全局时移、动态不足与裁剪损失；能量相关不是音素对齐证明，不按最佳lag直接修改训练集。
- 限制：只诊断，不合成、不读取录音4/5或Track9、不播放、不接触板卡。
- 下一责任方：Hardware-A / Codex 完成逐句统计和报告。


### [PS-20261021-10] 时序与裁剪诊断结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED / DIAGNOSIS_ONLY。
- 基准提交：20ebd6a；冻结Round88，8公共validation，不训练或合成。
- 量化结果：8/8能量包络最佳lag0，相关0.9103～0.9723，不支持全局平移修复。gain1.6导致能量27.97%、AP51.14%值越界；AP动态比预测0.7711→增益1.2337→裁剪0.8835，谱0.7512→1.2019→1.1507，能量0.9091→1.4546→1.3718。
- 修改路径与报告：build/audit_alignment_clipping_20261027.py、report/alignment_clipping_audit_20261027.{md,json}、coummucation.md。
- 复现：yolo Python build/audit_alignment_clipping_20261027.py --asset-root <asset-root> --output <generated>/alignment_clipping.json；启动器完成JSON后退出1，完整8行、有限值、checkpoint/缓存SHA独立核验。
- 判定：统一增益与裁剪在不同参数组作用不同，优先冻结模型做能量/AP增益移除对照，而不是继续统一增益或损失权重扫描。
- 限制：全局能量相关不证明局部音素对齐；RMS量不证明轨迹正确；统计位于20ms帧，非最终5ms裁剪率；仅参数统计不能证明CER改善。无录音4/5、Track9、训练、合成、播放、板测或PS/PL结论。
- 下一责任方：Hardware-A / Codex 在同8句冻结模型和谱gain1.6、分别移除能量或AP增益，检查内容与自然度，结果出来前不选新配置。


### [PS-20261021-10] 分组增益机制验证认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：268dc96；冻结Round88 checkpoint，8公共validation，谱gain1.6。
- 实验：原gain1.6、仅去能量增益、仅去AP增益三个固定对照；使用生产20ms锚点统计，其他裁剪/F0/VUV/合成不变，无搜索网格或训练。
- 修改路径：build/audit_content_chain_20261027.py --group-ablation、report/group_gain_ablation_20261027.{md,json}、coummucation.md。
- 复现：generate用yolo Python、evaluate用Python3.12，--group-ablation --asset-root <asset-root> --output <generated>/group_gain_ablation_20261027。
- 选择证据：报告同句CER、逐句UTMOS、两说话人一致性；只改善总分而某人退步不选新配置。结果不能替代固定男性五门。
- 限制：不读取录音4/5或Track9，不播放、不训练、不接触板卡。计为机制验证，不额外扩充50轮训练预算。
- 下一责任方：Hardware-A / Codex 完成对照并提交证据。


### [PS-20261021-10] 分组增益机制验证结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：REJECTED_AS_CONTENT_SOLUTION。
- 基准提交：268dc96；模型Round88冻结，8公共validation，生产20ms锚点统计，无训练/网格。
- 量化结果：baseline CER44/152=0.289474、UTMOS2.457535；去能量gain CER40/152=0.263158、UTMOS2.448939；去AP gain CER44/152=0.289474、UTMOS2.474633。
- 跨人证据：去能量gain令SSB0080 UTMOS2.613651→2.561476，SSB0434为2.301418→2.336402，未满足无说话人回退门；去AP在两人小幅上升0.014700/0.019497，但8/8句CER均不变。AP版8/8WAV哈希不同，确实改了信号。
- 判定：不选新生产候选；裁剪冲突不是简单移除单组gain即可解决的主要内容瓶颈，不继续本地增益微调。
- 修改路径与报告：build/audit_content_chain_20261027.py、report/group_gain_ablation_20261027.{md,json}、coummucation.md。
- 复现：入口generate/evaluate --group-ablation --asset-root <asset-root> --output <generated>/group_gain_ablation_20261027；解释器/脚本SHA见JSON。生成退出1但8行24WAV完成，哈希与有限分数独立检查；评测退出0。
- 限制：8句自动ASR/UTMOS无显著性或听感结论，非固定男声五门；不读录音4/5或Track9，不训练、不播放、不接触板卡。
- 下一责任方：Hardware-A / Codex 盘点允许的固定男声训练监督与内容表示，不再围绕统一增益/裁剪反复选点。50轮总预算不扩充，原Round93已中止不重启。

### [PS-20261021-10] 固定男声监督与教师依赖盘点认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：7b9bd19；范围：校验录音1～3与192/8公共配对清单，核对历史教师生成依赖及训练时序审计适用范围。
- 修改路径：build/audit_fixed_male_supervision_20261027.py、report/fixed_male_supervision_inventory_20261027.{json,md}、coummucation.md。
- 复现：Python3.12 build/audit_fixed_male_supervision_20261027.py --asset-root <main> --output report/fixed_male_supervision_inventory_20261027.json。
- 量化结果：待校验；主工作区存在他人未提交RTL/报告及交流记录，全部保留；本工作在现有独立任务检出内进行。
- 限制：不训练，不读录音4/5或Track9音频，不播放、不操作板卡；文件名/身份清单不等于音素覆盖或因果证明。
- 下一责任方：Hardware-A / Codex 完成盘点，确定教师依赖恢复条件后再开展机制性训练，不扩充Round108上限。

### [PS-20261021-10] 固定男声监督与教师依赖盘点结果
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED / DIAGNOSIS_ONLY。
- 基准提交：7b9bd19；修改路径：build/audit_fixed_male_supervision_20261027.py、report/fixed_male_supervision_inventory_20261027.{md,json}、coummucation.md。
- 量化结果：录音1～3哈希/字节通过；192训练/8验证的400个公共float32源/教师文件哈希/样本数通过；Fixed-Male标记训练行0。历史时序报告48条与当前192/8清单文件名交集均0，不能沿用其音素对齐结论。
- 依赖：历史预期位置缺少CosyVoice源码和全部关键教师资产；官方API可访问且revision仍为29e01c4e8d000f4bcd70751be16fa94bf3d85a18；主要权重约4.43GB，D盘空闲约98.1GB，GPU8GB。没有宣称推理可运行。
- 复现：Python3.12 build/audit_fixed_male_supervision_20261027.py --asset-root <main> --output report/fixed_male_supervision_inventory_20261027.json；退出0，报告附SHA与限制。
- 限制：清单身份审计不是全盘音频去重；无固定男声配对监督不等于唯一失败原因。未读录音4/5或Track9音频、未训练/播放/板测；不是新方案轮。
- 报告：report/fixed_male_supervision_inventory_20261027.md及JSON。
- 下一责任方：Hardware-A / Codex 在D盘单一任务目录恢复官方精确revision教师依赖，先用训练录音检验内容，再决定源专用监督训练；保持Round108上限，不恢复参数扫描。

### [PS-20261021-10] 源专用教师环境恢复认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：5a53f54；范围：只恢复公共官方教师源码/资产，不启动新训练轮。
- 路径：D:/2026_FPGA_teacher_workspace/{source,models,cache,tmp,venv,runs}；正式脚本build/restore_cosyvoice3_assets_20261027.py，结果后续进入report。
- 版本：CosyVoice官方源码074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc；Fun-CosyVoice3模型29e01c4e8d000f4bcd70751be16fa94bf3d85a18。
- 复现：Python3.12 build/restore_cosyvoice3_assets_20261027.py --workspace D:/2026_FPGA_teacher_workspace；git定点fetch源码与submodule。
- 资源：D盘开始空闲约98.1GB；模型主要文件约4.43GB，依赖/环境另需空间。现有yolo GPU torch2.8.0+cu128可用，不修改该全局环境。
- 限制：未宣称依赖或推理通过；只下载公开资产，不上传语音；不读取锁定素材、不播放、不操作板卡。Round108上限不变。
- 下一责任方：Hardware-A / Codex 逐件校验资产、独立依赖环境、训练素材离线烟测并发布结果。

### [PS-20261021-10] 教师环境恢复启动证据
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED / ENVIRONMENT_IN_PROGRESS，非完成训练轮。
- 基准提交：5a53f54；修改路径：build/restore_cosyvoice3_assets_20261027.py、report/cosyvoice3_teacher_restore_20261027.md、coummucation.md；大文件仅D:/2026_FPGA_teacher_workspace。
- 已完成：官方源码074ca6d与Matcha子模块dd9105b定点检出退出0；torch2.8.0+cu128 CUDA可用；独立venv torchaudio2.8.0+cu128安装成功；模型配置与campplus官方SHA校验通过。
- 在运行：模型下载session38601；依赖安装session5662。未完成全资产校验、import/推理测试；不得只凭本记录假定进程仍活跃，恢复时须查询实际handle。
- 复现：Python3.12 build/restore_cosyvoice3_assets_20261027.py --workspace D:/2026_FPGA_teacher_workspace；源码/依赖版本见report/cosyvoice3_teacher_restore_20261027.md。
- 限制：venv重用本机torch，尚非可跨电脑交付包；未训练/合成/播放/板测，未读锁定音频；不增加训练轮预算。
- 下一责任方：Hardware-A / Codex 完成依赖校验并用训练录音离线检验教师内容，再确定源专用监督训练。

### [PS-20261021-10] 固定男声训练素材教师烟测认领
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：CLAIMED。
- 基准提交：7e7602d；范围：依赖/权重校验后，仅对允许训练录音1～3做native VC教师生成；目标使用已有target_t6_8s.wav，SHA4651ab56…177c8f。
- 修改路径：build/generate_fixed_male_teacher_20261027.py；输出D:/2026_FPGA_teacher_workspace/runs/fixed_male_teacher_20261027，正式结果后续report。
- 复现：教师venv Python build/generate_fixed_male_teacher_20261027.py --asset-root <main> --workspace D:/2026_FPGA_teacher_workspace --recordings 1 2 3。
- 判据：精确资产SHA、strict权重加载、有限非空输出、正确源/目标哈希与时长，随后独立ASR内容检查；通过烟测不等于配对质量或五门通过。
- 限制：无ASR转TTS、无波形时间拉伸、不用录音4/5或Track9、不播放/板测、不训练学生；无源专用监督有效性结论。
- 下一责任方：Hardware-A / Codex 完成生成与内容诊断后确定是否可进入源专用训练。

### [PS-20261021-10] 教师烟测结果与用户暂停交接
- 日期：2026-10-27；角色：Hardware-A / Codex；状态：PROPOSED / USER_PAUSED。
- 基准提交：7e7602d；用户明确“今天先到这里吧”，持久目标已暂停，不再启动训练/评测。
- 修改路径：build/generate_fixed_male_teacher_20261027.py、build/audit_fixed_male_teacher_content_20261027.py、report/fixed_male_teacher_{generation,content}_20261027.json、coummucation.md。
- 已验证：14个模型文件下载校验完成，strict完整权重加载通过；配置导入/GPU运算通过；录音1～3教师生成退出0，时长18.04/16.76/19.52秒，峰值CUDA约1.99GB，生成耗时6.71/4.61/4.56秒。tokenizer ONNX回退CPU，flow/声码器GPU。
- 内容评测：暂停时查询session94922已自然完成退出0，三段相对源ASR为11/73、17/70、18/67编辑，合计46/210=0.219048。不是人工金标准；教师内容尚不满足直接无条件作为优质监督的证据，不启动学生训练。
- 复现：教师venv Python build/generate_fixed_male_teacher_20261027.py --asset-root <main> --workspace D:/2026_FPGA_teacher_workspace --recordings 1 2 3；Python3.12 build/audit_fixed_male_teacher_content_20261027.py --asset-root <main> --generation <teacher-workspace>/runs/fixed_male_teacher_20261027/generation.json --output <teacher-workspace>/runs/fixed_male_teacher_20261027/content_audit.json。
- 限制：无试听、板测或五门结论；不读录音4/5或Track9，无新学生训练轮；原Round108上限不变。所有大文件保存在D盘任务目录；用户RTL/PL保留。
- 下一责任方：用户恢复后Hardware-A核查教师逐句识别差异与局部对齐，判断是否适用监督；不直接恢复参数扫描。当前无本任务活跃训练/下载/评测进程。
