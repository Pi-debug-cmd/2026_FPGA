# Round 11 ARM适配同位流对照

任务 PL-20261027-01，2026-10-27，代码979fb89。同一compact位流、驱动、两段受控输入，各CPU/exp_only/combined三模式，旧新程序交错三遍，共36次，原始计时及SHA见同名JSON。无ALSA或现场录放。

36次全部退出0、80000个PCM16输出样本与Round10同模式逐字节一致；PL exp零fallback。只接受数值保持，不更改既有用户听感。

| 输入 | 模式 | 旧中位墙钟s | 新中位墙钟s |
| --- | --- | ---: | ---: |
| male1 | cpu | 2.603558 | 2.674638 |
| male1 | exp_only | 2.603753 | 2.602989 |
| male1 | combined | 2.645587 | 2.621563 |
| male4 | cpu | 2.618957 | 2.608949 |
| male4 | exp_only | 2.606971 | 2.605818 |
| male4 | combined | 2.658425 | 2.608862 |

combined中位数下降约0.91%/1.87%，但新combined仍未可靠快于同程序exp_only（male1慢约0.71%，male4约0.12%）。prepare约0.113→0.105s，unpack约0.088→0.085s；DMA仍约0.436s/3279次。小改动保持数值但未解决实际瓶颈，FFT仍不设默认。cpu单项波动较大，保留全部原始计时，不声称算法发生回归。

复现：方案报告入口 world_fft_adapter_trial.py，传入同位流目录、旧新程序和新output路径。板端程序SHA在JSON中。

下一步分解内核copy_in/DMA/copy_out开销，以证据决定接口/核时钟优化；不能把本轮吞吐改进写成100ms物理延迟或长期稳定性通过。当前compact候选驻留、v23音频服务停止。
