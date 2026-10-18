# 可调比例与DSP复位接口 v2

状态：2026-10-11已通过实板配置/复位数值测试：16组双格式黄金向量全符，错误接口及连续状态测试通过；三轮实时试听脚本零xrun，用户听感待反馈。旧固定比例位流保持可用，不能用v2设备树驱动旧位流。

控制沿用AXI GPIO 2.0双通道，地址0x41200000；不创建GPIO内核设备，由DMA客户端独占映射。寄存器偏移依据 [AMD PG144寄存器空间](https://docs.amd.com/r/en-US/pg144-axi-gpio/Register-Space)，同时核对2018.3生成IP配置。

| 偏移 | 内容 | 契约 |
| --- | --- | --- |
| 0x00 | channel1 DATA，18位ratio_q16 | 32768～131072，即0.5～2.0；复位期间写入 |
| 0x08 | channel2 DATA，bit0 DSP_RUN | 0保持DSP复位，1运行；上电默认0 |

两个通道均配置all outputs。输出数据寄存器读值不能当作参数回读，读操作只用于冲刷MMIO写入；驱动不假设输出寄存器会返回上次写值。实际语义见 [PG144数据寄存器](https://docs.amd.com/r/en-US/pg144-axi-gpio/AXI-GPIO-Data-Register-GPIOx_DATA)。

DSP复位为全局peripheral_aresetn与DSP_RUN的AND。只复位变调核，不复位Codec、音频Formatter或DMA。释放后清零2048个RAM单元；100MHz下20.48微秒，驱动等待50微秒后才返回。

`PITCH_DMA_CONFIGURE = _IOW('P',2,8)`，参数为两个uint32：ratio_q16、reserved（必须0）。加锁后先保持复位1微秒、写比例、释放并等待清零。配置操作清空相位、RAM与指针，用于每次运行开始，不能当无缝变调。未配置v2核心的PROCESS返回EINVAL，避免向仍保持复位的核心送DMA而超时。

DMA设备只允许一个open，其他open返回EBUSY，防止不同音频进程在块间偷偷重置状态。旧v1设备仍支持PROCESS，CONFIGURE返回EOPNOTSUPP。DMA故障后继续锁定EIO；DSP reset不能证明DMA故障已恢复，不自动解除故障锁。

ARM32工具：`pitch_dma_stream 256 native_s24 86856` 或 `pitch_dma_stream 257 pcm32 65536`。第四参数提供时执行一次configure/reset；不提供时保留已有状态（v2必须曾配置），TLAST不重置。ratio=65536为核内旁路，录放路径仍有设备缓冲及PCM16量化，不等于整机零延迟。

预备板测：`sim/generate_dma_control_vectors.py`准备16组黄金结果（7比例×2格式，再重复86856×2），`board/verify_dma_control.py`检查每次复位、边界拒绝、reserved位、独占open及未知ioctl。完成后才试听原声/升调/降调，再做10分钟稳定性。测试包：`build/generated/pl_control_bundle`；旧固定包：`build/generated/pl_bundle`。
