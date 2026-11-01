# PL FFT位准确模型与资源探测 Round 6

任务PL-20261027-01，基准9b609d4。板端FFT执行是主热点之一，旧18bit串行FFT慢于ARM且不满足log谱精度。此轮由Vivado MCP配置独立xfft 9.1：2048最大长度、运行时1024/2048、单精度浮点输入输出、25bit旋转因子、pipelined streaming、自然序、100MHz。先用官方位准确C模型替代完整WORLD调用，分别观察D4C、分析、合成和全部；不以numpy float FFT冒充RTL精度，不在板上加载。

源码`src/ps/world_fft_ip_model.cpp`只在显式host构建`-FftModelSdk <本机Vivado生成的SDK目录>`启用；`WORLD_FFT_MODEL=cpu|d4c|analysis|render|all`，其余尺寸保持原double。c2r补Hermitian、DC/Nyquist虚部置零，模型输入显式转float。实际IP内部是浮点接口的定点实现，不能预先保证足够精度。

独立工程复现`source build/create_world_fft_probe.tcl`；SDK zip由generate_target cmodel产生，不提交厂商DLL/头文件。下一步比较两段受控男声相对v23的数值差异并做独立FFT方向/尺度检查，再记录OOC资源/时序/时钟延迟和DMA预算。仅模型通过不等于PL板测或听感通过。

Round5恢复补充：首次start命令立即读取PCM为closed，异步启动后只读复核两PCM均RUNNING，原v23运行；该就绪等待不能省略。没有新现场录放。
