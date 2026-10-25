# PS-20261021-10：HuBERT→WORLD 因果 GRU 序列教师 Round 23

## 结论

本轮 **REJECTED**。两层单向 GRU 共 477,771 参数，按 5 ms WORLD 帧预测；Track 5～8 每轨前 80% 训练、后 20% 验证。第 100 步验证损失最低 `0.4007`，之后训练损失下降而验证持续恶化，最终第 900 步早停并恢复第 100 步权重。未来输入扰动对过去输出最大影响为精确 `0.0`，因果性通过。

冻结后在已暴露 Track 9 的严格结果（身份 / P10 / 固定男性泄漏 / UTMOS / CER）为：

`0.5622 / 0.5463 / 0.1567 / 1.3388 / 0.3804`

身份两门通过；泄漏、UTMOS、CER 对 `≤0.10 / ≥2.30 / ≤0.15` 失败。相比 Round 21 检索，身份、自然度和内容均更差，不请求试听、不进入固定男性转换、蒸馏或 PL。

## 诊断

- Track 9 谱包络 DCT MAE `2.8029`，较前两轮继续下降。
- log-F0 MAE `0.1370`、VUV 概率 MAE `0.0943`。
- 能量 MAE `0.9992`、AP DCT MAE `5.2040` 仍高；合成前峰值 `1.6642`，必须限幅。
- 仅降低谱包络误差没有换来自然度和 CER，下一步必须先测当前 60D SP/12D AP 表示的无模型重建上限，不能继续盲目换预测网络。

## 复现

```powershell
$env:FPGA_ASSET_ROOT='C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\train_hubert_world_causal_gru_round23_20261025.py --asset-root 'C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\evaluate_seed_fixed_male_strict_20261024.py --asset-root 'C:\Users\World\Desktop\2026_FPGA' --manifest build\generated\hubert_world_round23_20261025\strict_manifest.json --output build\generated\hubert_world_round23_20261025\strict_metrics.json
```

checkpoint SHA-256 `3bdbb0f8a11ac94dc65e7fb4ddf350eb1a2a2df96f92636be5bf943d118e441b`；重建 WAV SHA-256 `36d2b76ff40af9277ab7814b4e4298be788d74b582e734e5f69e1a4114e861b9`。生成物未提交。板卡保持关机，本轮未录音或播放。

