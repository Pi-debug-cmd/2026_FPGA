# PS-20261021-10：HuBERT→WORLD 路径级连续检索 Round 22

## 结论

本轮 **REJECTED**。连续性参数只用 Track 5～8 四折留一验证选择；五个固定惩罚 `0/0.10/0.25/0.50/1.00` 中，验证分数分别为 `0.9917/1.0181/1.0309/1.0369/1.0454`，因此冻结选择 `0.0`。非零连续约束虽然把平均跳转率从 `49.32%` 降到最低 `13.81%`，却持续增加声学帧和动态误差，证明当前候选空间中“顺序连续”与“内容正确”冲突。

冻结后在已暴露 Track 9 的严格结果（身份 / P10 / 固定男性泄漏 / UTMOS / CER）为：

`0.7108 / 0.6894 / 0.1757 / 1.4125 / 0.4783`

身份和 UTMOS 相对 Round 21 略升，但泄漏和 CER 明显恶化；后三门仍未满足 `≤0.10 / ≥2.30 / ≤0.15`。不请求试听、不进入固定男性转换、学生蒸馏或 PL。

## 判定

路径约束不能修复独立声学帧拼接：一旦强制沿目标句子连续前进，检索内容很快偏离输入；不加约束则退化为高频跳帧。后续不再扩大候选数或惩罚网格，应改用能够生成连续声学轨迹的序列解码器，并明确建模 VUV、能量和 AP。

## 复现

```powershell
$env:FPGA_ASSET_ROOT='C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\run_hubert_world_path_round22_20261025.py --asset-root 'C:\Users\World\Desktop\2026_FPGA'
& 'C:\Users\World\AppData\Local\Python\pythoncore-3.12-64\python.exe' build\evaluate_seed_fixed_male_strict_20261024.py --asset-root 'C:\Users\World\Desktop\2026_FPGA' --manifest build\generated\hubert_world_round22_20261025\strict_manifest.json --output build\generated\hubert_world_round22_20261025\strict_metrics.json
```

重建 WAV SHA-256 为 `55ea991b443ede4e998da03dcfa75fef974122d551c18451a3acb3c36014a592`。生成物在忽略目录；板卡按用户说明保持关机，本轮没有要求上电、录音或播放。

