# PL-20261027-01 Round23：提示音后融合最小相位 PL 实时复测

## 结论

**ACCEPTED（20 秒实时可用门）。** 操作者在双提示音与 2 秒准备窗口后完成持续讲话，并反馈：**“讲话时能听到转换声音，效果和ps类似”**。本轮 1079 个有声帧，录放零 xrun、ALSA error 0、输入触顶 0、输出削顶 0；融合 minphase PL 运行 4857 次、fallback 0。

这证明当前 candidate 能在板上以既有 v23 音色链完成有限时实时采录放，效果主观上与 PS 路径类似。它不等于完整 WORLD 全 PL，也不替代 60 秒、10 分钟、30 分钟稳定性和定量物理延迟门。

## 条件

- candidate SHA `1bc4b3f8...29373`；ARM 程序 SHA `2dea4725...f438`；module SHA `fbbe531f...1f62`。
- `WORLD_MINPHASE=pl`、`WORLD_EXP=cpu`；200 ms 前缀，`fifo_io`。
- 32 kHz/S24_LE 双声道；period 512，capture/playback buffer 4096/3072，start delay 32 ms。
- 输入 Q16 262144（4x），输出 Q16 49152（0.75）。
- 录入前 880/1175 Hz 双提示音，提示 exit 0、24,960 帧、12%峰值；提示后 2 秒才启动采录放。

大程序预部署首次被原厂后台的串口日志打断；上传器未替换目标，从已核验 offset `1,101,824` 续传，最终 SHA 完整通过。该传输异常发生在切换和实时测试前，不影响测试程序身份。

## 客观结果

| 项目 | 结果 |
|---|---:|
| 提示音 exit / 帧数 / 后置准备 | 0 / 24960 / 2.0 s |
| arecord/runtime/aplay | 0 / 0 / 0 |
| capture overrun / playback underrun / ALSA error | 0 / 0 / 0 |
| PL calls / fallback | 4857 / 0 |
| 采集 / 播放 16 kHz 样本 | 320000 / 320000 |
| 参数提交 / 消费 | 502 / 502 |
| 有声帧 | 1079 |
| 原始采集 peak / 近满幅样本 | 0.415668 / 0 |
| 输出 peak / 削顶样本 | 0.404884 / 0 |
| 分析 RTF / 渲染含等待 RTF | 0.561150 / 0.310517 |
| 最大分析批次 | 34.605 ms |
| mixer restore / 测试后 PCM | 0 / closed+closed |

用户态 backend：prepare `21.913 ms`、device ioctl `2.011376 s`、unpack `57.200 ms`、mutex wait `10.384 ms`。驱动累计：copy-in `10.295 ms`、device `1.885301 s`、copy-out `85.489 ms`；内核 device 平均约 `388.16 us/call`。

候选运行态快照已在 reboot 前下载：MICB、左右 ADC、左右 DAC、LOUT1/ROUT1 PGA、HP_L/HP_R 均为 On。该证据补齐 Round21 未下载 active codec 状态的缺口。

## 主观结论边界

- 用户明确确认转换声音可听。
- 用户评价“效果和ps类似”，符合文件门 SNR 约 97 dB/最大误差 1 的预期；不声称 PL 音质优于 PS。
- 用户没有单独回答提示音听感问题；只能写提示音进程 exit 0 且测试时序生效，不能擅自写“用户确认提示音可闻”。
- Round21 的原始“没听到声音”仍保留；用户随后澄清当时录入开始时没有准备好，因此不再作为候选音频链失败的归因证据。

## 恢复

结果和 active codec 快照下载后，模块成功卸载，`sync` 后正常 reboot。最终原 v23/原厂 bit SHA 匹配，FPGA operating，服务 running，双 PCM RUNNING，自有模块无，taint 0，临时目录清除。既有 FAT 未正确卸载警告仍出现；本轮未写启动分区，维护窗口离线 fsck 建议不变。

## 下一步

当前达到有限时“可以用”状态。下一轮若继续，应保持同一 candidate 和提示流程，先做 60 秒有效讲话稳定性；通过后逐级扩展到 10 分钟和 30 分钟。每次现场录放仍需新的准备确认，失败轮次照常提交。
