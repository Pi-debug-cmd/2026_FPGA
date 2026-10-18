# 2026-10-10 A盘配置的音频与变调DMA候选

用户明确以A盘厂商资料为准，板级使用xc7z020clg400-2。现已完成本机候选位流及DMA客户端ABI检查，**尚未完成PL回传、PL录放或G1验收**。

## 本板配置与构建

`build/prepare_vendor_audio.py` 比对交接PS参数和A盘BD，531项全部相同；只抽取厂商音频及三组I2C共24条XDC，复制厂商axi_dynclk到独立输入目录。审计 `vendor_audio_audit.json` 记录原文件SHA，A盘文件保持原样。

生成入口 `build/create_audio_pitch_dma.tcl`，器件-2、本板DDR/MIO/时钟；音频Formatter仍走HP0，PCM16符号扩展32位的独立AXI DMA/变调核走HP1，控制基址0x40400000。固定Q16=86856，每块TLAST传播、状态跨块保留。Linux已核对音频控制地址和中断位置。

完整设备树发现F2P位0/1已用于视频时序和UART；新增DMA改为位12/13（DT SPI56/57），保留I2C位2、音频位3～6。源脚本已更新，综合前将初版BD修正并重新生成。证据 `board_platform_inventory_full_20261010.json`。

首轮整体综合在展开阶段运行约8分钟后停止并切换分IP方式；补查交接历史显示Formatter单IP本就耗时约11分钟，不能将展开耗时当逻辑故障。分IP综合成功，`audio_pitch_dma_synth_ooc.log`：9316 LUT、14380寄存器、5 BRAM、6 DSP，估计WNS+3.750ns。独立变调核的旧-1结果另存，不改写其器件条件。

实现及位流成功：`audio_pitch_dma_impl.log`，8302 LUT、13179寄存器；时序报告WNS+2.160ns、WHS+0.017ns，已约束路径无失败，另有bus-skew报告。DRC没有Error/Critical Warning，6个DSP输入寄存器建议、1个无可布线负载告警、2个BRAM write-first提示。**厂商XDC只有引脚/电平，报告仍有3个输入、6个输出未设外部延时；尚不能宣称完整音频IO时序签核。**

## 板端DMA客户端与环境

板端5.15.0-xilinx、CONFIG_MODVERSIONS=y、XILINX_DMA=y、CMA=256MiB，configfs overlay与FPGA Manager可见。原交接Module.symvers为空、旧kernel_src路径不存在，用户确认没有完整构建目录。

使用现有Ubuntu-20.04 WSL，安装ARM交叉编译/内核构建必要依赖（25包、约101MB），下载当前板端内核配置并核SHA。A盘linux-ebf-xilinx-v2022.2源码SHA及安全路径/链接检查记录在 `build/generated/kernel_abi_v2/source_manifest.json`。首轮/tmp构建目录在后续访问时已消失，改为 `/var/tmp/2026_fpga_kernel_20261010`；初版只构建vmlinux未导出最终Module.symvers，修正为vmlinux+modules。当前已得到非空符号表和5.15.0-xilinx构建环境。

开启MODVERSIONS时，modules_prepare不足以生成符号校验表，需完整内核构建；依据 [Linux 5.15外部模块文档](https://www.kernel.org/doc/html/v5.15/kbuild/modules.html)。这里仅构建工具与符号，不安装或更换板卡内核。

`src/kernel/pitch_dma_proxy.c` 使用内核DMAengine及coherent缓冲，接收先启动、发送随后启动；有超时、状态核对和移除期间文件描述符引用保护。ARM32 ioctl以一块PCM16符号扩展int32输入并原位回传。参考 [Linux 5.15 DMAengine客户端接口](https://www.kernel.org/doc/html/v5.15/driver-api/dmaengine/client.html)。错误后停止两路并锁定失败状态；固定比例原型没有独立DSP复位，不能把重新打开或只复位DMA当算法状态恢复。

`src/ps/pitch_dma_stream.c` 已编译：int32格式或native_s24双声道左输入→PCM16→int32 DMA→PCM16→双声道低24位；默认256帧块，不重采样。固定比例对应当前位流，不支持现场注册改比例。

ABI实际检查 `board_pitch_dma_driver_abi_20261010.log`：新模块加载0、仅注册无匹配设备、卸载0，未启动DMA；工具非法0/4097帧返回2、设备缺失返回3。没有版本/符号拒绝；dmesg的out-of-tree taint是此次模块注册记录，不是DMA成功证据。

## 候选与回退

候选包 `build/generated/pl_bundle/manifest.json`：位流、hwh、module、工具、设备树源及SHA。Zynq FPGA Manager厂商源码要求每32位字节交换、同步字66 55 99 aa；候选 `audio_pitch_dma_swap.bin` 已按此生成，4045564字节，SHA `63911132384d018aba20090a521d4488c6d361809c9538e7ae2d6fa707015be3`。

原厂启动位流 `/boot/bit/zynq7020.bit` SHA `16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61` 已核对，2022.2生成、7z020clg400。只读解析并准备 `/tmp/codex_pl_trial_20261010/factory_restore_swap.bin`，SHA `af275946c15ae958e9bed16c12f6cab45b63ebecc18645cec24176315db7fc60`；没有加载回退镜像，恢复流程尚待验证。启动脚本读取/bit/${bitfile}并loadb，启动分区文件保持原样。

设备树候选已dtc编译到/tmp，仅有addr-size提示，尚未应用。当前Linux仍绑定视频、GPIO、UART、音频和dynclk等PL外设，**切换前必须停止相应消费者并按依赖卸载/重绑，防止访问精简工程里不存在的地址，并刷新音频时钟状态**。读取预检查入口 `board/pl_switch_preflight.py`；GPIO消费者和音频按键监听须查实际状态，不调用旧厂商全局kill脚本。

下一项：候选传输校验→依赖/回退预检查→现场可恢复的PL切换→固定比例、连续跨块PCM32黄金比对→native格式与麦克风试听。通过前保持v5 PS-only作为可听基线，G1/G3未完成。
