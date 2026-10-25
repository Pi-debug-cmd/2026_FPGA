# PS-20261021-10：冻结候选第三条新会话 Round 9

日期：2026-10-24

角色：Hardware-A / Codex

状态：**ACCEPTED_OBJECTIVE / WAIT_LOCAL_LISTENING**

## 结论

Round 8 冻结规则在第三条、不同文本的新会话上只运行一次，身份、身份 P10、源泄漏、UTMOS 和 CER 五项客观门槛全部通过。固定男性到既定女性目标的电脑端离线候选因此达到当前客观出口门；下一步是在 Hardware-A 当前完整环境上进行真人试听。

第三位 Remote-PS-C 合作者只负责独立的电脑端方案探索，不负责复现或验证 Hardware-A 的这一候选。本轮候选已经在 Hardware-A 本机完整运行，因此本地试听前不要求为 Remote-PS-C 制作模型 Release；只有以后确实需要跨电脑交付某个候选时，才执行 `ARTIFACTS.md` 的交付流程。

本结论不代表板端、实时、Cortex-A9、Vivado、RTL 或 PL 通过。Seed-VC 仍是约 363M 参数、30 步、非因果的电脑端离线方案；板上没有部署它，仍运行 v23 最大音量保底。

## 新会话与数据纪律

- 操作者在采录前明确回复“准备好了”，并在传输前单独回复“授权”。
- 现场采录为 32 kHz、单声道、PCM16、20.0 秒；WAV SHA-256 为 `72ab2217f1480e5241cd28d41f3c7c4ba3f286d428ad69f9a27793c448d45876`。
- 原始 PCM SHA-256 为 `f35692a7b749cba57414e5caba5f2be27d7f746b533e73217c9017fb73485c4b`；传输 gzip SHA-256 为 `1af79310ca49a5e7f275cef5f503b18b0764e67f986bd975128273d87be403d7`。
- 输入 RMS `-38.1384 dBFS`、峰值 `-9.5780 dBFS`、削波比例 0。冻结的持续语音检测得到 `5.95 s` 起点，处理长度 `14.05 s`。
- 真人录音、生成 WAV 和串口日志只留在忽略目录 `build/generated/`，未加入 Git。

## 冻结配置与结果

候选保持 Seed-VC V2、Track 8 高活动 10 秒提示、30 步、`CFG=1.10`、`seed=20261018` 和 Round 8 起点裁切规则不变。提示 SHA-256 为 `ba901d5196d8b96508826e61f0236379638a02ec93e6924872890c998a7bc6a4`；本轮只推理一次。

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
| 目标身份均值 | 0.5200 | ≥0.45 | 通过 |
| 目标身份 P10 | 0.4719 | ≥0.35 | 通过 |
| 源身份泄漏 | 0.0591 | ≤0.10 | 通过 |
| UTMOS | 3.0789 | ≥2.30 | 通过 |
| CER | 0.1020 | ≤0.15 | 通过 |

三个非重叠窗口的身份为 `0.5408/0.5644/0.4546`，泄漏为 `0.0311/0.0495/0.0966`，UTMOS 为 `2.9402/3.2603/3.0362`。输出 SHA-256 为 `f6880252d63839e7ba64b5141a7d3babd6cdc2ddd451915ca99062622234d0ac`，长 `14.0481 s`，无削波，未播放。

## 复现

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source build\generated\seed_fixed_male_20261024\round9_new_session_capture.wav --tag frozen_round9_new_session --target-mode track8_active10 --source-onset-trim --cfg 1.10 --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\frozen_round9_new_session\manifest.json --output build\generated\seed_fixed_male_20261024\frozen_round9_new_session\metrics.json
```

推理耗时 `46.1435 s`。权重加载审计哈希为 `c853ea578b409f625f961bcb15d5cff1f8ef9a75f3209ec21d9b7c73ab422e88`，所有参数存在；Track 9 未使用。

## 板端恢复状态与下一步

采录后已恢复单实例 `/opt/world_voice/world_voice_autostart.sh`；录放 PCM 均为 `RUNNING`，Headphone `127/127 (100%, +6 dB)`，Playback `255/255 (100%, 0 dB)`。当前上电方案仍是 v23 最大音量保底。

下一步由 Hardware-A 在操作者再次明确“准备好了”后播放本轮生成结果并收集真人听感。Remote-PS-C 不参与本方案验证；如未来确需把候选交给另一台电脑，再另行执行 `ARTIFACTS.md` 的跨电脑交付流程。
