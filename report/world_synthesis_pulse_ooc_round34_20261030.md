# Round34：WORLD 合成脉冲核 OOC 实现

## 结论

**ACCEPTED（OOC routed 门）**。在 `xc7z020clg400-2`、100 MHz 目标下，干净短路径工程
完成 C-sim、HLS 综合、IP 导出及 Vivado OOC 布局布线。最终 WNS=`1.919 ns`、
WHS=`0.048 ns`，14930 个可路由网络全部完成，DRC 无 Error/Critical Warning。

这仍不是完整音频工程签核：OOC 的 AXI/时钟边界没有顶层位置约束，必须由下一轮完整
PS/音频/minphase/pulse 工程重新验证时序和互连资源。

## 复现条件

- 基准提交：`506d2dd`
- 工具：Vitis HLS / Vivado 2026.1
- part：`xc7z020clg400-2`
- 工程：`D:/wpl_20261030_r34/pulse_ooc`（生成物，不入 Git）
- 时钟：10 ns
- 源码 SHA-256：`43a21ed4d8c3d218f7e1b1e8b82e9876db3035e9435f5752da3d9b708cbaaaa8`
- testbench SHA-256：`d826f0f4fe10b99e4ce380d69c2cda406209be57516bc92a2e20137f3feb28bd`
- 实现脚本 SHA-256：`3d10060a52a199dcf2a16818b469d0773c9c50ff19fc78133573b72487038fd9`

```powershell
$env:WORLD_SYNTH_HLS_PROJECT='D:/wpl_20261030_r34/pulse_ooc'
& 'D:/USER_Software/vivado/2026.1/Vitis/bin/vitis-run.bat' --mode hls --tcl --input_file ./build/probe_world_synthesis_pulse_hls.tcl
& 'D:/USER_Software/vivado/2026.1/Vitis/bin/vitis-run.bat' --mode hls --tcl --input_file ./build/impl_world_synthesis_pulse_hls.tcl
```

## 数值、资源与时序

- C-sim：5/5；worst relative-L2=`1.72913210714e-7`，max abs=`5.03438131873e-7`。
- HLS 延迟估算仍为最大 56650 cycles（0.567 ms @100 MHz）。
- routed：6735 LUT、8776 FF、8 BRAM36 Tile（16 BRAM18K）、22 DSP、3382 Slice。
- WNS=`1.918719 ns`，WHS=`0.047895 ns`；实现报告等效 achieved period=`8.081 ns`。
- route：14930 fully routed、0 routing errors、0 unrouted/partial。

相对 Round31 HLS 估算，routed LUT 从 10920 降至 6735，DSP保持22，BRAM18K从18降至16。
以 Round18 已路由的完整音频+minphase 工程（13910 LUT、20145 FF、9.5 BRAM Tile、47 DSP）
线性相加形成保守预估：20645 LUT（38.81%）、28921 FF（27.18%）、17.5 BRAM Tile
（12.5%）、69 DSP（31.36%）。尚未计入新增 AXI interconnect，但各资源余量均大于60%，
满足本轮至少20%余量门。

## DRC 与限制

DRC 为 68 Warning、21 Advisory、0 Error。主要是浮点 IP 流水建议（DPIP/DPOP）；
`ZPS7-1`来自纯OOC壳没有PS7，`RTSTAT-10`为无可路由负载。OOC 另有
`HD.CLK_SRC`/边界 pin 未固定警告，因此时序必须在完整设计重签。

本轮没有生成板上 release、加载 FPGA、录音或播放；Round30 持久运行状态未改变。
