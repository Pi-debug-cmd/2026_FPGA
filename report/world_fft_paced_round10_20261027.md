# Round 10 静默定速管线滞后

任务 PL-20261027-01，2026-10-27，基准 1b8e909，入口 4513f66。板上 compact FFT/exp 位流与 Round10文件回归相同。未访问ALSA、没有采录放。

5秒受控male1输入，16k PCM16，128样本/8ms定速，625块。逐块输入交付和输出到达时刻及二进制/输入SHA保存在三份 world_fft_paced_*_round10_20261027.json。

| 模式 | p50 ms | p95 ms |
| --- | ---: | ---: |
| 原v23 | 100.534687 | 117.058676 |
| FFT计划复用+PL exp | 96.583057 | 113.992885 |
| compact2048+PL exp | 96.959689 | 114.187369 |

复现使用 board/world_exp_latency_probe.py --help 选择相同base、binary、fft-mode、label，WORLD_EXP=pl。JSON记载实际设置和原始625块滞后；统计去除启动段，算法见脚本。

结论：compact FFT在此单轮未减少滞后，100ms目标仍未通过。以上排除ALSA、codec、模拟和声学传播，不能解释为物理端到端延迟或稳定性通过。服务停止、候选暂时驻留，需在静默诊断结束恢复正常启动基线。
