# WORLD v23 浮点FFT位准确模型 Round 6

实现提交53645ef；2026-10-27；任务PL-20261027-01。Vivado MCP创建xfft9.1 rev16，2048最大/运行时1024与2048、floating_point、25bit旋转因子、pipelined streaming、natural order。实际模型参数全部记录在JSON，并与生成XCI交叉核对。

30个独立FFT用例（1024→2048→1024切换，正反向，零/脉冲/常数/随机复数/1e-12弱信号）通过，相对L2误差最大6.60848722e-08，门限1e-5；对照numpy double DFT，只用于方向、尺度和精度检查。完整WORLD仍以原v23 double为对照。

| 输入 | D4C SNR dB | 分析 SNR dB | 合成 SNR dB | 全部 SNR dB | 全部最大PCM16误差 |
| --- | ---: | ---: | ---: | ---: | ---: |
| male1 | 118.306 | 90.467 | 92.263 | 88.876 | 1 |
| male4 | 113.844 | 89.661 | 90.966 | 87.845 | 1 |

两段各80000样本，所有非CPU路径最大PCM16误差1；门限SNR≥80dB且最大误差≤4通过。cpu/off与前轮原v23输出hash一致。日志保留每个分阶段模型调用数，其他FFT尺寸仍用CPU。模型耗时不代表RTL速度；官方浮点接口内部定点行为不能以普通float FFT替代。

结论：接受该FFT候选的模型数值门，允许进入RTL接口与PS/PL集成；未通过PL板测、听感、真实端到端延迟或稳定性。本轮未切PL，板上原v23继续运行。OOC综合在独立工程进行中，资源/时序尚未签核。

复现：按方案用Vivado生成SDK，解压nt64 zip到忽略目录；`build/build_world_exp.ps1 -Target host -FftModelSdk <SDK> -WorldRoot <WORLD>`；运行`build/check_world_fft_ip_quality.py --sdk <SDK> --exe <host_fftmodel.exe> --xci <XCI> --input <male1/input.raw> --input <male4/input.raw> --out <generated-dir>`。输入为前轮相同受控WAV前5秒、均值声道、scipy resample_poly、16k PCM16，SHA见JSON；生成语音不提交。
