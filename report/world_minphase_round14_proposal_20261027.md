# Round14 固定周期融合核优化

任务PL-20261027-01，日期2026-10-27，基准49627af。FFT改为固定10级、每级512蝶形，10bit反转组合逻辑、512点float32旋转因子ROM；输出exp/sin/cos循环请求II=1。每级每地址仅访问一次，inter依赖约束仅作用于同级；级间保持顺序，必须RTL cosim验证。

构建入口延续Round13；新增gen_world_minphase_twiddles.py可重生ROM，check_world_minphase_quality.py复现两段完整语音75dB/最大误差3门。HLS tcl仍使用独立生成工程，不碰厂商或板卡。24例host单元已执行；完整语音和HLS结果独立提交。不将host数值称为RTL通过。

本轮也去除Round13附带厂商TXT行尾空格，仅格式，数值不变。
