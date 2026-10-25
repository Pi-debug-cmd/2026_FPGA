# PS-20261021-10：HuBERT→WORLD 教师上限 Round 20

## 结论

本轮 **REJECTED**。Track 5～8 训练、Track 9 留出目标重建的身份均值与 P10 已通过，但固定男性泄漏、UTMOS 和 CER 三门失败；不进入试听、固定男性转换、学生蒸馏或 PL 部署。

严格结果（身份 / P10 / 男性泄漏 / UTMOS / CER）为：

`0.5986 / 0.5691 / 0.1471 / 1.3548 / 0.4348`

对应门槛为 `≥0.45 / ≥0.35 / ≤0.10 / ≥2.30 / ≤0.15`。身份两门通过，后三门失败。

## 固定方案

- 内容教师：本机 HuBERT Base 第 9 隐层，权重 SHA-256 `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`。
- 训练数据：仅目标女声 Track 5～8，共 19,832 个 5 ms WORLD 帧；固定男性录音不参加训练。
- 输出：60 维中心化 log-SP DCT、连续 log-F0、VUV、能量和 12 维 AP-logit DCT；无源频谱残差和跳连。
- 映射器：96 维 PCA、前后各 2 个 HuBERT 帧上下文、两层 384 隐层 MLP，共 361,419 参数；2500 步固定种子训练。
- 验证：训练结束后才以 Track 9 生成重建；Track 9 未参与 PCA、归一化、裁剪边界或训练。首次输出暴露了 VUV 概率被误当 logit 的接口错误；只修复该确定性错误后重跑，故 Track 9 此后只能作为已暴露开发回归，不能再当最终盲测。

## 诊断

训练损失从 `0.4105` 降到 `0.1373`，说明网络能够拟合训练分布；修复 VUV 接口后预测有声比例从错误的 `1.0000` 降到 `0.8468`。但 Track 9 的谱包络 DCT 平均绝对误差仍为 `3.2389`，能量误差 `0.8690`，AP DCT 误差 `5.4159`，最终 UTMOS 和 CER 仍严重失败。

这说明当前瓶颈不是简单的 VUV 阈值，而是“帧独立小 MLP直接回归完整 WORLD 参数”在只有约 99 秒目标数据时丢失了清音、瞬态和细节。身份分数较高证明目标音色方向存在，但当前声学解码器不具备可用自然度与内容保持上限。

第一轮错误输出指标为 `0.6004 / 0.5788 / 0.1391 / 1.3652 / 0.3587`，同样失败；保留该失败历史，不能只报告修正后的结果。

## 复现

```powershell
$env:FPGA_ASSET_ROOT='C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\train_hubert_world_teacher_round20_20261025.py --asset-root 'C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\evaluate_seed_fixed_male_strict_20261024.py --asset-root 'C:\Users\World\Desktop\2026_FPGA' --manifest build\generated\hubert_world_round20_20261025\strict_manifest.json --output build\generated\hubert_world_round20_20261025\strict_metrics.json
```

生成 checkpoint、WAV、特征和原始评估 JSON 位于忽略目录 `build/generated/hubert_world_round20_20261025/`；checkpoint SHA-256 为 `d03944c13ce0b8c824abd2e8f69133616cf970a93fd2e63442f3e223038316da`，最终重建 WAV SHA-256 为 `a903abb1320278f64f80dce17f93c75b782e8cfbae519c472d6f6b8d50993604`。

本轮没有录音、播放、访问板卡或修改 v23 最大音量上电保底，也没有 Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。

