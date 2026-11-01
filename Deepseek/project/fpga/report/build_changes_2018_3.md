# M1 变更记录（Vivado 2018.3 建工程）

- 日期：2026-10-25
- 构建根：`D:\g_build\pl_20261025\`（仓库文件只读，未改动）
- Vivado：`D:\Vivado\Vivado\2018.3\bin\vivado.bat`，v2018.3 (64-bit)，SW Build 2405991
- 器件：`xc7z020clg400-2`

## 资产复制方式

仓库脚本以 `[file dirname [info script]]/..` 计算 root，因此**保持同样相对目录结构**复制到构建根后，
`create_audio_pitch_dma.tcl` 无需改任何路径即可运行：

```
D:\g_build\pl_20261025\
  build\create_audio_pitch_dma.tcl      (复制后仅做下述 BD 修改)
  build\synth_2018_3.tcl                (新写；替代 synth_audio_pitch_dma.tcl)
  build\impl_2018_3.tcl                 (新写；替代 implement_audio_pitch_dma.tcl)
  src\rtl\axis_pitch_shift.v            (原样)
  src\rtl\pcm_delay_ram.v               (原样)
  board\vendor_inputs\ps7_config.tcl    (原样，531 项 PS 配置)
  board\vendor_inputs\audio_i2c.xdc     (原样)
  board\vendor_inputs\my_iobuf.v        (原样)
  board\vendor_inputs\ip_repo\axi_dynclk (原样，digilentinc.com:ip:axi_dynclk:1.2)
```

## IP / 版本兼容性核查（2018.3 IP 目录实际查询）

| IP | 脚本请求的 VLNV | 2018.3 是否自带 | 处理 |
|---|---|---|---|
| processing_system7 | xilinx.com:ip:processing_system7:5.5 | 是 | 未改 |
| audio_formatter | xilinx.com:ip:audio_formatter:1.0 | 是（data/ip/xilinx/audio_formatter_v1_0） | 未改 |
| i2s_receiver | xilinx.com:ip:i2s_receiver:1.0 | 是 | 未改 |
| i2s_transmitter | xilinx.com:ip:i2s_transmitter:1.0 | 是 | 未改 |
| axi_dynclk | digilentinc.com:ip:axi_dynclk:1.2 | 由本地 ip_repo 提供 | 未改 |
| axi_dma | xilinx.com:ip:axi_dma:7.1 | 是 | 未改 |
| axi_iic | xilinx.com:ip:axi_iic:2.0 | 是（2026 版脚本用 2.1，2018.3 无 2.1） | 保持 2.0 |
| axi_interconnect | xilinx.com:ip:axi_interconnect:2.1 | 是 | 未改 |
| proc_sys_reset | xilinx.com:ip:proc_sys_reset:5.0 | 是 | 未改 |
| util_vector_logic / xlconstant / xlconcat | 2.0 / 1.1 / 2.1 | 是 | 未改 |

结论：**不需要改任何 IP 版本号**；`axi_iic:2.0` 只有 2018.3 的目录里存在，保持原脚本值。

## BD 修改（唯一的设计改动：固定 ratio 常量 → AXI GPIO）

原因：仓库 v2 驱动 `src/kernel/pitch_dma_proxy.c` 与 `board/pitch_dma_control_overlay.dts`
已经约定 `0x41200000` 是双通道 AXI GPIO（ch1=ratio_q16，ch2=低有效 DSP reset）；
2026-10-11 的控制版设计（`report/pitch_control_development_20261011.md`）就是这个结构。
原 `create_audio_pitch_dma.tcl` 用的是 `xlconstant 86856`，无法满足“写 ratio_q16 并读回”。
因此把常量替换为 AXI GPIO，**变调核 RTL 一行未改**。

对 `build/create_audio_pitch_dma.tcl` 的全部修改（4 处）：

1. 第 42-43 行 `xlconstant` → `axi_gpio:2.0`：
   ```
   CONFIG.C_IS_DUAL {1} CONFIG.C_GPIO_WIDTH {18} CONFIG.C_GPIO2_WIDTH {1}
   CONFIG.C_ALL_OUTPUTS {1} CONFIG.C_ALL_OUTPUTS_2 {1}
   CONFIG.C_DOUT_DEFAULT {0x00015348}   ; 上电即 86856，保持原固定比例行为
   CONFIG.C_DOUT_DEFAULT_2 {0x1}
   ```
2. `ctrl_ic` `NUM_MI {6}` → `{7}`，新增 `M06_AXI` → `ratio/S_AXI`；
   M00..M06 的 ACLK/ARESETN 循环补 M06。
3. `ratio/dout` → `ratio/gpio_io_o` 接 `pitch/ratio_q16`。
4. 地址分配新增 `0x41200000`（range 0x10000）给 `ratio/S_AXI/Reg`。

未改动：PS7 配置（531 项）、音频 Formatter/I2S/dynclk、AXI DMA（simple mode, 32-bit, SG length 23）、
中断 concat 位（I2C=2、I2S/Formatter=3..6、pitch DMA MM2S/S2MM=12/13）、全部引脚 XDC、HP0/HP1 分配。

## 与 2026-10-11 控制版的已知差异（如实记录）

2026-10-11 的控制版把 GPIO ch2 的 DSP_RUN 真正接到变调核 `aresetn`（默认保持复位）；
本 2018.3 构建为**最小改动**，ch2 只是可读写寄存器，`pitch/aresetn` 仍由 `crst/peripheral_aresetn` 驱动。
影响：`PITCH_DMA_CONFIGURE` 里的“先复位再配置”不会清空核内 2048 样本 RAM/相位。
因此数值比对必须在**刚加载位流后的连续流**上做（本次 M3 正是这样做的），不能在同一个位流里反复复位重跑。

## 运行记录（原始日志在 logs/）

- `create_2018_3.log` 首次跑通（无 GPIO）：`AUDIO_PITCH_DMA_VALIDATED`
- `create2_2018_3.log`：GPIO 的 s_axi_aclk 未接，`[BD 41-758]` 时钟未连接 → validate 失败
- `create3_2018_3.log`：补 `ratio/s_axi_aclk`、`ratio/s_axi_aresetn` 后 `AUDIO_PITCH_DMA_VALIDATED`
