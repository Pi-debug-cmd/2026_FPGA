# Vivado 2026.1 迁移报告（PL 可复现地基，2026-10-19）

## 结论

**迁移成功**：现有音频链工程在 Vivado 2026.1 下从零重建 → 综合 → 实现 → 位流，全流程通过，已约束的内部路径无失败端点且资源与 2018.3 基本一致。外部音频端口仍缺 input/output delay，不能把当前 WNS 解释成完整板级时序闭合。2018.3 不再需要。

## 做了什么

1. 确认本机无 2018.3 安装包（全盘检索），只有 2026.1；用户决定走"B：用 2026.1 重建"。
2. 从 `build/create_audio_pitch_dma.tcl` 派生 `build/create_audio_pitch_dma_2026.tcl`：固定输出 tag `audio_pitch_dma_2026`、去掉末尾 `exit`（MCP 会话内不能退）。
3. 唯一需要的 IP 版本改动：`axi_iic:2.0 → 2.1`（2026.1 目录里只有 v2_1；其余 IP 版本全部存在）。
4. 通过 Vivado MCP（会话 `vivado-20261019-210903-9ec967fe`）执行 create → synth → impl，输出到 `build/generated/audio_pitch_dma_2026/`。
5. 工程 BD 校验通过：`AUDIO_PITCH_DMA_VALIDATED_2026`；存在与 2018.3 相同的 AXI ID 位宽裁剪 WARNING（`BD 41-2384`，仅连接低位），属既有行为。

## 结果对比

| 指标 | 2018.3（历史） | **2026.1（本次）** | 变化 |
| --- | --- | --- | --- |
| Slice LUTs（实现后） | 8302 | **8105** | −2.4% |
| Slice Registers | 13179 | 13529 | +2.7% |
| Block RAM Tile | 5 | 5 | 持平 |
| DSP48E1 | 6 | 6 | 持平 |
| WNS @100 MHz | +2.160 ns | **+1.696 ns** | −0.46 ns，仍 >0 |
| 失败端点 | 0 | 0 | 持平 |
| 位流 | 3.90 MB | 3.86 MB | −1% |

综合阶段：LUT 9028 / FF 14362 / BRAM 5 / DSP 6、WNS +3.770 ns。

## 产物与证据

- 工程：`build/generated/audio_pitch_dma_2026/voice7020.xpr`
- 位流：`build/generated/audio_pitch_dma_2026/voice7020.runs/impl_1/zynq_wrapper.bit`（3.86 MB，21:37:40）
- 报告：`report/audio_pitch_dma_2026_{utilization,synth_timing,synth_drc,impl_utilization,impl_timing,impl_bus_skew,impl_drc}.txt`
- 脚本：`build/create_audio_pitch_dma_2026.tcl`、`build/synth_audio_pitch_dma_2026.tcl`、`build/implement_audio_pitch_dma_2026.tcl`

## 注意事项

1. **后续已做易失性加载**：交换字节后的位流可加载且 `fpga_manager=operating`，命令级 ALSA 播放/采集成功；未写入启动分区。该结果不包含真人试听、采集非静音、pitch DMA 黄金值或长期稳定验证，详见 `report/pl_2026_bitstream_board_verification.md`。
2. **构建日志中出现** `WARNING: [Project 1-5713] Board part '' set for the project is not found` —— 创建时未指定 board part（沿用 2018.3 脚本的做法），不影响综合实现；若后续要用 board 级约束需补 `set_property board_part`。
3. 构建时长：create ≈ 52 s，synth ≈ 16 min（含各 IP 综合），impl 到写位流 ≈ 3.4 min。
4. 实现报告指出 3 个输入端口和 6 个输出端口缺少 I/O delay；正式发布前必须补齐约束并重跑实现。
5. 会话：MCP 会话保留，可继续在 2026.1 里做 RTL 综合/仿真；xsim 仍须在 `D:\xsim_work` 下运行。
