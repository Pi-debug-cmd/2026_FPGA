# PS-20261021-10：Round 6 冻结后第二条新会话验收 Round 7

日期：2026-10-24  
角色：Hardware-A / Codex  
状态：**REJECTED（四项门槛失败，任务继续）**

## 结论

Round 6 候选在采集前已冻结：Seed-VC V2、30 步、`CFG=1.10`、`seed=20261018`、Track 8 高活动 10 秒提示。本轮使用同一名男性现场新录的另一条 20 秒会话，只运行一次冻结候选。UTMOS 通过，但身份均值、身份 P10、严格源泄漏和 CER 均失败，因此不得进入 Seed-VC 试听或标记 `WAIT_LOCAL_TEST`。

第一段 6 秒输出是主要异常：身份只有 `0.1529`、UTMOS 只有 `1.9587`；后续三段身份为 `0.5631/0.5440/0.4736`。下一轮应先诊断起始窗失败，而不是继续全局调 CFG。本条新会话从本轮起已经暴露，只能作回归。

## 采集、传输与板卡恢复

- 操作者在本轮前明确回复“准备好了”，并随后明确回复“允许传输本轮录音”。
- 采集流程：300 ms 提示音，等待 150 ms，随后录制 20.0 秒；原始 S24_LE、32 kHz、双声道经既有打包器输出 PCM16、32 kHz、单声道 WAV。
- 板端原始 SHA-256：`5667e0296c5566391e1bed38035b456d53a63bc4b42b95400b12d30a5fdceffb`。
- 压缩包：798,933 字节，SHA-256 `2c196752a9bcdcbbaa73562c120802e0c297fbd9df28e88583fbd192779aac07`。
- 解压 WAV：1,280,044 字节，SHA-256 `da1737af90da8ebeb0578719816e6d381fcfe74469d1a9f18519d250ef78fa3e`；与板端记录一致。
- QA：RMS `-35.19 dBFS`，峰值 `-9.14 dBFS`，无削波；低于 `-50 dBFS` 的 20 ms 帧比例 `37.9%`，高于 `-35 dBFS` 的比例 `16.3%`。
- 采集完成后恢复单实例 v23，录放 PCM 均为 `RUNNING`。采集脚本按采集前 mixer 快照恢复为 Headphone 105 / Playback 230，与用户要求的最大音量不符；发现后立即纠正为 Headphone 127 / Playback 255，并再次确认录放运行。
- 真人录音、串口日志和生成 WAV 全部留在 `build/generated/` 忽略目录，未加入 Git。

## 严格结果

| 指标 | 门槛 | 结果 | 判定 |
|---|---:|---:|---|
| 目标身份均值 | ≥ 0.45 | **0.4334** | **失败** |
| 目标身份 P10 | ≥ 0.35 | **0.2491** | **失败** |
| 严格源泄漏 | ≤ 0.10 | **0.1067** | **失败** |
| UTMOS | ≥ 2.30 | 2.5821 | 通过 |
| CER | ≤ 0.15 | **0.1538** | **失败** |

严格源泄漏的分窗均值为 `0.0726`，整段聚合向量余弦为 `0.1067`，按规则取较大值。输出 SHA-256 为 `fbe91f84c136dc1631618d0deeb2f05a4c90963ac2a8f0ecbdaa705209e2088d`，CPU 推理耗时约 58.93 秒。

## 复现

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source build\generated\seed_fixed_male_20261024\round7_new_session_capture.wav --tag frozen_round7_new_session --target-mode track8_active10 --cfg 1.10 --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\frozen_round7_new_session\manifest.json --output build\generated\seed_fixed_male_20261024\frozen_round7_new_session\metrics.json
```

本轮不产生 Seed-VC 真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。
