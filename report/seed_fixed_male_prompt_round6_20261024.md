# PS-20261021-10：Seed-VC 10 秒提示折中 Round 6

日期：2026-10-24  
角色：Hardware-A / Codex（电脑端离线算法）  
状态：**PROPOSED / WAIT_NEW_SESSION**

## 结论

Track 8 高活动 10 秒提示配合 Seed-VC V2、30 步、`CFG=1.10`、`seed=20261018`，在验证录音 4、已暴露录音 5 和 Round 3 已暴露新会话上均通过身份均值、身份 P10、严格源泄漏、UTMOS、CER 五门。

这个折中消除了 8 秒提示在新会话上的泄漏失败，也避免了 12 秒高 CFG 的内容塌缩。它仍不是最终客观接受：录音 5 和 Round 3 新会话都已暴露，必须在参数冻结后再采另一条全新会话，只运行一次才能决定是否进入模型交付和真人试听。

## 验证选择

固定 10 秒提示，只在录音 4 比较 CFG：

| CFG | 身份 | P10 | 泄漏 | UTMOS | CER | 判定 |
|---:|---:|---:|---:|---:|---:|---|
| **1.10** | **0.5810** | **0.5581** | **0.0678** | **2.8604** | **0.1471** | **五门通过，选择** |
| 1.40 | 0.5829 | 0.5538 | 0.0703 | 2.8916 | 0.1471 | 五门通过 |
| 1.70 | 0.5930 | 0.5831 | 0.0602 | 2.8881 | 0.1618 | CER 失败 |

选择规则是使用通过验证五门的最低 CFG，以降低新会话内容塌缩风险；已暴露回归不参与选参，只作通过/失败检查。

## 冻结后已暴露回归

| 数据 | 身份 | P10 | 泄漏 | UTMOS | CER | 判定 |
|---|---:|---:|---:|---:|---:|---|
| 标准录音 5 | 0.5591 | 0.4879 | 0.0903 | 2.8988 | 0.0500 | 五门通过 |
| Round 3 新会话 | 0.4818 | 0.4174 | 0.0679 | 2.7261 | 0.0984 | 五门通过 |

门槛为身份 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。目标提示取 Track 8 的 `1.76～11.76 s`，提示 SHA-256 为 `ba901d5196d8b96508826e61f0236379638a02ec93e6924872890c998a7bc6a4`。

## 复现

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source "人物音频资料\男声\标准录音 4.wav" --tag validation_track8_active10_cfgs --target-mode track8_active10 --cfg 1.10 1.40 1.70 --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\validation_track8_active10_cfgs\manifest.json --output build\generated\seed_fixed_male_20261024\validation_track8_active10_cfgs\metrics.json
```

冻结回归标签为 `regression_track8_active10_cfg110_rec5` 和 `regression_track8_active10_cfg110_newsession`。生成 WAV 未提交或播放；板上仍运行 v23 最大音量保底。本轮不产生真人试听、Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。
