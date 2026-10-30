# PL-20261027-01：PL 板端首轮——数值通过，性能拒绝

2026-10-27，基准 `8563cee`，程序源 `50974e2`，位流及恢复SHA见整机实现报告。COM4，Cortex-A9 / Linux5.15。只做文件测试，未录音/播放；当前候选位流临时驻留，v23服务停止。

硬件向量：96帧、49248 bins、全64bit输出零差异；单次513-bin ioctl（含双向拷贝与DMA）均值90.799µs、p95 91.248µs、最大95.868µs。完整语音：受控男声录音1前5秒，80000样本；新CPU与原v23逐字节一致、PL与整数模型逐字节一致，PL相对CPU SNR79.0566dB、最大PCM16误差3、1227次零fallback。

**性能未通过**：渲染RTF原v23 0.326989，新CPU0.326107，PL0.339278；总文件墙钟2.790654/2.784866/2.810207秒，未提速。PL后端含量化/角度处理/打包/解包共0.396830s，约323µs/调用，明显高于单独DMA约91µs，接口软件开销需先优化。历史电脑profile占比不能直接预测本机ARM整链收益；分析RTF0.55本来就是双核管线关键路径，不能把核吞吐当整链速度。

复现：候选临时加载后，`insmod world_exp_dma.ko`；`./world_exp_dma_probe exp_input.bin exp_expected.bin`；`python3 world_exp_file_trial.py --base /tmp/codex_world_exp_20261027`。完整结果见同轮两项JSON。下一轮先移除打包中的逐bin通用remainder/floor开销，并分项计时CPU exp和PL接口，继续保留相同输入及数值回归；此轮不安排现场试听。
