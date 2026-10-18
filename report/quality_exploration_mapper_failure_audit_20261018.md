# 旧 FARGAN mapper 失败路径审计（2026-10-18）

## 结论

旧 mapper 的主要问题不是 GRU 太小，而是表示与监督方式没有真正把“内容”同“源说话人音色”分开。各版都直接读取 FARGAN 的 20 维声学特征，并直接回归目标侧同一种特征；其中 17 维谱特征同时携带发音内容、声道/音色和录音通道信息。网络没有必须先经过说话人无关内容瓶颈，输出端又允许对输入谱作残差修正，所以最容易学到的是伪平行教师的平均修饰，而不是稳定去除陌生源声线。

增加容量、过去均值、音高提示、对抗损失或感知损失都没有改变这个信息通路。最强的 `context_v9` 把验证集目标余弦提高到 0.609，但 152 字仍错 18 字，明显差于基线 7 字，naturalness 诊断只有 1.832；所有 mapper 的 `subjective_acceptance` 均为 false。`expanded_v8` 已用 20 个训练说话人、1142.47 秒和 203411 参数，用户仍明确评价“**不像，而且声音不清晰，会颤**”。因此不能再把同类 20 维残差 mapper 的扩容或调权当作新路线。

## 旧方案实际做了什么

FARGAN 帧长为 160 个 16 kHz 样本，即 10 ms。20 维输入/输出为能量、17 维谱表示、音高坐标和周期性。训练对是源音频与固定目标教师转换音频分别经过部署版 C 特征提取器得到的伪平行帧；长度只做截断或末帧补齐，未建立更强的内容对齐。

| 版本 | 输入与因果上下文 | 输出与损失 | 结果/失败证据 |
|---|---|---|---|
| v1 | 音高归一化后的 20 维帧；单层 64 GRU；过去 151 个有声帧估计音高，不看未来 | 对输入作残差，改 17 维谱和音高，能量与周期性原样保留；谱 Smooth-L1 + 音高 MSE + 谱差分 | 目标余弦 0.501，152 字错 17；未通过主观验收 |
| v2 | v1 之前再用过去 200 个活跃帧做谱均值校正 | 同 v1 | 余弦 0.538，但错字升至 25；静态声道均值校正未解决内容/音色纠缠 |
| pitchaware | v1 输入外加原始源音高，共 21 维 | 同 v1 | 余弦 0.556、错 23；保留更多源音高信息没有得到可靠目标音色 |
| expanded_v8 | 21 维；2 层 128 GRU；20 个源说话人、1142.47 秒 | 17 维谱、目标中心附近音高和周期性；谱/音高/周期性/时间差分，1000 步后加条件特征对抗与 feature matching | 余弦 0.571、错 15；已通过 int8 C 数值实现，但用户拒绝“不像、不清晰、会颤” |
| perceptual / truncated | 从 v1 微调；仍是单层 64 GRU 20 维残差 mapper | 通过冻结的近似 FARGAN 加多分辨率谱、目标声纹和 CTC 损失；truncated 只反传 8 帧 | 余弦 0.516/0.550，错 19/20；训练声码器只是 surrogate，最终验证才用真实量化 C 声码器；梯度大且未通过主观验收 |
| context_v9 | pitchaware 21 维 + 过去 200 活跃帧的 17 维均值与置信度，共 39 维；2 层 128 GRU；400 帧训练段，16 帧 warm-up | 从 dynamics 版本微调；谱、音高、周期性、谱差分、音高一/二阶差分、周期性差分 | 余弦 0.609、错 18、naturalness 1.832，内容门未过；上下文修复了部分 F0 动态，却没有修复内容质量 |

phone guidance、phone CTC 与 phone CMN 也不能作为“内容编码器已解决”的证据。它们是离线双向辅助模型，没有部署进 mapper，而且都未过诊断门：source 的 phone sequence error rate 分别约 0.836、0.651、0.684；teacher 分别约 0.559、0.428、0.487，离要求的 0.25 很远。它们的标签来自同一 ASR teacher，所以即使分数提高也不是独立内容验收。

## 最主要失败模式

1. **不存在强制去音色的内容瓶颈。** 源谱特征可沿残差路径直接进入输出，源说话人的低沉、沙哑、吐气和通道特征自然会残留。
2. **伪平行帧监督不够可靠。** 教师与源仅近似同长，按帧谱回归会惩罚细微时序错位，容易产生平均化、含糊和颤动；训练损失下降不等于语音更清晰。
3. **目标注册没有进入模型。** 所有旧 mapper 都是固定目标训练，`source_enrollment=false`，也没有可替换的目标 embedding/profile 条件，因此不能证明板上注册新目标声源。
4. **客观声纹分数可被错误音频抬高。** 余弦从 0.50 增到 0.61 时，错字和听感没有同步改善。机器排序不能覆盖用户拒绝。
5. **后续补丁主要修局部统计。** 音高归一化、过去均值和 F0 动态损失能调整平均音高/平滑度，但不能把谱中的内容与身份解耦。

## 绝不能复用为新结论的组件

- 不得把 `FeatureMapper`、`PitchAwareMapper`、`MapperV8` 或 `MapperContext` 的权重继续训练后称为新架构；它们保留同一直接谱输入和残差输出通路。
- 不得把旧 phone guidance/CTC/CMN 权重称为合格内容编码器，也不得用其训练相关 ASR 分数作独立验收。
- 不得用 `expanded_v8` 的 int8 C 一致性或板端速度证明音质可行；它们只证明实现与参考一致。
- 不得只用目标余弦、训练 feature loss 或 F0 动态判断通过；必须同时看未见源的源泄漏、CER/字错、自然度和盲听。
- 不得把固定 Track5--8 目标的训练结果外推为“可注册任意目标”；至少要做完全未见目标的留出验证。

## 建议的最小、实质不同实验

先做一个 **固定目标、因果内容瓶颈 mapper**，只验证表示路线，不碰板端实时链路：

1. 使用现有多源→固定目标伪平行数据，按说话人留出验证源。输入仍可先用现有精确 C 特征，便于快速实验，但去掉任何输入到输出的谱残差/跳连。
2. 因果编码器读取当前及过去 32 帧（约 320 ms），压成 24--32 维 latent。共享编码器同时处理 source 和对应 teacher，加入 `L_content = |z_source-z_teacher|`；再用 gradient reversal 的源说话人分类器，迫使 latent 难以辨认源身份。
3. 绝对音高不进入 latent。单独输入过去统计归一化的相对 F0、V/UV 和能量轮廓；解码端用固定目标 profile 的 F0 中心/范围恢复目标音高。这样保留语调，但不把源绝对声线当内容。
4. 固定目标解码器只从 latent、相对韵律和目标 profile 生成完整 20 维目标 FARGAN 特征，不接收源 17 维谱。损失用掩码后的目标特征 Smooth-L1、谱/音高/周期性差分，以及冻结真实 FARGAN 的离线波形重建/ASR/声纹评价；第一轮不加 GAN，避免把失败原因混在一起。
5. 最小消融只做两项：`无瓶颈的旧 v8` 对照与 `瓶颈+paired latent consistency+speaker adversary`。若后者在未见源上不能同时降低 source leakage、保持/改善 CER 并提高目标相似度，就停止该声学特征路线，不再扩 GRU。

这个实验与旧路线的关键差异是：**输出端无法直接看见源谱，只能通过经配对一致性和说话人对抗约束的内容 latent 获得发音信息。** 它可以先用固定目标证明多陌生源泛化；通过后再把固定目标常量替换为 TargetProfile/target embedding，并用多目标训练、完全未见目标留出来验证注册能力。

建议首轮门槛沿用当前质量探索门：未见源目标 identity 均值至少 0.45、P10 至少 0.35，source leakage 不高于 0.10，UTMOS 至少 2.3，CER 不高于 0.15 且相对源恶化不超过 5 个百分点；同时必须在盲听中胜过 A1。该实验仍是离线可行性筛选，不表示已满足板端预算。

## 可复用与不可复用的现有资产

可以直接复用数据与测量基础设施：

- `neural_reference/prepare_fargan_features_20261006.py`：部署版 C 特征抽取和 source/teacher reconstruction 控制。
- `board_budget_20261005/fargan_corpus_expanded/manifest.json`：已有多源伪平行训练集和不变 held-out 集。
- `board_support/native_llvc_20261005/fargan_probe_host.exe --synthesis`：真实量化 FARGAN 离线合成。
- `neural_reference/evaluate_board_phonetic_naturalness_20261005.py` 及现有 heldout screening：可作为统一输出评测框架，但 ASR/声纹仍需按“非主观验收”解释。
- `fargan_mapper_v8_20261006.py` 的 C 导出格式和原生数值核对流程可作为工程骨架；不得复用它的直通残差架构或已失败权重。

目前没有现成脚本实现上述“无谱跳连 + 配对内容一致性 + 源说话人对抗”的因果 mapper，需要新建独立训练脚本。旧脚本中最值得保留的是数据抽取、FARGAN 合成、held-out 切分和评测，而不是 mapper 模型本身。

## 主要证据位置

- `交接/核心材料/neural_reference/fargan_feature_mapper_20261006.py`
- `交接/核心材料/neural_reference/fargan_mapper_v8_20261006.py`
- `交接/核心材料/neural_reference/fargan_mapper_context_20261006.py`
- `交接/核心材料/neural_reference/train_fargan_*_20261006.py`
- `交接/核心材料/board_budget_20261005/fargan_mapper_*/decision.json`
- `交接/核心材料/board_budget_20261005/fargan_*/heldout_screening.json`
- `交接/核心材料/board_budget_20261005/fargan_context_v9/development_gate.json`
- `交接/核心材料/board_support/native_llvc_20261005/continuous_refinement_evidence_20261006.json`

