# PS-20261021-10：多轨冻结候选新会话盲测 Round 12

日期：2026-10-24

角色：Hardware-A / Codex

状态：**REJECTED（严格源泄漏失败）**

## 结论

Round 11 折中多轨候选冻结后，在一条不同文本的新会话上只运行一次。身份、身份 P10、UTMOS 和 CER 均通过，但严格源泄漏为 `0.1250`，超过 `0.10` 上限，因此本候选拒绝，不请求真人试听。

该结果与 Round 10 用户听到“男声残留明显”的风险方向一致：多轨目标提示提高了目标身份，但目前仍不能稳定消除源男声。评估门槛和严格泄漏口径不变，本条录音从现在起只能用于开发回归。

## 采录与授权

- 操作者采录前明确回复“准备好了”，传输前单独回复“允许传输本轮录音”。
- 朗读文本为车站/列车新句；32 kHz、单声道、PCM16、20 秒。
- WAV SHA-256：`f61e055288a7b0dc63db256f45e4b0d6fa60ccae1d0aa382b9a45f22e90a2702`。
- 原始 PCM SHA-256：`ea92645783a8144378fa1ab0e733c61670331547e1e9886f5063823cc034efcb`。
- 传输 gzip SHA-256：`677fc17f27e3f57ce436023d0ea889ecb9b109addf6ea3f961de5b1c89417c7c`，721310 字节。
- 输入 RMS `-38.4751 dBFS`、峰值 `-9.4528 dBFS`、削波比例 0；持续语音裁切起点 `2.15 s`。

## 冻结结果

候选为 Seed-VC V2、Track 5～7 各 2 秒 + Track 8 4 秒的十秒提示、30 步、`CFG=1.10`、`seed=20261018` 和持续语音起点裁切。提示 SHA-256 为 `0f70b18eef37614ce0f866f989cf5376bd237e410ffb6f1e85b70ec4c2909391`，Track 9 未使用。

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
| 目标身份均值 | 0.5666 | ≥0.45 | 通过 |
| 目标身份 P10 | 0.5082 | ≥0.35 | 通过 |
| 源身份泄漏 | **0.1250** | ≤0.10 | **失败** |
| UTMOS | 2.7704 | ≥2.30 | 通过 |
| CER | 0.0408 | ≤0.15 | 通过 |

三个窗口的泄漏为 `0.1005/0.0874/0.1637`，第三窗最严重。输出 SHA-256 为 `b811d766e162aae7a817a8275dcd62cf4c475409238a25ff8ec3cf3027c59ccf`，长 `17.8445 s`，无削波，未播放。

## 复现与边界

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source build\generated\seed_fixed_male_20261024\round12_new_session_capture.wav --tag frozen_round12_new_session --target-mode multi3x2_track8x4 --source-onset-trim --cfg 1.10 --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\frozen_round12_new_session\manifest.json --output build\generated\seed_fixed_male_20261024\frozen_round12_new_session\metrics.json
```

真人录音、生成 WAV 和串口日志只在 `build/generated/` 忽略目录，未提交。板上已恢复单实例 v23 最大音量保底，录放 PCM 均运行，Headphone 127、Playback 255。本轮不产生真人听感、Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。
