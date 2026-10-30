# Round15 HLS级间约束及RTL工具失败

任务PL-20261027-01，2026-10-27，实现e98e787。显式LOOP_FLATTEN off后，C-sim24例通过、relativeL2最大8.5944e-7；HLS估算30229拍@100MHz、10007LUT/7732FF/8 BRAM18K/38DSP。不是routed或DDR实测。

RTL cosim未进入执行：Vivado生成float-add IP时Windows完整路径超过260字符，日志明确Could not add generated file / file path is too long，最终Verilog Fail/NA。失败不是数值不符；也不能写RTL通过。完整去除空白行的工具日志附world_minphase_cosim_round15_failure_20261027.txt。首次C-sim include引号被HLS误识为相对路径，入口已修正为无引号-I路径，本仓库路径无空格。

板端静默轮次结束后执行原服务stop、卸载两个自有module、sync、正常reboot。启动分区与v23未改；原v23 SHA f12da25e...、factory bit SHA16cb36...匹配，FPGA operating、原服务pid604、采集/播放PCM RUNNING、内核Not tainted、自有模块未加载。只读恢复证据world_full_pl_baseline_restore_round15_20261027.json。未发起新的现场试听或把恢复提示音算测试。

下一步短路径HLS工程重跑，源码仍在仓库，生成物不入Git。
