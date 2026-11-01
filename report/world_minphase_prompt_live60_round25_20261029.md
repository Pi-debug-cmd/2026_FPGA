# PL-20261027-01 Round25：60 秒有效讲话稳定性复测失败

## 结论

**REJECTED（提示音不可闻，且客观音频门失败）。** 操作者在测试后明确反馈：**“我刚刚没有听到提示音”**。因此正式录入起点对操作者不可判定，不能把本轮当作有效的 60 秒讲话稳定性测试。

与此同时，运行时完整处理了 60 秒，但退出码为 6：有声帧为 0，输出出现 133 个削顶样本。监督器记录子进程 `0/6/0` 并退出 1。PL 本身完成 8,803 次调用、fallback 0，采集和播放都达到 960,000 个 16 kHz 样本，零 xrun；这些不能覆盖提示不可闻、有声帧为 0和输出削顶的失败门。

## 条件

- 基准提交 `d85bee6`；candidate SHA `1bc4b3f8...29373`，ARM SHA `2dea4725...f438`，module SHA `fbbe531f...1f62`。
- `WORLD_MINPHASE=pl`、`WORLD_EXP=cpu`，60 秒、prefill 200 ms、`fifo_io`。
- 32 kHz/S24_LE 双声道，period 512，capture/playback buffer 4096/3072，start delay 32 ms。
- 输入 Q16 262144（4x），输出 Q16 49152（0.75）。
- 既有提示流程报告 exit 0、24,960 帧、12% 峰值、后置准备 2 秒；操作者实际未听见，故不能写“提示音通过”。

## 客观结果

| 项目 | 结果 |
|---|---:|
| arecord/runtime/aplay | 0 / 6 / 0 |
| capture overrun / playback underrun | 0 / 0 |
| PL calls / fallback | 8803 / 0 |
| 采集 / 播放 16 kHz 样本 | 960000 / 960000 |
| 参数提交 / 消费 | 1502 / 1502 |
| 有声帧 | 0 |
| 原始采集 peak / RMS / 近满幅样本 | 0.620975 / 0.056869 / 0 |
| 输出 peak / 削顶样本 | 2.423787 / 133 |
| 分析 RTF / 渲染含等待 RTF | 0.271251 / 0.288714 |
| 最大分析批次 | 16.511 ms |
| mixer restore / 测试后 PCM | 0 / closed+closed |

PL 用户态 device ioctl 累计 `3.620930 s`；驱动累计 `calls=8803, copy_in_ns=18586356, device_ns=3400138775, copy_out_ns=148677439`，内核 device 平均约 `386.25 us/call`。candidate active codec 快照中 MICB、左右 ADC/DAC、LOUT1/ROUT1 PGA、HP_L/HP_R 均为 On。

本轮没有保存真人原始音频，不能离线判定采集内容；也不能从幅度非零推断操作者持续讲话。退出码 6 与 `clipped_samples=133` 一致，但即使忽略削顶，有声帧 0 仍不满足门槛。

## 恢复

证据下载后卸载 module、`sync` 并正常 reboot。最终原 v23/原厂 bit SHA 匹配，FPGA `operating`，服务 running；首次复核紧邻启动时双 PCM 尚 closed，随后复核均为 `RUNNING`。kernel taint 0，无候选 module，临时目录不存在。既有 FAT 未正确卸载警告仍出现；本轮未写启动分区。

## 下一步

先修提示流程，不直接重跑 60 秒：

1. 在提示音前增加静音预热，让 codec/DAPM 完成启动；
2. 改为更长、更响、频率递增的三段提示；
3. 增加 `--prompt-only`，只播放提示并恢复 mixer，不启动录音；
4. 操作者明确确认听见后，才再次申请 60 秒录入准备确认。

输出削顶也需在下一次有效讲话测试前处理；优先把输出增益从 0.75 降到更安全值或加入有界限幅，不能用削顶运行验收音质。
