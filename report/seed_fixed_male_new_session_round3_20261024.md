# PS-20261021-10：Seed-VC 冻结后新会话客观验收 Round 3

日期：2026-10-24  
角色：Hardware-A / Codex  
状态：**REJECTED（仅严格源泄漏失败，任务继续）**

## 结论

Round 2 候选在采集前已经冻结。本轮使用同一名男性现场新录的 20 秒新会话，只运行一次 `CFG=1.10 / seed=20261018 / 30 steps / Track 8 高活动 8 秒提示`。身份均值、身份 P10、UTMOS 和 CER 均通过，但严格源泄漏为 **0.1223**，高于 `0.10` 上限，因此本候选不得进入试听，也不得标记 `WAIT_LOCAL_TEST`。

新会话已经暴露，后续只可作为回归证据。下一候选必须只用既有开发/已暴露录音优化并重新冻结，最终接受仍需另一条全新的现场会话。

## 采集与恢复证据

- 串口：CH340 `COM4`；操作者在本轮前明确回复“准备好了”，之后又明确授权传输录音。
- 采集：先播放 300 ms 提示音，等待 150 ms，随后录制 20.0 秒；板端原始格式为 S24_LE、32 kHz、双声道，经既有打包器输出 PCM16、32 kHz、单声道 WAV。
- 板端原始 SHA-256：`b63483b1d780b663672b3f50766d17b289094ea352fc90e9cbda7b524d7c5169`。
- 传输压缩包：772,936 字节，SHA-256 `2f9aee9e09cc30d7d398934ab63afab75a30e8e410107b5580dfb02d6faf7723`。
- 解压 WAV：1,280,044 字节，SHA-256 `fd4aaf53a7637cccf458442feffe8232d3e8ca9317da69d332666e3babb02db2`；与板端记录完全一致。
- QA：RMS `-37.65 dBFS`，峰值 `-0.02 dBFS`，数字削波比例 `0`；20 ms 帧低于 `-50 dBFS` 的比例为 `43.4%`。录音整体偏低且有接近满幅的瞬态峰，但格式、时长、语音识别文本均有效；本轮未裁剪、未重录、未针对该录音调参。
- 采集结束后恢复 v23 最大音量保底：仅一个自启动父进程，录放 PCM 均为 `RUNNING`，`Headphone=127,127`、`Playback=255,255`。
- 真人录音、串口原始日志、转换 WAV 均只在 `build/generated/` 忽略目录，未加入 Git。

## 严格结果

| 指标 | 门槛 | 新会话结果 | 判定 |
|---|---:|---:|---|
| 目标身份均值 | ≥ 0.45 | 0.5007 | 通过 |
| 目标身份 P10 | ≥ 0.35 | 0.4431 | 通过 |
| 严格源泄漏 | ≤ 0.10 | **0.1223** | **失败** |
| UTMOS | ≥ 2.30 | 2.8356 | 通过 |
| CER | ≤ 0.15 | 0.1148 | 通过 |

严格源泄漏取“分窗余弦均值”和“整段长度加权聚合向量余弦”两者较大值：本轮分别为 `0.1127` 和 `0.1223`。输出 SHA-256 为 `5bf9e0a3259633c190e51ee70a77cdbc6e7e194a38a95b06121a0d80372ba9d1`，CPU 推理耗时约 52.99 秒。

## 复现命令

为隔离系统 `torchvision` 并匹配本地 CPython 3.12 二进制依赖，使用 `-S`：

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source build\generated\seed_fixed_male_20261024\new_session_capture.wav --tag frozen_new_session --target-mode track8_active8 --cfg 1.10 --seed 20261018 --steps 30

D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\frozen_new_session\manifest.json --output build\generated\seed_fixed_male_20261024\frozen_new_session\metrics.json
```

完整结构化摘要见 `report/seed_fixed_male_new_session_round3_20261024.json`。模型为约 363M 参数的 30 步非因果教师，本轮不构成 Cortex-A9、实时、PL 或真人听感通过。
