# 2026-10-10 PL DMA 首次实板测试

> 最终进度：用户确认20秒复测持续可听、延迟感受不到、无断续杂音颤动；额外60秒返回0、采集overrun=0、播放underrun=0。主观延迟结论不代表零延迟测量。随后原厂位流成功加载，DMA模块/overlay移除；声卡及显示驱动恢复，但恢复摄像头采集 `amba_pl:vcap_dvp` 时串口命令超时，Ctrl-C无响应。gpio-keys、mixer恢复和SIGCONT551后续步骤尚未完成。用户要求今天停止，尚未确认断电重启；已停止操作，下次先重启核对。启动分区未修改，完整回退未验收。下文此前“听感待回答/候选保留”状态以本段为准。

新增证据：`board_dma_live_60s_20261010.log`、`board_factory_rollback_20261010.log`、`board_factory_restore_dependencies_20261010.log`、`board_factory_rollback_completed_20261010.log`。回退脚本 `board/restore_factory_pl.sh` 已修正显示聚合生成顺序（先xlnx-pl-disp后xlnx-drm），尚未处理摄像头恢复卡住，不能直接重跑。

用户授权在板旁配合整片 PL 重配置。COM14 始终可用，未修改启动分区、原厂位流或资料盘。

## 结果

用户表示首轮未准备好，已再次运行20秒实时测试，独立目录 `/tmp/codex_pitch_dma_live_20261010_repeat1`。脚本返回0，capture_overruns=0、playback_underruns=0，处理无报错；听感待回答。日志 `board_dma_live_20s_repeat1_run_20261010.log`。准备重复脚本时曾因 shell 展开 `$@` 导致 sed 失败，该次没有启动录放；修正后完成本轮。

- 候选 `audio_pitch_dma_swap.bin` 成功加载，FPGA manager 为 `operating`。
- 临时设备树创建 DMA 0x40400000，GIC 88/89；驱动创建设备 `/dev/pitch_dma`。
- PCM32 8195 样本、S24_LE 8195 帧按 257 帧分块顺序通过同一 PL 核，返回均为 0；输出长度和 SHA256 与参考模型完全相同，验证跨 TLAST 保持状态。
- PCM32 输出：32780 字节，`5e8cceeb72fdf032683199610e649f75b40aa4859ed8f862bdc6667a3bfef8b8`。
- S24_LE 输出：65560 字节，`43fc0f6b3402b15f80ffa8a2375da8d08601ce65c21a8d1049327ead33971c9b`。
- 清除 2048 个零样本的测试历史后运行 `board/live_pitch_dma_trial.sh`：32kHz、S24_LE 双声道，DMA 分块 256，固定 Q16=86856；20 秒采集 overrun=0、播放 underrun=0，处理日志为空，脚本成功结束。
- 实际录放 period512 / buffer3072，结束时两个 PCM 均 closed，中断各累计2572次。**用户听感尚待回答**，无端到端延迟测量，未完成长期稳定性或目标音色验收。

## 切换细节与已发现问题

先暂停已核对 PID551 的原厂音乐监听程序，保存 mixer，按上层消费者→底层设备顺序解绑旧 PL 驱动。GPIO reset 使用者全部释放后才解绑 PL GPIO；串口为 PS UART。

第一次加载未触及硬件：固件目录参数使用 echo 带入换行，内核找不到文件。改用 `printf "%s"` 后加载成功。当前 firmware_class.path 临时设为 `/lib/firmware`（原值空字符串，零字节写入不会恢复该参数）；不再指向项目临时目录。

恢复 Formatter 时触发自动重探测，手动 bind 返回 busy，原 shell 的 exit 导致登出。重新登录确认音频五个驱动全部绑定且声卡已注册，才继续。以后恢复应先检查自动绑定状态，不对已绑定设备重复 bind，错误不要退出交互登录 shell。

设备树移除会有内核提示 `/__symbols__/pitch_dma` 属性内存泄漏；目前只应用一次。alsactl 有原系统缺少 UCM 配置的警告，脚本未报告 mixer 恢复失败。

## 当前板况与继续入口

**候选 PL 仍运行，临时 DMA overlay 和模块仍存在；录放已停止。** 原厂视频、PL GPIO、PL UART、PL IIC 等消费者保持解绑；PID551 为 T(stopped)，不可直接恢复它或绑定候选中不存在的外设。等待本轮听感后决定复测或原厂回退。

本轮目录 `/tmp/codex_pitch_dma_live_20261010` 已存在，脚本拒绝覆盖；重复试听须创建新的项目测试目录。黄金向量不能直接再次从头比对：内核相位已推进，必须重新加载 PL 或计算正确的连续状态参考。

原厂回退文件 `/tmp/codex_pl_trial_20261010/factory_restore_swap.bin` 已准备但**实际回退未验证**。回退需先停止本项目音频、移除临时 overlay/模块、解绑候选音频，然后加载原厂镜像，再按 GPIO/时钟→底层外设→上层消费者顺序恢复原绑定，最后恢复 mixer 和 SIGCONT551。叶子原绑定记录在同目录 `leaf_bindings.txt`。断电重启应从原启动镜像启动；尚未在本轮验证。

主要证据：`board_pl_candidate_load_retry_20261010.log`、`board_pl_rebind_state_20261010.log`、`board_pl_dma_overlay_20261010.log`、`board_dma_golden_20261010.log`、`board_dma_live_20s_20261010.log`、`board_dma_live_final_state_20261010.log`。
