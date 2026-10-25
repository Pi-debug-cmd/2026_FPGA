# PS-20261021-10：Seed-VC 目标提示时长优化 Round 4

日期：2026-10-24  
角色：Hardware-A / Codex（电脑端离线算法）  
状态：**REJECTED（CER 失败，任务继续）**

## 结论

保持 Seed-VC V2、30 步、`CFG=1.10`、`seed=20261018`、Track 8 素材和严格评估器不变，只把目标高活动提示从 8 秒增加到 12 秒。验证录音 4 的目标身份、P10、源泄漏和 UTMOS 均改善，但 CER 从 8 秒基线的 `0.1471` 恶化为 **0.1912**，超过 `0.15` 上限，因此本轮不合格。

本轮只使用录音 4 做选择，没有运行录音 5 或 Round 3 新会话回归，也没有据新会话结果调参。

## 结果

| 指标 | 门槛 | 8 秒基线 | 12 秒候选 | 判定 |
|---|---:|---:|---:|---|
| 目标身份均值 | ≥ 0.45 | 0.5515 | 0.5837 | 通过 |
| 目标身份 P10 | ≥ 0.35 | 0.5121 | 0.5441 | 通过 |
| 严格源泄漏 | ≤ 0.10 | 0.0753 | 0.0644 | 通过 |
| UTMOS | ≥ 2.30 | 2.8138 | 2.9656 | 通过 |
| CER | ≤ 0.15 | 0.1471 | **0.1912** | **失败** |

12 秒提示取 Track 8 的 `1.76～13.76 s`，提示 SHA-256 为 `982e36786031fe8be41e03e61178f24a1ac2fd33042f1301161530b6be0192dd`；输出 SHA-256 为 `9d33756ee9dd6388a2238b6d6c6680ca7cd38e5f9d1219e24ebc545b5af3bc86`。

## 复现

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source "人物音频资料\男声\标准录音 4.wav" --tag validation_track8_active12 --target-mode track8_active12 --cfg 1.10 --seed 20261018 --steps 30

D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\validation_track8_active12\manifest.json --output build\generated\seed_fixed_male_20261024\validation_track8_active12\metrics.json
```

生成 WAV 未提交或播放；板卡 v23 保底未改动。本轮不产生真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 结论。
