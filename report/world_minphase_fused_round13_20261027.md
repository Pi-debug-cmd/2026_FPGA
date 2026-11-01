# Round13 融合最小相位数值通过，首版HLS周期拒绝

任务PL-20261027-01，2026-10-27，实现2c2e2d0。24个独立log谱，相对原WORLD复数滤波器最大relativeL2 9.2324e-7；两输入各5秒完整语音最大PCM16误差1，SNR96.237/96.601dB，host候选未使用PL exp。原始SHA/输入/输出/遥测在world_minphase_fused_host_round13_20261027.json。

HLS2026.1成功生成RTL，目标100MHz，估算18150LUT/11213FF/6 BRAM18K（3 BRAM36K）/81DSP；时钟估计7.300ns是HLS估计，不是routed签核。首版动态索引FFT环路整体延迟未知，蝶形子循环上界18434拍，exp输出循环约25137–25650拍，不能认定实时收益。因此拒绝将首版直接上板，保留其数值和架构原型。

原始HLS顶层/FFT报告已附TXT。下一轮固定FFT循环、预计算旋转因子ROM并流水复数指数，先明确周期/资源上界，再做HLS RTL数值cosim和Vivado MCP整机签核。未更改板卡或用户听感，compact位流驻留、服务暂时停止。
