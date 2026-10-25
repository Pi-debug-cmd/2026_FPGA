# PS-20261021-10 Seed-VC 严格留出复验（Round 1）

## 结论

本轮 **REJECTED**，不请求试听、不部署板卡。验证录音 4 上冻结的 Seed-VC V2 30 步候选为 `CFG=1.10, seed=20261018`；首次运行锁定录音 5 后，身份、P10、UTMOS、CER 通过，但严格源泄漏为 **0.1079 > 0.10**。

板上现有 v23 保底未改变。本轮仅做电脑端 CPU 离线推理和客观评测，没有录音、播放、真人听感、Cortex-A9、Vivado、RTL 或 PL 测试。

## 防泄漏协议

- 男声录音 1～3：只建立源说话人评估质心。
- 男声录音 4：扫描 4 个 CFG × 2 个固定随机种子并冻结候选。
- 男声录音 5：候选冻结后才首次转换和评价；未根据其结果回调本轮参数。
- 女声 Track 5～8：构造 4×2 秒确定性目标提示并建立目标评估质心。
- 女声 Track 9：未读取、未训练、未选参、未评价。

说话人和 UTMOS 使用非重叠 6 秒窗（尾窗至少 1.5 秒）。身份报告窗均值和 P10。泄漏同时计算逐窗余弦均值与整段长度加权向量余弦，取两者较大值判定。CER 使用离线 Whisper-small；为避免同一汉字繁简体被误报成内容错误，先去标点并用固定 `opencc-python-reimplemented==0.1.7` 的 `t2s` 标准化，同时在原始 JSON 中保留未标准化 CER。

## 结果

| 数据 | 身份均值 | 身份 P10 | 严格泄漏 | UTMOS | CER | 判定 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 验证录音 4 | 0.5992 | 0.5624 | 0.0979 | 2.7454 | 0.1471 | 五门通过，冻结 |
| 锁定录音 5 | 0.5784 | 0.5278 | **0.1079** | 2.7941 | 0.0625 | 泄漏失败 |

锁定集逐窗泄漏为 0.1300、0.0737、0.0769、0.1213；逐窗均值 0.1005，整段聚合 0.1079。不能把 0.1005 四舍五入成通过，也不能改用较宽松口径掩盖整段失败。

## 复现

```powershell
python build/run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source "人物音频资料\男声\标准录音 4.wav" --tag validation_r1 --cfg 0.70 0.85 0.95 1.10 --seed 20261018 20261019 --steps 30
python build/evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\validation_r1\manifest.json --output build\generated\seed_fixed_male_20261024\validation_r1\metrics_strict.json
python build/run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source "人物音频资料\男声\标准录音 5.wav" --tag locked_holdout --cfg 1.10 --seed 20261018 --steps 30
python build/evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\locked_holdout\manifest.json --output build\generated\seed_fixed_male_20261024\locked_holdout\metrics_strict.json
```

生成 WAV 和原始大清单位于忽略目录 `build/generated/seed_fixed_male_20261024/`，未提交。下一轮只在验证录音 4 上比较合法的 Track 5～8 目标提示结构，降低源身份泄漏；现有录音 5 只作已暴露回归集，最终接受仍需冻结后的新会话句。
