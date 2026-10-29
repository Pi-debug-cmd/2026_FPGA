# PL-20261027-01 Round18：融合最小相位核整机接入与实现

## 结论

`xilinx.com:hls:world_minphase:1.0` 已接入完整 Zynq 音频工程，并在 `xc7z020clg400-2` 上完成 BD validate、综合、布局布线和 bit/bin 生成。最终 routed checkpoint 的 WNS 为 `+0.856 ns`、WHS 为 `+0.029 ns`，setup/hold/pulse-width 失败端点均为 0；32,065 条需布线网络全部完成，black box 为 0，DRC Error 为 0。Round18 的整机静态实现门通过。

本轮没有加载板卡，不能写成板端可用或实时通过。Linux FPGA Manager 载荷仍须按既有流程完成 32-bit 字内换序，且要先实现有界轮询驱动和恢复脚本。

## 接入拓扑与地址

- 原音频 DMA 保持 HP0，既有 WORLD complex-exp DMA 保持 HP1。
- HLS 输入、输出两个 32-bit AXI master 通过新的 `minphase_mem` 互联独占 HP2。
- HLS `s_axi_control` 接 `0x43C70000`，`s_axi_control_r` 指针参数接 `0x43C80000`。
- HLS 中断接 F2P bit14；首个板端驱动仍用有界轮询，避免新增中断依赖。
- 100 MHz FCLK0 同时驱动 HLS、HP2 和新互联。

## 复现

```powershell
$env:WORLD_MINPHASE_IP_REPO='D:/wpl_20261027_r16/m/solution/impl/ip'
$env:WORLD_MINPHASE_PROJECT='D:/wpl_20261029_full/m'
& 'D:/USER_Software/vivado/2026.1/Vivado/bin/vivado.bat' `
  -mode batch -source 'build/create_world_exp_20261027.tcl' -tclargs minphase
& 'D:/USER_Software/vivado/2026.1/Vivado/bin/vivado.bat' `
  -mode batch -source 'build/implement_world_minphase_20261029.tcl'
```

第一次在仓库长路径生成的工程已通过 BD validate，但在 `generate_target` 展开 HLS 浮点子核时超过 Windows 260 字符限制。相同源码和连接改在 `D:/wpl_20261029_full/m` 后通过；这项失败作为工具路径事实保留，不解释成 RTL 失败。

## 最终整机结果

| 项目 | 结果 |
|---|---:|
| WNS / TNS | +0.856 ns / 0.000 ns |
| WHS / THS | +0.029 ns / 0.000 ns |
| setup / hold / pulse-width 失败端点 | 0 / 0 / 0 |
| 内部未约束端点 / 无时钟寄存器 | 0 / 0 |
| 5 条 bus-skew 最小裕量 | +9.037 ns |
| routed / routing-error nets | 32,065 / 0 |
| Black box / DRC Error | 0 / 0 |
| Slice LUT | 13,910（26.15%） |
| Slice Register | 20,145（18.93%） |
| Block RAM Tile | 9.5（6.79%，19 BRAM18K 等效） |
| DSP48E1 | 47（21.36%） |

相对此前完整 WORLD-exp 工程（8,026 LUT / 13,283 FF / 6 BRAM Tile / 9 DSP），本轮新增整机开销为 5,884 LUT、6,862 FF、3.5 BRAM Tile、38 DSP，资源仍有充足余量。

## DRC 与时序限制

DRC 共 169 项：131 Warning、38 Advisory、0 Error。Warning 主要为 HLS 浮点 DSP 流水建议（`DPIP/DPOP` 共 104 项）、既有音频 RAM 异步控制、LUT 方程和一条无可路由负载提示。全部保留，不把“零 Error”表述为“零警告”。

内部时序覆盖完整，但现有板级音频约束仍有 3 个输入和 6 个输出未设置外部 I/O delay；因此本结果是内部整机时序通过，不是外部接口完整 signoff。

## 生成物

生成物不提交 Git：

- `zynq_wrapper.bit`：4,045,767 bytes，SHA-256 `e2131f0c4306f891e05f9a5aa9cee33077ad794b3ab2a2a53e0eac9d67b8cee3`
- 原始 `zynq_wrapper.bin`：4,045,564 bytes，SHA-256 `2e8517d9d126261fd397ec76e3209b111d9cee232d6374bdc9bb099473d79117`
- routed DCP：15,090,535 bytes，SHA-256 `f3aaccbd59a381751b654f34759e09b2c612082548f9d547ec512bfaa287a298`

机器可读数据和原始报告哈希见同名 JSON，简明日志见同名 TXT。

## 下一步

生成换序后的 Linux 临时载荷；实现 DMA coherent 缓冲、两组 AXI-Lite 寄存器和超时轮询驱动；用与 Round16 同源的 513-bin 静默向量做板端对照并验证恢复原厂 bit/v23。任何录音、播放或试听前仍需当次操作者确认准备好。
