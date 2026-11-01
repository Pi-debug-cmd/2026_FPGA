# Round13 首个融合核原型

任务PL-20261027-01，2026-10-27，基准622fbd8。源码src/hls/world_minphase.cpp把1024点镜像log谱→FFT→倒谱lifter→FFT→exp/cos/sin封装为单核，使用固定数组、共享radix2蝶形，无逐FFT PS回传。输入513点float log谱，输出513点复数滤波器；显式保留WORLD/Ooura c2c共轭约定。

这是最小相位阶段，并非完整合成；log计算、激励与overlap-add仍在PS。按用户全计算链PL目标逐层推进。原方案随机激励改为必须复现WORLD种子/消费顺序，不能换成不同LFSR；普通STFT也不能替代CheapTrick。

宿主单元：MinGW编译sim/tb_world_minphase.cpp与上游common/fft/matlabfunctions，24个光滑/交替/不规则log谱及多种电平对照。完整语音：build/build_world_exp.ps1 -Target host -CacheFftPlans -MinphaseModel -WorldRoot <WORLD0.3.5>；WORLD_MINPHASE_MODEL=cpu|fused，WORLD_EXP=cpu。候选wrapper只在host显式开启，默认仍CPU。

HLS：vitis-run --mode hls --tcl --input_file build/probe_world_minphase_hls.tcl --work_dir build/generated/world_minphase_hls_run。目标xc7z020clg400-2/100MHz。结果作为独立测试提交；本方案不改板卡、启动分区、默认程序。
