# PL-20261027-01：整机实现与 Vivado MCP 复核

2026-10-27；基准提交 `69544be`。Vivado 2026.1，xc7z020clg400-2。通过命令行完成独立工程布局布线和 bit/bin 生成，再按用户建议通过 `tools/mcp_vivado.py` / Vivado MCP 打开**完整 routed checkpoint**重新报告时序、资源、DRC 和 bus skew。

| 检查 | 结果 |
| --- | --- |
| 100MHz FCLK0 设置 / 保持裕量 | WNS +1.391ns / WHS +0.036ns |
| 设置 / 保持 / 脉宽失败端点 | 0 / 0 / 0 |
| 内部未约束端点 / 无时钟寄存器 | 0 / 0 |
| 完整布线设计黑盒 / DRC Error | 0 / 0 |
| 整机 LUT / FF / BRAM36等效 / DSP | 8026 / 13283 / 6 / 9 |
| exp核 LUT / FF / RAMB36 / DSP | 463 / 273 / 1 / 9 |
| 5条 bus skew 约束最小裕量 | +8.996ns |

不是外部接口全时序签核：沿用音频设计缺少3个输入、6个输出的外部延时约束，且DRC仍有36项Warning、4项Advisory（DSP寄存、RAM异步控制等）；不得把“零Error”写成“无警告”。最初尝试独立打开综合顶层DCP时，OOC IP仍为外部引用，报告不完整，因此**该报告不作为资源验收**；本结论来自随后打开的完整route DCP。

Linux FPGA Manager候选字序载荷4,045,564 bytes，SHA256 `e0e90fa86bfe10d67d0d606be2e6aba2ca6634fddf96bfba849ecdab1df5f0c0`。压缩包336,822 bytes，串口传输SHA已校验。生成物不入Git，不修改启动分区。

复现：`vivado -mode batch -source build/implement_world_exp_20261027.tcl`（新输出目录，不覆盖现有工程），`python build/package_world_exp.py`；MCP：`python tools/mcp_vivado.py start`，在自己的会话中 `open_checkpoint {.../impl_1/zynq_wrapper_routed.dcp}`，运行 `report_timing_summary`、`report_utilization`、`report_drc`、`report_bus_skew`。完整机器记录及四项原始报告见同前缀JSON和TXT。

下一步仅静默板测：校验恢复载荷→停服务/解绑旧PL外设→临时加载→513-bin DMA向量→同输入v23/CPU/模型/PL文件对比及实测耗时。任何现场录放仍须当轮确认。
