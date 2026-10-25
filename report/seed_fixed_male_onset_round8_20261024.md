# PS-20261021-10：持续语音起点裁切 Round 8

日期：2026-10-24  
角色：Hardware-A / Codex（电脑端离线算法）  
状态：**PROPOSED / WAIT_NEW_SESSION**

## 结论

Round 7 的主失败来自约 8 秒前导静音和开头瞬态，而不是后续语音段：失败输出第一窗身份/UTMOS 为 `0.1529/1.9587`，后三窗身份均 ≥`0.4736`。本轮保持 Seed-VC V2、Track 8 高活动 10 秒提示、30 步、`CFG=1.10`、`seed=20261018` 和严格评估器不变，只在推理输入端加入确定性的持续语音起点检测。

最终规则在录音 4、录音 5、Round 3 新会话和 Round 7 新会话上全部五门通过。Round 7 从四门失败提升到身份 `0.5828`、P10 `0.5512`、泄漏 `0.0628`、UTMOS `2.8588`、CER `0.1154`。

这仍不是最终接受：四条数据都已暴露，必须在规则冻结后另采一条全新会话盲测。

## 起点规则

- 20 ms 帧 RMS，活动阈值 `-40 dBFS`；
- 搜索首个 2.0 秒窗口，其中活动帧比例至少 30%；
- 保留检测起点前 250 ms；
- 只有最终裁切量至少 2.0 秒才启用，否则保持原音频不变。

初版曾对录音 5 裁掉 0.57 秒，使 CER 从 `0.0500` 恶化到 `0.1875`。该探测结果被拒绝并保留为失败证据；最终的 2 秒最小裁切规则使录音 5 不裁，恢复五门通过。

## 最终回归

| 数据 | 裁切起点 | 身份 | P10 | 泄漏 | UTMOS | CER | 判定 |
|---|---:|---:|---:|---:|---:|---:|---|
| 标准录音 4 | 0.00 s | 0.5810 | 0.5581 | 0.0678 | 2.8604 | 0.1471 | 五门通过 |
| 标准录音 5 | 0.00 s | 0.5591 | 0.4879 | 0.0903 | 2.8988 | 0.0500 | 五门通过 |
| Round 3 新会话 | 4.47 s | 0.4883 | 0.4340 | 0.0560 | 2.6624 | 0.0820 | 五门通过 |
| Round 7 新会话 | 6.87 s | 0.5828 | 0.5512 | 0.0628 | 2.8588 | 0.1154 | 五门通过 |

门槛为身份 ≥0.45、P10 ≥0.35、泄漏 ≤0.10、UTMOS ≥2.30、CER ≤0.15。评估器和门槛没有改变。

## 复现

四组命令只替换 `--source` 和 `--tag`：

```powershell
D:\Anaconda\envs\yolo\python.exe -S build\run_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --source <source.wav> --tag <tag> --target-mode track8_active10 --source-onset-trim --cfg 1.10 --seed 20261018 --steps 30
D:\Anaconda\envs\yolo\python.exe -S build\evaluate_seed_fixed_male_strict_20261024.py --asset-root C:\Users\World\Desktop\2026_FPGA --manifest build\generated\seed_fixed_male_20261024\<tag>\manifest.json --output build\generated\seed_fixed_male_20261024\<tag>\metrics.json
```

标签为 `onset_trim_rec4`、`onset_trim_min2_rec5`、`onset_trim_round3`、`onset_trim_round7`。生成 WAV 未提交或播放；板上仍运行 v23 最大音量保底。本轮不产生真人试听、Cortex-A9、实时、Vivado、RTL 或 PL 通过结论。
