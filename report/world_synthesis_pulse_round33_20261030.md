# Round33：真实 WORLD 合成脉冲模型尺度修正

## 结论

Round32 的重复 `fft_size` 除法已移除。两段真实 5 秒输入均通过预定数值门，
因此本轮状态为 **ACCEPTED（host 模型门）**。这证明 Round31 脉冲核可在真实
WORLD 流式合成路径替代三次 FFT、噪声去均值、频域乘法、fftshift、周期 DC 去除
和最终缩放；不等于 OOC、整机时序、板卡或听感已经通过。

## 唯一改动

HLS 核的逆 FFT 已输出归一化结果；WORLD/Ooura CPU 逆 FFT 不归一化，并在原路径末尾
统一除以 1024。hook 不再对 HLS 结果重复除以 1024。其他模型接口、随机数消费顺序、
anchor 插值、transition fallback、输入和增益保持 Round32 不变。

## 受控条件

- 基准提交：`9500220`
- 模型可执行文件 SHA-256：`8a7d60f58b2c4b6e03b891959e0cdd336ceb7f2688cae06b2cceee78a3e1a09e`
- `WORLD_EXP=cpu`、`WORLD_AP_MINPHASE_STRIDE=1`、`WORLD_AP_FALLBACK_RATIO=8`
- CPU 对照：`WORLD_SYNTH_PULSE_MODEL=0`；模型：`WORLD_SYNTH_PULSE_MODEL=1`
- 每段 WAV 取前 5 秒、双声道均值、`resample_poly` 到 16 kHz、PCM16 量化
- 输出增益 Q16=`39322`；每例输出 80000 样本

## 结果

| 输入 | 输入 PCM SHA-256 | 模型调用 | CPU fallback | SNR | 最大误差 | RMS误差 | CPU/模型削顶 |
|---|---|---:|---:|---:|---:|---:|---:|
| 标准录音 1 | `7a23bd30…00b2` | 1643 | 124 | 105.295306 dB | 1 | 0.015811 | 0 / 0 |
| 标准录音 4 | `8edae31b…d70d1c` | 1628 | 179 | 104.549879 dB | 1 | 0.014577 | 0 / 0 |

门槛为 SNR ≥75 dB、最大 PCM16 误差 ≤3、零削顶、模型调用 >0；全部通过。
fallback 是原设计保留的高变化 transition CPU 路径，并非静默失败。

## 复现

```powershell
./build/build_world_exp.ps1 -WorldRoot <WORLD_ROOT> -Target host -Compiler D:/mingw64/bin/g++.exe -SynthesisPulseModel
python build/check_world_synthesis_pulse_quality.py --exe build/generated/world_exp_ps/world_exp_host_synthpulse_model.exe --source '人物音频资料/男声/标准录音 1.wav' --source '人物音频资料/男声/标准录音 4.wav' --out build/generated/world_synthesis_pulse_round33
```

本轮没有切换 FPGA、录音、播放或修改 Round30 板上持久 release。下一步应建立脉冲核
OOC/整机连接与 DMA/batch 接口，再做板端数值回归；不能由本报告直接宣称“完整 PL 已部署”。
