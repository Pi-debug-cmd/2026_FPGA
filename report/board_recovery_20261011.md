# 2026-10-11 重启恢复核对

用户已重启开发板。通过 COM14/115200 登录，uptime 约2分钟，内核仍为5.15.0-xilinx，FPGA manager operating。

声卡0、Formatter/I2S录放、PL GPIO、gpio-keys、显示和摄像头采集驱动均已绑定。临时 overlay 为空，`/dev/pitch_dma`不存在，PCM录放均closed。原厂音乐监听PID549为S运行状态；昨晚PID551不再可用，不可沿用。

5秒原厂WAV播放返回0、underruns=0。第一次用户音响未供电，不计听感通过；重复播放同样返回0且零underrun，用户确认“听到了”。脚本保存并恢复mixer。原厂音频输出恢复已验证，摄像头/显示仅验证驱动绑定，不代表实物功能测试。

证据：`board_reboot_recovery_20261011.log`、`board_factory_audio_recovery_20261011.log`、`board_factory_audio_recovery_repeat1_20261011.log`。

昨晚候选PL听感及黄金向量结论保持：参见 `pl_dma_board_test_20261010.md`。恢复结论分开记录：冷启动恢复通过；摄像头热重绑定会卡住，完整热回退未通过。已修改 `board/restore_factory_pl.sh`，在修改硬件前检查原试验监听PID，跳过摄像头热绑定，明确要求冷启动完成全外设恢复。该脚本仍绑定10/10试验目录和PID，只是历史恢复入口，不能用于当前重启后的新切换。

下一步：整理每次试验的状态保存及切换流程，使用本次实际监听PID；继续配置比例/独立DSP复位，使注册参数能进入PL，再进行10分钟稳定性与参数边界验证。既有位流固定Q16=86856，没有独立DSP复位或运行中改比例功能。
