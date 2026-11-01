# WORLD v23 FFT PS/PL集成 Round 7

基准9092e1f；任务PL-20261027-01，2026-10-27。独立候选工程`world_fft_20261027`保留音频HP0、exp HP1；新增FFT HP2与DMA 0x40410000。无参数时仍构建原exp工程；参数`fft`才新增模块，不覆盖原工程。

## 合约

- FFT采用Round6通过的xfft9.1浮点/25bit旋转因子，1024/2048、正反向、自然序、未归一化，与WORLD的接口一致。
- 单次DMA输入：64bit头低24位为XFFT config（NFFT低5位=10/11，forward bit8），之后N个64bit `{imag_f32,real_f32}`。输出恰好N个64bit复数，无头。c2r在PS补Hermitian，r2c仅取前N/2+1；DC和Nyquist虚部置零。
- AXI包装先握手配置，再接N数据，最后等待输出TLAST；持续valid/ready背压，计数与TLAST不匹配置protocol_error。一次只接一个事务。
- 新root-only临时驱动`/dev/world_fft`独立分配coherent TX/RX，接收先于发送，串行化同核事务，20ms超时和DMA状态错误即返回EIO并锁住，不能静默退回CPU；只/tmp加载，不修改设备树/启动。
- PS候选显式构建`-CacheFftPlans -FftPl`；`WORLD_FFT=cpu|pl2048|pl1024|pl`，未支持的尺寸仍double；`WORLD_EXP`独立控制已有exp。计prepare/DMA/unpack/互斥等待，避免以核耗时冒充收益。

## 构建及门槛

- 完整Vivado命令：`vivado -mode batch -source build/implement_world_exp_20261027.tcl -tclargs fft`；本次通过Vivado MCP创建、validate_bd_design并启动综合，尚未有整机时序结论。
- ARM：`build/build_world_exp.ps1 -Target arm -CacheFftPlans -FftPl -WorldRoot <WORLD>`；kernel：WSL运行`build/build_world_fft_driver.sh <matching-linux-src> <matching-build>`。二进制和module已编译，SHA见build JSON。probe警告严格检查只豁免上游fft.cpp的`{0}`聚合初始化警告。
- 模型生成RTL向量：质量脚本指定`--vectors-only --out build/generated/world_fft_rtl_vectors`；打开独立整机工程后`source build/run_world_fft_sim.tcl`。30帧覆盖两尺寸/方向切换、零/脉冲/常数/随机/弱信号，后半加入输入空拍与输出背压，全部复数float位必须与官方C模型相同；仿真进行中。
- 接口与数值通过、完整布局布线/DRC与恢复镜像核验后，才临时加载并执行静默板测：`world_fft_dma_probe`128次对照原double FFT，`world_fft_pl_trial.py`两输入各baseline/cpu/fft2048/fft1024/fft_all/exp_only/combined。CPU必须逐字节一致，PL路径SNR≥75dB/最大PCM16误差≤8（兼容已有exp误差），必须有真实PL调用且exp零fallback。

不预设FFT上PL必然更快：1024/2048分别单测，考虑PS转换、DMA和双线程争用，再选默认。当前板上原厂PL和v23运行；FFT候选尚未上板，没有新现场录放、听感或高实时验收。恢复脚本增加先卸载FFT测试module，其余沿用上一轮音频/I2C重绑修复。
