# Round32：真实 WORLD 合成脉冲模型首次回归（失败留痕）

## 结论

`WORLD_SYNTH_PULSE_MODEL=1` 已把 Round31 浮点核接入真实
`synthesisrealtime` anchor 路径，默认关闭时仍走原 PS 路径。模型调用门通过、输出无削顶，
但数值门失败，因此本轮状态为 **REJECTED**，不得进入 OOC、整机连接或板卡部署。

## 受控条件

- 基准提交：`30e89b5`
- 可执行文件 SHA-256：`0455af6b937b964b19f964b9e6f13b16407a5849c7b005ddf3f4e3d398c985f0`
- 两段仓库受控输入各取前 5 秒，双通道均值后用 SciPy `resample_poly` 到 16 kHz，再量化 PCM16。
- 输入 1 PCM SHA-256：`7a23bd306128cb433d888378c087ca188e033f03a08ea54e548b861899aa00b2`
- 环境固定为 `WORLD_EXP=cpu`、`WORLD_AP_MINPHASE_STRIDE=1`、`WORLD_AP_FALLBACK_RATIO=8`；唯一对照变量为 `WORLD_SYNTH_PULSE_MODEL=0/1`。
- 没有录音、播放、切换 FPGA 或修改 Round30 板上 release。

## 结果

| 输入 | 模型调用 | CPU fallback | SNR | 最大 PCM16 误差 | 模型削顶 |
|---|---:|---:|---:|---:|---:|
| 标准录音 1 | 1643 | 124 | 0.127282 dB | 17939 | 0 |
| 标准录音 4 | 1628 | 179 | 0.180461 dB | 23965 | 0 |

门槛为 SNR ≥75 dB、最大误差 ≤3、削顶 0、模型调用 >0；两例均失败。

## 根因与下一轮唯一修正

WORLD/Ooura 的 c2r 逆变换不归一化，原 CPU 路径在脉冲合成末尾再除以
`fft_size`。Round31 HLS 核的逆变换已经在核内除以 1024；本轮 hook 又除了一次，
导致大多数模型脉冲缩小 1024 倍。下一轮只移除 hook 的重复除法，再以完全相同条件重跑。

复现：

```powershell
./build/build_world_exp.ps1 -WorldRoot <WORLD_ROOT> -Target host -Compiler D:/mingw64/bin/g++.exe -SynthesisPulseModel
python build/check_world_synthesis_pulse_quality.py --exe build/generated/world_exp_ps/world_exp_host_synthpulse_model.exe --source '人物音频资料/男声/标准录音 1.wav' --source '人物音频资料/男声/标准录音 4.wav' --out build/generated/world_synthesis_pulse_round32
```
