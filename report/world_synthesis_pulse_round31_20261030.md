# PL-20261027-01 Round31：WORLD 合成脉冲核 PL 原型

## 结论

**ACCEPTED（host / HLS C-sim / Verilog RTL cosim 原型门）。** 新核把每个 WORLD 脉冲在最小相位滤波器之后的三次 FFT、随机噪声去均值、非周期频域乘法、逆变换、fftshift、周期分量 DC 去除和最终缩放放入一个 PL 边界。5 组有声/无声及不同 `noise_size` 对照的最坏 relative-L2 为 `1.7291321e-7`，最大绝对误差 `5.0343813e-7`；Verilog RTL cosim 5/5 通过。

本轮没有修改或加载板卡，Round30 开机 PL 版本保持不变。本结果不是完整合成、整机布局布线或实时提升通过；PS 暂时继续产生原 WORLD `RandnState` 随机序列并提供滤波器，从而保持种子和消费顺序可回放。下一层才把滤波器生成、overlap-add 与 40 ms batch 状态继续融合。

## 接口边界

`world_synthesis_pulse()` 每次处理一个 1024 点脉冲，输入：

- 周期与非周期最小相位复滤波器各 513 bins；
- PS 按原 WORLD `RandnState` 顺序生成的最多 1024 个原始噪声样本及 `noise_size`；
- 既有 512 点 DC remover。

输出是已经完成 WORLD 最终 `/fft_size` 等效缩放的 1024 点 impulse response。当前保留 PS 脉冲定位与随机数状态，是为了先隔离和签核计算密集 FFT 边界，不用不同 LFSR 替换原随机序列。

## 数值检查

- MinGW host：5/5 通过；worst relative-L2 `1.72913214679e-7`，worst absolute `5.03438134014e-7`。
- Vitis HLS C-sim：5/5 通过；worst relative-L2 `1.72913210714e-7`，worst absolute `5.03438131873e-7`。
- Verilog/XSim RTL cosim：5/5 通过；post-check 数值同 C-sim。
- RTL latency：min/avg/max `50,445 / 51,603 / 55,214` cycles，即 100 MHz 下约 `0.504 / 0.516 / 0.552 ms`；total 258,123 cycles。

## HLS 资源估算

为了给后续 D4C、CheapTrick 和合成状态留资源，三次变换强制复用同一个 `Transform` 数据通路。相对初版独立正/逆 FFT：

| 版本 | LUT | FF | BRAM18K | DSP | 估算最大延迟 |
|---|---:|---:|---:|---:|---:|
| 初版独立正/逆 FFT | 14,461 | 11,871 | 20 | 40 | 0.431 ms |
| 共享 Transform | 10,920 | 9,495 | 18 | 22 | 0.567 ms |

共享版节省 3,541 LUT、2,376 FF、2 BRAM18K 和 18 DSP；延迟仍远低于 10 ms 帧周期。以 Round18 已路由整机加上本 HLS 估算做非签核上界，约为 24,830 LUT、29,640 FF、37 BRAM18K、69 DSP；真正结果必须重新整机综合/布局布线，不能把估算直接写成可用资源。

## 警告与限制

- XSim 动态依赖监视器针对显式 `DEPENDENCE inter false` 打印 2,100 条 Critical WARNING；5 组 RTL 数值通过说明本组向量未出现错误，但不是形式证明。与 minphase 核一样，整机签核前必须保留并处理此风险。
- HLS 报告的 10,920 LUT / 9,495 FF / 18 BRAM18K / 22 DSP 是综合估算，不是 OOC routed 或完整音频工程结果。
- 当前一次 AXI 事务仍是一脉冲，不是最终 40 ms batch；下一轮要把多脉冲描述符、滤波器生成和跨块 overlap-add 状态合并，减少 PS/PL 边界。
- 本轮没有真实 WORLD 文件 PCM16/SNR 回归、板卡加载、音频、试听或稳定性测试，因此不宣称部署可用或整机提速。

## 复现

```powershell
& ./build/test_world_synthesis_pulse.ps1
$env:WORLD_SYNTH_HLS_PROJECT='D:/wpl_20261030_r31/pulse_shared'
& 'D:/USER_Software/vivado/2026.1/Vitis/bin/vitis-run.bat' `
  --mode hls --tcl --input_file ./build/probe_world_synthesis_pulse_hls.tcl
& 'D:/USER_Software/vivado/2026.1/Vitis/bin/vitis-run.bat' `
  --mode hls --tcl --input_file ./build/cosim_world_synthesis_pulse_hls.tcl
```

关键 SHA-256：源码 `43a21ed4...baaaa8`，testbench `d826f0f4...b28bd`，csynth report `23fc818d...cff4c`，cosim report `e830a11f...fd794`，XSim log `9c8ff57c...1754d`。
