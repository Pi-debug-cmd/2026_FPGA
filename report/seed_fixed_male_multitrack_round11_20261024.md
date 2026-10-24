# PS-20261021-10：多轨目标提示听感修复 Round 11

日期：2026-10-24

角色：Hardware-A / Codex（电脑端离线算法）

状态：**PROPOSED / WAIT_NEW_SESSION**

## 结论

Round 10 的单 Track 8 十秒候选虽然客观五门通过，但用户判定“清晰度比以前好，但是没有更像目标女声，男声残留明显”。本轮恢复 2026-10-18 真人试听中更像目标、闷感更少的多轨注册信息，同时保留 Track 8 的较长上下文：Track 5～7 各 2 秒、Track 8 为 4 秒，总计 10 秒。

冻结 `CFG=1.10`、`seed=20261018`、30 步和持续语音起点裁切后，标准录音 4/5 与 Round 3/7/9 三条已暴露新会话全部五门通过。相对纯四轨各 2 秒方案，它把标准录音 5 的严格泄漏从失败的 `0.1148` 降到 `0.0952`；相对刚被真人否决的单 Track 8 十秒方案，它在 Round 9 上把目标身份从 `0.5200` 提高到 `0.5913`、P10 从 `0.4719` 提高到 `0.5800`。

这些数据均已暴露，只能证明回归稳健性。新规则必须冻结后再采一条不同文本的新会话并只运行一次，客观通过后才能请求真人试听。

## 提示结构与筛选

- Track 5、6、7：各自最高活动 2 秒；
- Track 8：最高活动 4 秒；
- 拼接后 10 秒，提示 SHA-256 `0f70b18eef37614ce0f866f989cf5376bd237e410ffb6f1e85b70ec4c2909391`；
- Seed-VC V2，30 步，`CFG=1.10`，`seed=20261018`；
- 源端继续使用 Round 8 的持续语音起点裁切；
- Track 9 未使用。

纯四轨各 2 秒、`CFG=0.95` 的探测在 Round 9 上通过，但在标准录音 5 上严格泄漏为 `0.1148`，因此拒绝。折中 10 秒提示在 Round 9 比较 `CFG=0.95/1.10` 后，两者均通过；选择目标身份更高的 `1.10` 冻结回归。

## 已暴露回归

| 数据 | 身份 | P10 | 泄漏 | UTMOS | CER | 判定 |
|---|---:|---:|---:|---:|---:|---|
| 标准录音 4 | 0.6411 | 0.6244 | 0.0887 | 2.7582 | 0.1176 | 五门通过 |
| 标准录音 5 | 0.6371 | 0.5799 | 0.0952 | 2.9058 | 0.0375 | 五门通过 |
| Round 3 新会话 | 0.5438 | 0.4677 | 0.0646 | 2.7469 | 0.1311 | 五门通过 |
| Round 7 新会话 | 0.6592 | 0.6466 | 0.0714 | 2.7960 | 0.0769 | 五门通过 |
| Round 9 新会话 | 0.5913 | 0.5800 | 0.0762 | 2.9314 | 0.1429 | 五门通过 |

门槛仍为身份 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15；评估器没有改变。

## 复现

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source <source.wav> --tag <tag> --target-mode multi3x2_track8x4 --source-onset-trim --cfg 1.10 --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\<tag>\manifest.json --output build\generated\seed_fixed_male_20261024\<tag>\metrics.json
```

标签为 `round11_mix10_cfg110_rec4`、`round11_mix10_cfg110_rec5`、`round11_mix10_cfg110_round3`、`round11_mix10_cfg110_round7`；Round 9 扫描标签为 `round11_mix10_round9`。

本轮没有播放、录音或改动板卡，v23 最大音量保底保持不变。生成 WAV 未提交。本轮不产生真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。
