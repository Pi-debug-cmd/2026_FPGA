# PS-20261021-10：Seed-VC 12 秒提示 CFG 优化 Round 5

日期：2026-10-24  
角色：Hardware-A / Codex（电脑端离线算法）  
状态：**REJECTED（已暴露新会话 CER 回归失败，任务继续）**

## 结论

固定 Track 8 高活动 12 秒提示、Seed-VC V2、30 步和 `seed=20261018`，只在验证录音 4 上提高 CFG。`CFG=1.70` 首次让验证录音 4 五门全过，随后冻结参数：已暴露录音 5 回归也全过，但 Round 3 已暴露新会话的输出发生内容塌缩，ASR 仅为“正确的正确的”，CER 达 **0.9672**。因此 CFG 路线不具备新会话稳健性，本轮拒绝，不采新的盲测。

## CFG 验证筛选

| CFG | 身份 | P10 | 泄漏 | UTMOS | CER | 判定 |
|---:|---:|---:|---:|---:|---:|---|
| 1.10 | 0.5837 | 0.5441 | 0.0644 | 2.9656 | 0.1912 | CER 失败 |
| 1.25 | 0.5963 | 0.5604 | 0.0687 | 2.9201 | 0.1765 | CER 失败 |
| 1.40 | 0.5842 | 0.5442 | 0.0524 | 2.7914 | 0.1765 | CER 失败 |
| **1.70** | **0.5912** | **0.5527** | **0.0671** | **2.8428** | **0.1471** | **五门通过，冻结** |

门槛仍为身份 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。

## 冻结后已暴露回归

| 数据 | 身份 | P10 | 泄漏 | UTMOS | CER | 判定 |
|---|---:|---:|---:|---:|---:|---|
| 标准录音 5 | 0.5621 | 0.5122 | 0.0664 | 2.9805 | 0.0375 | 五门通过 |
| Round 3 新会话 | 0.5078 | 0.4728 | 0.0661 | 2.7222 | **0.9672** | **CER 失败** |

新会话原始采集整体电平为 `-37.65 dBFS`，且存在 `-0.02 dBFS` 的孤立瞬态峰。12 秒提示和高 CFG 对旧录音有效，但在这一输入条件下丢失了内容约束。下一轮应处理输入稳健性或在 8～12 秒提示之间找结构折中，而不是继续提高 CFG。

## 用户现场听感归属

用户原话：“刚刚进行了两段试音，我觉得第一个改进好些，第二就没什么改进”；随后澄清：“就是你在进行验收的过程中，我听到了提示音，然后我说话可以转化”。采集提示音后恢复运行的是板上 **v23 最大音量保底**；本轮 Seed-VC 候选只做电脑端离线生成，未播放、未部署。因此该反馈记录为 v23 恢复后的现场观察，不能归因于 CFG 候选对比，也不改写用户结论。

## 复现

验证候选统一使用：

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source "人物音频资料\男声\标准录音 4.wav" --tag <tag> --target-mode track8_active12 --cfg <1.25|1.40|1.70> --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\<tag>\manifest.json --output build\generated\seed_fixed_male_20261024\<tag>\metrics.json
```

录音 5 与 Round 3 新会话的标签分别为 `regression_track8_active12_cfg170_rec5`、`regression_track8_active12_cfg170_newsession`。生成 WAV 未提交；板上仍是 v23。本轮不产生 Seed-VC 真人试听、Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。
