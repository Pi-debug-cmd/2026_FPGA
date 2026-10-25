# PS-20261021-10：HuBERT 内容检索→WORLD Round 21

## 结论

本轮 **REJECTED**。以 Track 5～8 建立 4,953 帧 HuBERT/WORLD 目标库，对已暴露 Track 9 作 k=4 内容近邻检索并重建 WORLD。严格结果（身份 / P10 / 固定男性泄漏 / UTMOS / CER）为：

`0.6749 / 0.6613 / 0.1545 / 1.3833 / 0.3261`

身份两门通过；泄漏、UTMOS、CER 对 `≤0.10 / ≥2.30 / ≤0.15` 均失败，不请求试听、不进入固定男性转换、学生蒸馏或 PL。

## 相对 Round 20

- 身份从 `0.5986` 提高到 `0.6749`，P10 从 `0.5691` 提高到 `0.6613`。
- CER 从 `0.4348` 降到 `0.3261`，但仍远未过门。
- UTMOS 仅从 `1.3548` 到 `1.3833`；固定男性泄漏从 `0.1471` 增到 `0.1545`。
- WORLD 特征误差有所下降：谱包络 DCT `3.2389→2.8947`、log-F0 `0.1850→0.1345`、AP DCT `5.4159→5.1334`，但能量误差仍约 `0.8698`。

检索真实目标帧能够强化目标身份和部分内容，但独立近邻把不同句子的声学帧拼在一起，连续性和自然度没有达到可用上限。下一轮若继续，必须改变为段级/路径级时序检索或带序列损失的解码器，不能继续只调 k 值。

## 复现与边界

```powershell
$env:FPGA_ASSET_ROOT='C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\run_hubert_world_retrieval_round21_20261025.py --asset-root 'C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\evaluate_seed_fixed_male_strict_20261024.py --asset-root 'C:\Users\World\Desktop\2026_FPGA' --manifest build\generated\hubert_world_round21_20261025\strict_manifest.json --output build\generated\hubert_world_round21_20261025\strict_metrics.json
```

重建 WAV SHA-256 为 `bb717ac304031f6f10b18507f8d86dae5890c26f55b2a924fb7c16fe649c0ccf`。生成 WAV 与原始指标留在忽略目录；Track 9 在 Round 20 已暴露，本轮仅为开发回归。未录音、未播放、未访问板卡，v23 最大音量上电保底不变。

