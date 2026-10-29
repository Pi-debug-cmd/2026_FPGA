# PL-20261027-01 Round24：60 秒提示音稳定性无效录入

## 结论

**REJECTED（无有效语音，不能用于稳定性验收）。** 60 秒流式链完整运行，录放子进程均正常，融合 minphase PL 完成 7,883 次调用且 fallback 为 0；但 WORLD 检出有声帧为 0，未满足 `--require-voiced`，监督器退出 1。操作者随后明确反馈：**“60s录入我没有准备好”**。

因此本轮只能证明候选在无有效语音输入时连续运行 60 秒且没有 xrun、ALSA error、PL fallback 或削顶，不能证明 60 秒真人语音稳定性，也不能把失败归因于 PL 算法或音频链。Round23 的 20 秒实时可用结论不变。

## 条件与结果

- 基准提交 `e0b518e`；candidate、ARM 程序、module、提示音、200 ms prefill、`fifo_io`、增益和 ALSA 参数均与 Round23 相同，唯一计划变量为 20 秒延长到 60 秒。
- 提示音 exit 0、24,960 帧、12% 峰值，提示后 2.0 秒启动录入。
- arecord/runtime/aplay 子进程 `0/0/0`；capture overrun 0、playback underrun 0、ALSA error 0。
- 采集/播放各 960,000 个 16 kHz 样本，提交/消费参数帧 `1502/1502`。
- PL `7883 calls / 0 fallback`；用户态 device ioctl 累计 `3.252549 s`，驱动 device 累计 `3.055748 s`，驱动平均约 `387.64 us/call`。
- raw capture peak `0.423708`、capture RMS `0.027869`，输入近满幅样本 0；output peak `0.148522`、输出削顶样本 0。
- 分析 RTF `0.283794`、渲染含输出等待 RTF `0.278869`、最大分析批次 `16.826 ms`。
- 有声帧 0，监督器明确报错 `Speech trial contains no voiced frames`。

作为对照，Round23 同配置的 raw peak `0.415668`、RMS `0.059064`、有声帧 1079。两轮峰值相近但本轮 RMS 约减半且无任何基频帧；结合操作者原话，本轮没有足够证据继续定位为 VAD、麦克风或 PL 故障。

## 运行态与恢复

候选运行态 active codec 快照中 MICB、左右 ADC/DAC、LOUT1/ROUT1 PGA、HP_L/HP_R 均为 On。驱动统计为 `calls=7883, copy_in_ns=15978294, device_ns=3055747554, copy_out_ns=134268642`。

证据下载后卸载 module、`sync` 并正常 reboot。最终：

- 原 v23 SHA `f12da25e...49b7`、原厂 bit SHA `16cb36f7...2a61` 匹配；
- FPGA `operating`，`world-voice` running，采集和播放 PCM 均 `RUNNING`；
- kernel taint 0，无候选 module，临时目录不存在；
- 启动仍出现既有 FAT 未正确卸载警告；本轮未写启动分区，离线 fsck 建议不变。

## 下一步

下一轮仍使用同一 candidate 与参数重做 60 秒门，但必须等待操作者新的明确准备确认。提示后需要在整个正式录入期间持续讲话；失败轮不自动重跑。若有效讲话后仍为 0 voiced，才进入采集/VAD 定位。
