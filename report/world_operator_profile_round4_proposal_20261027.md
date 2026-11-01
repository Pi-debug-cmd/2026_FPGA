# PL-20261027-01：Round 4 ARM算子剖析方案

基准 `ed3624a`（任务分支按入口规则同步最新main后，历史结果SHA不改写）。增加诊断构建开关 `-ProfileOperators`：只用链接器`--wrap`计时WORLD的Dio/StoneMask/CheapTrick/D4C、FFT建表和执行；计数器线程局部，按分析阶段、FFT长度、r2c/c2r/c2c及plan/execute分别记录。生产程序默认不启用，无算法、批次或音色参数变化。

复现：`./build/build_world_exp.ps1 -WorldRoot <pyworld-0.3.5/lib/World> -Target arm -ProfileOperators`。沿用前轮受控标准录音1前5秒16k PCM16；板端将比较原v23与计时版输出SHA，再读取计时。计时开销通过同输入墙钟与runtime汇总对照说明，不能当作未插桩程序的绝对速度。

本轮只静默文件测试，原厂PL保持不动，不录音、不播放测试音。传输前原v23服务暂时停止，完成后恢复。下一PL模块依据ARM真实算子占比选择，不能继续套用电脑端exp占比。
