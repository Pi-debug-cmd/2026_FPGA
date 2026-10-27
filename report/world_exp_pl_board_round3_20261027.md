# PL-20261027-01：Round 3 板端回归与管线延迟诊断

基准实现提交 `7269c2a`，同步main后 `7a0f16b`；程序SHA256 `493ff17bc51a70706968006ccf8d4f5961b427aed86ca67384e8102d068c25f9`。位流及同一受控5秒输入不变，仅静默文件测试。

PL与整数模型80000样本逐字节一致；新CPU与原v23逐字节一致；PL相对原v23 SNR79.0566dB，最大PCM16误差3，1227次零fallback，零削顶。PL接口总0.235515s，准备0.099111/DMA0.120715/解包0.015689s，比Round2再少约5.8%。渲染RTF0.306332，总文件墙钟2.799151s、分析RTF0.552814。

新增定速文件诊断：每128个16k采样以8ms间隔输入，按输出样本位置对应输入块的实际交付时刻计算PS管线交付滞后，保留625个原始值；聚合去掉首尾各0.5秒。无ALSA、无录音、无播放，**不是物理端到端延迟**。

| 路径 | PS管线p50 | PS管线p95 | PS管线最大 | feeder最大迟到 |
| --- | --- | --- | --- | --- |
| 原v23 | 99.129ms | 115.867ms | 117.410ms | 2.701ms |
| PL | 98.437ms | 115.484ms | 117.190ms | 0.294ms |

结论：当前确实有PL参与核心合成且数值回归通过，但卸载exp对总体延迟改善很小。即使排除ALSA/codec，PS管线p95仍超过100ms；不能宣布“高实时性完成”。主要下一方向是ARM分析阶段D4C/CheapTrick/DIO与40ms参数批次/前瞻依赖；继续增加exp核吞吐不能自动解决此关键路径。

复现：`python3 world_exp_file_trial.py --base /tmp/codex_world_exp_20261027`；新增 `python3 world_exp_latency_probe.py --base /tmp/codex_world_exp_20261027 --backend v23`，再以`--backend pl`对照。原始结果分别为 `world_exp_pl_board_round3_20261027.json`、`world_exp_paced_latency_{v23,pl}_20261027.json`。

现场20秒低缓冲试验已通过只读preflight，等待本轮操作者准备确认；尚无本轮听感。当前为临时候选位流+内核模块，音频服务停止；原厂恢复镜像已准备。启动分区和原v23二进制未改。
