# PL接入：当前原型与板级约束

2026-10-10。PS-only可听基线是v5，先读 `project_guide.md` 与 `report/live_audio_20261010.md`。本文件不是部署批准或上板成功记录。

## 独立数据通路原型

`build/create_pitch_dma_prototype.tcl` 在Vivado2018.3生成PS GP0控制、HP0内存回传、AXI DMA双向32位流、已验证的变调RTL。固定Q16=86856，PCM16符号扩展到32位；TLAST由DMA传播，算法状态跨块保留。输出保存在独立目录，已有项目拒绝覆盖。初次构建发现PS IRQ_F2P未开启及尝试设置DMA只读参数，已修正；`-tclargs`须位于Vivado命令末尾，否则后面的参数会被当脚本参数。

v2在 `build/generated/pitch_dma_prototype_v2/` 已完成validate_bd_design及wrapper生成，退出0；证据 `report/pitch_dma_prototype_v2_retry.log`。DMA原型自动分配控制地址0x40400000。日志仍有模块解析局部参数、clock-domain传播、IRQ SUGGESTED_PRIORITY以及HP0 AXI ID位宽1/6告警；这些须在完整工程中核对生成连接和读写回传，**不能以validate通过替代仿真、综合、实现或上板验证**。没有生成/加载位流。

**该原型使用默认PS配置，没有音频外设，不能烧录/加载到板卡。** 其DDR/MIO、地址和IRQ位置不代表当前Linux或底板契约。使用-1仅为当时独立工具检查条件。用户2026-10-10指定以A盘为准，后续板级器件采用xc7z020clg400-2，不再等待丝印。

## 完整板级接入条件

- 经核对的本板PS配置：参考 `交接/核心材料/pl_kernels/build_2018/ps7_config.tcl`、厂商工程与当前板况。不可套其他PYNQ板preset。核对DDR、MIO、FCLK与EMIO I2C。
- 保留音频驱动可见的原外设与布局。交接构建脚本记录audio_dynclk 0x43C20000、Formatter 0x43C40000、I2S Rx 0x43C50000、Tx 0x43C60000；中断连接为Tx F2P位3、Formatter播放位4、采集位5、Rx位6。这些为源码依据，合入前仍须与实际设备树逐项比对，不能把原型默认分配地址或位0/1覆盖为音频配置。
- 音频Formatter通过HP0访问DDR；新增变调DMA应独立评估HP1及空闲地址/IRQ，保留现有录放路径，避免与旧GEMM或设备树资源冲突。
- 现有音频流是32kHz S24_LE双声道容器；变调核是PCM16单声道符号扩展32位流。先由PS显式转换并使用独立DMA验证；不得直接接入Formatter/I2S流而忽略格式、通道及音频元信息。16kHz注册与重采样仍是独立契约。
- 运行时配置比例需要经验证的控制接口与更新边界；当前常数比例原型只用于固定比例回传，不支持现场注册调参。
- 板端非PYNQ已确认系统：先核对可用驱动、连续物理缓冲及缓存一致性。不得用任意malloc物理地址或旧GEMM内核模块假充AXI DMA驱动。

板级验证顺序：保留PS-only基线→本板配置/资源核对→完整工程构建与时序→可恢复位流切换→旁路块回传→定点变调黄金比对→接实时录放→PS-only/PS+PL公平延迟对照。未通过前G1/G3不标完成。
