# PL-20261027-01 Round20：融合最小相位核静默板端验证

## 结论

Round18/19 的融合最小相位核已在 Zynq-7020 实板完成加载、coherent DMA、24 例向量和两段受控男声文件回归。24/24 探针通过，最坏 relative-L2 `8.53141669193e-7`；真实 v23 文件输出相对原 v23 的 SNR 为 `97.371/96.942 dB`，最大 PCM16 误差均为 1，零 fallback、零超时。该 PL 后端已达到“可供文件转换使用”的板端数值门。

本轮没有录音、播放或试听，不能据此宣称真人实时稳定性、物理延迟或音色主观门通过。融合核只迁移固定 1024 点最小相位阶段，不是整个 WORLD 分析/合成链全 PL。

## 板端向量与开销

- `/dev/world_minphase` 成功创建，24 个与 Round16 同源用例全部通过。
- 24 次统计：copy-in `46,644 ns`、device `9,197,184 ns`、copy-out `383,652 ns`；device 平均约 `383.2 us/call`。
- 两段文件的 minphase-only 与 combined 合计增加 5,052 次调用。驱动增量：copy-in `11.355 ms`、device `1.953 s`、copy-out `92.410 ms`；device 平均约 `386.5 us/call`。
- 未出现模块超时锁存或 ioctl 错误。加载自有模块时内核按预期临时 taint `4096`（out-of-tree），重启后恢复为 0。

## 两段 5 秒静默文件

| 输入 | 模式 | 墙钟秒 | SNR dB | 最大 PCM16 误差 |
|---|---:|---:|---:|---:|
| male1 | 原 v23 | 2.899892 | exact | 0 |
| male1 | 新程序 CPU | 2.845253 | exact | 0 |
| male1 | fused minphase PL | 2.748740 | 97.371389 | 1 |
| male1 | 旧 exp PL | 2.770467 | 79.056613 | 3 |
| male1 | minphase+exp 请求 | 2.755961 | 97.371389 | 1 |
| male4 | 原 v23 | 2.816433 | exact | 0 |
| male4 | 新程序 CPU | 2.822582 | exact | 0 |
| male4 | fused minphase PL | 2.747420 | 96.942108 | 1 |
| male4 | 旧 exp PL | 2.802386 | 78.573573 | 2 |
| male4 | minphase+exp 请求 | 2.801134 | 96.942108 | 1 |

新程序 CPU 路径与原 v23 两段均逐字节一致。minphase+exp 请求的输出 SHA 与 minphase-only 完全一致，独立 exp 后端遥测为 `calls=0/fallback=0`：融合核已经包含该最小相位阶段的 exp/cos/sin，启用融合核后旧逐算子 exp IP 不再参与，不应重复计为额外 PL 迁移。

以新程序 CPU 单次样本为对照，minphase PL 墙钟下降约 3.39%/2.66%；样本数不足以写成稳定性能收益。分析 RTF 分别约从 `0.56/0.55` 到 `0.54/0.54`，最大分析批次约 `32.83/33.27 ms`，仍须用真实 I/O 和长时压力验证。

## 过程异常与修正

1. 首次 load 命令末尾误用 shell `exit`，候选已成功 `operating`、音频驱动已绑定，但串口包装器等不到结束标记而超时；重新登录后状态正常，未重载候选。
2. 文件脚本首次在任何用例前因旧 `world_exp_dma` 没有可选 sysfs stats 文件停止；改用其既有用户态 calls/fallback 遥测。
3. 第二次脚本错误要求 minphase+exp 中独立 exp 调用必须大于 0；实测证明融合核绕过旧 exp 入口。最终门改为 exp-only 必须调用、融合模式必须零调用且与 minphase-only 逐字节一致，v3 全部通过。
4. 生成输入时 host EXE 因本机 Windows DLL 重定位错误未启动，但 `check_world_exp_quality.py` 在启动前已经按既有固定流程生成输入；两段输入 SHA 与历史 Round1/10 完全一致，因此不以该 host 失败生成新的基准结论。

## 恢复

测试后两个自有模块均成功卸载，执行 `sync` 和正常 `reboot`，由未修改的启动分区重新加载原厂系统。最终核对：

- 原 v23 SHA `f12da25e...49b7`，原厂 bit SHA `16cb36f7...2a61`；
- FPGA `operating`，`world-voice` running；采集/播放 PCM 均 RUNNING；
- 自有 DMA 模块未加载，内核 taint `0`，候选 `/tmp` 目录已清除。

重启日志仍出现既有 `FAT-fs (mmcblk0p1): Volume was not properly unmounted` 警告；本轮没有写启动分区，启动文件 SHA 正常，但应在维护窗口离线 fsck，不能忽略为“零恢复警告”。

完整板端遥测保存在 `world_minphase_file_result_round20_20261029.json`。原始串口日志受 `.gitignore` 管理，其逐件 SHA 记录在同名汇总 JSON。

## 下一步

在操作者再次明确准备后，以 minphase PL 为唯一新增变量运行有限时真实 v23 录放，先验证零 xrun/零 fallback/电平，再与 CPU v23 对比墙钟、分析峰值和听感；通过后才做长时稳定性。独立 exp IP 已被融合核覆盖，不应作为默认组合继续占用软件调用路径。
