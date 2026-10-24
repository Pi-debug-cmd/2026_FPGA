# PS-20261021-10 Seed-VC 目标提示结构优化（Round 2）

## 结论

本轮状态为 **PROPOSED / WAIT_NEW_SESSION**。Track 8 高活动 8 秒提示配合 Seed-VC V2 30 步、`CFG=1.10`、`seed=20261018`，在验证录音 4 和已暴露的录音 5 回归上均同时通过身份均值、身份 P10、严格源泄漏、UTMOS、CER 五门。

这还不是 `WAIT_LOCAL_TEST`：录音 5 已在 Round 1 用于失败判定，因此 Round 2 只能把它当回归集。最终客观接受必须用模型冻结后同一男性新录的一条新会话句；现场录音前需要操作者当轮明确准备确认。

## 唯一变量与选择

保持模型、30 步、源数据切分、随机种子、重采样、增益和严格评估器不变，只比较以下合法目标提示：

- Round 1：Track 5～8 各 2 秒高活动片段；
- Track 8 前 8 秒；
- Track 8 从 1.77 秒开始的 8 秒高活动片段。

Track 8 高活动提示的验证候选 `CFG=1.10` 五门通过且泄漏余量最好。Track 8 前 8 秒的三个候选均因 CER 0.1618 失败。Track 9 全程未使用。

## 指标

| 数据 | 身份均值 | 身份 P10 | 严格泄漏 | UTMOS | CER | 判定 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 验证录音 4 | 0.5515 | 0.5121 | 0.0753 | 2.8138 | 0.1471 | 五门通过 |
| 已暴露录音 5 回归 | 0.5336 | 0.5163 | 0.0919 | 2.9340 | 0.0500 | 五门通过 |

门槛为身份均值 ≥0.45、P10 ≥0.35、严格泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。严格泄漏仍取“逐 6 秒窗余弦均值”和“整段长度加权向量余弦”两者较大值。验证输出 SHA-256 为 `5fab6917df7970d3337c05572d28cd1279365d3c18b17907a18e46f354bdbc21`；回归输出 SHA-256 为 `614d621b9c32fd38c9776f1ac0e3cb9d2a73aacb087a0ef2a5bffd4c982447d3`。

## 复现

```powershell
python build/run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source "人物音频资料\男声\标准录音 4.wav" --tag validation_track8_active8 --target-mode track8_active8 --cfg 0.70 0.95 1.10 --seed 20261018 --steps 30
python build/evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\validation_track8_active8\manifest.json --output build\generated\seed_fixed_male_20261024\validation_track8_active8\metrics.json
python build/run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source "人物音频资料\男声\标准录音 5.wav" --tag regression_track8_active8 --target-mode track8_active8 --cfg 1.10 --seed 20261018 --steps 30
python build/evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\regression_track8_active8\manifest.json --output build\generated\seed_fixed_male_20261024\regression_track8_active8\metrics.json
```

本轮没有录音、播放、试听、板卡、Cortex-A9、Vivado、RTL、PL 或实时测试。Seed-VC 教师约 363M 参数且为非因果 30 步扩散，只证明电脑端音质上限方向；板上 v23 保底未改变。
