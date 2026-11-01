# PL-20261027-01 Round21：融合最小相位 PL 首轮实时测试

## 结论

**REJECTED。** 20 秒监督日志的数字链门全部通过，但操作者原话为：**“没听到声音”**。用户听感是硬门，不能用零 xrun、非零 output peak 或 PL 调用成功覆盖，因此本轮不接受为实时可用。

板卡已在结果下载后卸载临时模块、`sync` 并正常重启；原厂 bit/v23 SHA、FPGA、服务、双 PCM、taint 和临时目录恢复核对通过。本轮没有自动重复录放。

## 条件

- 操作者在本轮重新明确“准备好了”。
- 20 秒，200 ms 前缀，`fifo_io`；period 512，capture/playback buffer 4096/3072，start delay 32 ms。
- 既有增益：输入 Q16 `262144`（4x），输出 Q16 `49152`（0.75）。
- `WORLD_MINPHASE=pl`、`WORLD_EXP=cpu`；这是相对既有 v23 实时配置的唯一算法后端变量。
- candidate SHA `1bc4b3f8...29373`，ARM 程序 SHA `2dea4725...f438`，module SHA `fbbe531f...1f62`。

## 客观日志

| 项目 | 结果 |
|---|---:|
| arecord/runtime/aplay 退出码 | 0 / 0 / 0 |
| capture overrun / playback underrun / ALSA error | 0 / 0 / 0 |
| PL calls / fallback | 2725 / 0 |
| 采集 / 播放 16 kHz 样本 | 320000 / 320000 |
| 参数提交 / 消费 | 502 / 502 |
| 有声帧 | 30 |
| 原始采集 peak / 近满幅样本 | 0.424322 / 0 |
| 输出 peak / 削顶样本 | 0.197959 / 0 |
| 分析 RTF / 渲染含等待 RTF | 0.272714 / 0.277273 |
| 最大分析批次 | 24.116 ms |
| mixer restore / 测试后 PCM | 0 / closed+closed |

用户态 minphase 计时为 prepare `12.578 ms`、device ioctl `1.204112 s`、unpack `29.887 ms`、mutex wait `6.195 ms`。驱动累计为 copy-in `5.863 ms`、device `1.133735 s`、copy-out `47.025 ms`；2725 次调用的内核 device 平均约 `416.05 us/call`。

这些数据证明采集、WORLD 线程、PL ioctl 和 aplay 进程都前进，且程序写出了非零数字样本；它们**不能证明模拟输出实际可听**。只有 30 个有声帧也说明有效讲话负载较低，但仍不解释为用户一定听错。

## 监督与部署修正

`board/live_world_trial.py` 新增 `WORLD_MINPHASE` 请求记录、`world_minphase_pl` calls/fallback 强校验和失败路径遥测保存。既有 mixer、ALSA、调度、增益和清理逻辑未改变。

预部署大文件首次串口传输在 2.59/2.69 MB 附近受控制台日志干扰超时；上传器没有替换目标文件，随后以 `.b64` 前缀 SHA 核对从 offset 2,592,768 续传，最终完整二进制 SHA 正确。该传输异常与后续运行程序校验分开记录。

## 恢复和只读对照

正常重启后：原 v23 SHA `f12da25e...49b7`、原厂 bit SHA `16cb36f7...2a61`，FPGA operating，服务与双 PCM RUNNING，自有 module 无，taint 0，临时目录清除。

恢复后的原厂只读 codec 状态显示 Headphone `105/105`、Playback `230/230`，左右 PCM output mixer On，左右 DAC、LOUT1/ROUT1 PGA、HP_L/HP_R 均 On。这只是恢复后的工厂状态，候选运行态快照已随 `/tmp` 在重启时清除，不能倒推候选当时 DAPM 一定相同。

启动仍出现既有 FAT 未正确卸载警告；本轮未写启动分区，哈希正常，维护窗口 fsck 建议不变。

## 下一诊断门

不得直接重复同一 20 秒测试。下一次操作者确认后按顺序隔离：

1. 原厂环境播放已知参考音，确认当前扬声器/耳机物理输出可听；
2. 临时 candidate 下播放同一参考音，区分 PL 热切后的音频/codec 路径与 WORLD 算法；
3. 参考音可听后再跑短时 WORLD，并在恢复前下载 candidate 的 active codec/DAPM 快照和输出证据；
4. 任一参考播放不可听即停止，不把问题归因到 minphase 数值核。

任何新播放或讲话测试必须取得新的当轮准备确认。
