# PS 音色方案探索交接（2026-10-19）

## 本轮结论

本轮没有操作板卡、播放音频、切换 PL 或启动 Vivado。工作顺序已改为：先找到音质可接受且能压缩到 Cortex-A9 PS 的文件转换方案，通过后才评估 PL。

首个新候选把冻结的 reduced-LLVC 内容编码器与 FARGAN 合成器组合起来：

`源波形 → LLVC 因果内容特征 → 64 维 PCA → 8 帧过去上下文 MLP → 20 维目标 FARGAN 特征 → FARGAN`

该结构不向输出提供源 17 维频谱或残差跳连，与已失败的 direct-20D mapper 不同。预测头 151,700 参数，过去上下文 80 ms；训练使用 18 名源说话人，验证严格留出 SSB0043、SSB0394 两名说话人。

四条留出句的现行客观结果：

| 指标 | 候选 | 同句教师 FARGAN oracle | 门槛 | 判定 |
| --- | ---: | ---: | ---: | --- |
| 目标身份均值 | 0.656 | 0.796 | ≥0.45 | 通过 |
| 目标身份 P10 | 0.621 | 0.762 | ≥0.35 | 通过 |
| 源泄漏均值 | 0.065 | 0.031 | ≤0.10 | 通过 |
| UTMOS 均值 | 1.660 | 3.388 | ≥2.30 | **失败** |
| CER 均值 | 0.582 | 0.174 | ≤0.15 | **失败** |

因此该候选不进入试听、不部署 PS、不交给 PL。它证明 LLVC latent 能抑制源身份，但不能保留足够的发音和帧级声学细节。训练的验证损失在 200 步后恶化，继续扩容或延长训练没有依据。缓存 latent 曾按 WORLD 时间轴裁切，后续若复核必须从同一 PCM 按 FARGAN 10 ms 时间轴重新提取；这个限制不改变当前“未过客观门”的判定。

## Seed-VC V2 纠正

归档记录显示完整 Seed-VC V2 曾被用户明确拒绝：“二更好，三没有改进，反而退步了”。本机虽保留固定提交源码，但 CFM、AR、ASTRAL、HuBERT、BigVGAN 权重与原 CUDA 环境均已缺失。恢复它需要大量下载，且只会复现已经拒绝的路线，因此不作为质量主线，也不安排再次试听。

## 下一步边界

下一轮先验证更强的语义表示上限：用本地 HuBERT teacher 特征预测目标 FARGAN 20 维特征，先回答“语义信息充分时能否同时达到内容、自然度、身份和泄漏门”。只有 teacher 上限过门，才蒸馏为小型因果编码器并做 Cortex-A9 文件转换；teacher 上限不过门则更换声学解码路线。旧 direct-20D、WORLD 包络 A3、完整 Seed-VC V2 和本轮 LLVC-latent/FARGAN v1 均不再延长训练。

## 产物

- 训练脚本：`build/quality_exploration/train_llvc_content_fargan.py`
- 评测脚本：`build/quality_exploration/evaluate_llvc_content_fargan.py`
- 训练与音频文件：`build/generated/quality_exploration_20261019/llvc_content_fargan_v1/`
- 客观评测：`report/quality_exploration_llvc_content_fargan_v1_20261019.json`
