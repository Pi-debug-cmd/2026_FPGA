# FARGAN oracle 资料审计（2026-10-18）

## 结论

旧资料里已经有一个**不经过声学映射器、直接把参考声学特征送入官方预训练 FARGAN 声码器**的 oracle 重建：`fargan_teacher_reconstruction`。它能隔离回答“FARGAN 声码器本身是否足以重建目标样式语音”。但它的输入是 CosyVoice3 直接 source-VC 教师波形提取出的 20 维特征，不是目标人物 Track 5–8 原始录音本身，也不是板上注册后由陌生说话人实时预测出的特征。因此它是有效的**声码器上界控制**，不能当作已经完成的实时变声链。

当前 `fargan_v8_fullchain_verification` 不是 oracle。它包含 V8 mapper，再进入 FARGAN；它只证明 C/ARM 数学一致、线程链和速度，不证明音质。记录中 `target_quality_accepted=false`、`quality_accepted=false`、`board_live_deployed=false`。

`wide192_psola_oracle` 也不是纯 FARGAN oracle。它是整段源统计和 Praat/PSOLA 控制，明确 `not_causal=true`、`praat_control_only=true`、`not_board_deployable=true`。

## 直接证据

- `交接/核心材料/neural_reference/prepare_fargan_features_20261006.py`：分别从 source 与 CosyVoice3 teacher 波形调用 `fargan_probe_host.exe --features`，然后把 `teacher_features` 原样送给 `--synthesis`，输出 `fargan_teacher_reconstruction`。没有 mapper。
- `交接/核心材料/board_budget_20261005/fargan_teacher_reconstruction/decision.json`：标记 `control_only=true`、`target_voice_conversion=false`，共八个 validation 输出。
- `交接/核心材料/board_budget_20261005/fargan_teacher_reconstruction/heldout_screening.json`：152 字上，FARGAN teacher-feature 重建为 7 edits、目标余弦 0.7701566；同批 teacher 波形为 9 edits、0.8725310；源声音为 5 edits、0.1892453。
- `交接/核心材料/board_budget_20261005/phonetic_naturalness/fargan_teacher_reconstruction.json`：FARGAN teacher-feature 重建的诊断自然度均值 2.9777314；teacher 波形 3.5696795；源声音 2.4452231。该分数是旧诊断模型输出，不等于主观验收。
- `交接/核心材料/neural_reference/check_fargan_preserved_feature_controls_20261006.py`：另外做了两个明确标记为 `oracle_teacher_features=true` 的控制：保留源能量列 0；以及保留源能量列 0 和周期性列 19。两者仍没有 mapper。
- `交接/核心材料/board_budget_20261005/fargan_teacher_source_energy/heldout_screening.json` 与 `phonetic_naturalness/fargan_teacher_source_energy.json`：8 edits/152、目标余弦 0.7390515、诊断自然度 2.6507860。
- `交接/核心材料/board_budget_20261005/fargan_teacher_source_energy_periodicity/heldout_screening.json` 与对应自然度文件：6 edits/152、目标余弦 0.7207287、诊断自然度 2.3929283。
- `交接/核心材料/board_support/native_llvc_20261005/fargan_probe.c`：`--features` 用官方 LPCNet encoder 提取每 10 ms 的 20 维特征；`--synthesis` 只调用 `fargan_synthesize`，没有音色 mapper、波形混合或目标注册逻辑。
- `交接/核心材料/board_support/native_llvc_20261005/fargan_assets.json`：记录官方 Xiph Opus/FARGAN 模型与源文件校验和；FARGAN 模型文件约 13.8 MB，部署 C 权重源约 22.0 MB。

## 能回答与不能回答的问题

现有 oracle 能回答：在给定正确的目标样式 20 维特征时，官方 FARGAN 的重建质量显著高于旧 mapper 输出；旧链主要瓶颈确实在“陌生源内容/声学特征 → 目标特征”的映射，而不是 FARGAN 合成器完全不可用。旧记录也显示保留更多源特征会逐步降低目标相似度和自然度，说明源音色泄漏会从声学特征直接传到输出。

现有 oracle 不能回答：真实目标录音经 FARGAN 重建是否达到当前项目的 identity≥0.75、UTMOS≥2.6、CER 退化≤5 个百分点门槛；也不能证明目标注册、多陌生源泛化或板上实时性。旧 speaker cosine、ASR 和自然度评估器与现行评估口径不同，不能直接替代当前闭环指标。

## 下一步最小实验

不重新训练、不调用旧 mapper。直接复用 `fargan_corpus/manifest.json` 中已存在的 `target_track5.features.f32` 至 `target_track8.features.f32`，逐条运行 `fargan_probe_host.exe --synthesis`，得到真实目标 Track 5–8 的 FARGAN 重建。用相同时间窗比较每条“原目标录音 vs FARGAN 重建”的说话人相似度、UTMOS、CER，并报告均值和最差条目。

这个实验只测声码器上界，预计几分钟即可完成，也不需要板卡或用户试听。若通过当前 oracle 门槛，后续应把资源集中在因果内容编码器和目标条件声学 mapper；若不通过，应先更换或微调声码器，避免继续训练一个被声码器上界限制的 mapper。

## 执行结果

上述最小实验已经完成。四条输出长度均与原目标录音逐样本一致，完整生成记录见 `report/quality_exploration_fargan_target_oracle_20261018.json`，现行评估见 `report/quality_exploration_fargan_target_oracle_metrics_20261018.json`。

- 目标质心身份：均值0.8782，最低0.8682；通过均值≥0.75。
- UTMOS：均值2.7515，最低2.6105；通过均值≥2.6。
- 内容：Whisper偶尔对原声与重建分别输出繁体和简体，因此保留原始CER并增加仅覆盖本批转写字符的显式繁简归一。归一后平均CER为0.0308，通过≤0.05；Track8最差为0.0947，仍需作为异常案例保留。

因此FARGAN声码器上界通过，后续资源转向“陌生输入内容到目标20维声学特征”的因果映射。该结论不代表目标注册、多陌生源泛化、主观音质或板上实时已经通过。
