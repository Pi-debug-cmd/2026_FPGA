# WORLD v23 FFT + exp 完整布局布线

任务PL-20261027-01，2026-10-27，源实现b551646，Vivado2026.1 / Vivado MCP。独立工程world_fft_20261027，xc7z020clg400-2，音频HP0、exp HP1、FFT HP2，未覆盖原工程。

完整routed设计复核：100MHz，WNS+0.302ns/WHS+0.036ns，setup/hold失败端点均0、黑盒0、DRC Error0。17200LUT/29183FF/24.5BRAM/69DSP（LUT32.33%、BRAM17.5%、DSP31.36%）。bus skew全部MET，原始报告同目录留存。3输入/6输出外部IO延时尚未完整约束，DRC警告/建议保留，不代表外部接口完整签核。

bitstream已生成，Linux字节交换SHA `bdb4c0877e9818976dd7d9281a8ccc162018681cdf880bf117d2f55d3af72988`，4045564字节，gzip619028字节；双DMA地址和完整manifest见JSON。复现：`vivado -mode batch -source build/implement_world_exp_20261027.tcl -tclargs fft`；`python build/package_world_exp.py --fft`。位流在忽略目录，不提交Git。

RTL30帧/40960词与官方模型逐位相同（另轮已提交）。本轮只接受整机实现门；候选正在115200串口校验传输，音频服务临时停止，尚未加载FFT候选或进行FFT板端性能/听感测试。恢复载荷仍从板上已知SHA的原厂bit生成，不修改启动分区；JTAG当前可用，前轮已验证系统复位恢复原厂v23。
