# PL-20261027-01 Round17：最小相位融合核 OOC 实现

## 结论

Round16 已通过 24/24 Verilog RTL 数值对照的 `world_minphase` HLS 核，在 `xc7z020clg400-2`、100 MHz 约束下完成 OOC 综合、布局和布线。布线后 WNS 为 `+1.327 ns`、WHS 为 `+0.053 ns`，无 setup/hold 失败端点，未布线网络为 0，black box 为 0，DRC Error 为 0。因此核级实现门通过，可以进入整机连接阶段。

这不是整机时序签核：OOC 边界未设置 `HD.CLK_SRC` 和 `HD.PARTPIN_LOCS`，Vivado 也明确提示 OOC 模式不会执行全部连接型 DRC。加入 PS、AXI、DMA/HP 端口及现有音频逻辑后必须重新跑完整实现。

## 复现

基准提交：`12d23894d308be30b44fd73292bed34cd0c18a8c`

```powershell
$env:WORLD_HLS_PROJECT='D:/wpl_20261027_r16/m'
& 'D:/USER_Software/vivado/2026.1/Vitis/bin/vitis-run.bat' `
  --mode hls --tcl --input_file 'build/impl_world_minphase_hls.tcl'
```

脚本执行 `export_design -flow impl -rtl verilog -format ip_catalog`。短路径工程用于避开 Windows 260 字符路径限制；正式源码仍在仓库。

## 布线后结果

| 项目 | 结果 |
|---|---:|
| 目标周期 | 10.000 ns（100 MHz） |
| 实现后达到周期 | 8.673 ns |
| WNS / TNS | +1.327 ns / 0.000 ns |
| WHS / THS | +0.053 ns / 0.000 ns |
| setup / hold 失败端点 | 0 / 0 |
| 未布线 / 部分布线网络 | 0 / 0 |
| Slice LUT | 4,996（9.39%） |
| Slice Register | 5,769（5.42%） |
| DSP48E1 | 38（17.27%） |
| BRAM18K 等效 | 7（3.5 Block RAM Tile，2.50%） |
| Slice | 1,992 |
| SRL | 224 |
| Black box | 0 |

HLS 导出的布线报告将本核资源记为 `4996 LUT / 5769 FF / 38 DSP / 7 BRAM18K`，比 Round16 的综合估算略低，不能直接与完整设计剩余资源相加后宣称整机可用。

## DRC 与保留风险

DRC 共报告 125 项：94 项 Warning 和 31 项 Advisory，无 Error 或 Critical Warning。94 项 Warning 包含 DSP 输入/输出寄存建议 `DPIP-1=47`、`DPOP-1=30`、`DPOP-2=15`，以及 OOC 包装边界的 `RTSTAT-10=1`、`ZPS7-1=1`。当前时序已通过，DSP 流水建议不是本轮阻断项；整机实现仍须重新检查。

另外保留以下限制：

- OOC 时钟端口缺少顶层实际 BUFG 位置，当前正裕量不能替代整机 clock skew 检查。
- OOC AXI 边界缺少实际 partition pin 路由信息，边界路径必须在整机中重新收敛。
- Round16 XSIM 对显式 `inter false` 报出的动态地址依赖警告仍保留；24 例数值通过不等于形式证明。
- 本轮未生成或加载板卡位流，未录音、播放或试听。

机器可读摘要和复现哈希见 `report/world_minphase_ooc_round17_20261029.json`，纯文本摘要见同名 `.txt`。

## 下一步

把导出的 IP 接入现有 Zynq 音频设计，连接 AXI-Lite 控制和 DDR 主端口，生成完整 address map；随后依次执行整机 validate、综合、布局布线、DRC、资源和时序门。只有整机门通过后，才进行可恢复的静默板端向量测试；任何现场录音、播放或试听开始前仍需当次操作者确认准备好。
