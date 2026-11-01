# WORLD v23 PL加速交接（2026-10-27）

任务PL-20261027-01，Hardware-A/Codex，PR16，分支agent/Pi-debug-cmd/PL-20261027-01。用户已放弃Deepseek，要求能放PL就放PL、最好完整计算链PL；后续以阶段融合为主，非逐FFT卸载。

## 安全基线

根工作区有历史未提交文件，不动。独立worktree位于tmp/world_v23_pl_worktree。COM4/115200，Linux5.15.0-xilinx，1GB DDR，7020-2。板卡在Round15静默诊断后正常reboot，已恢复原厂bit/v23，两个PCM RUNNING、自有模块卸载、内核Not tainted。恢复证据report/world_full_pl_baseline_restore_round15_20261027.json。启动分区与原v23未改。没有新的现场录放授权；新测试必须单独确认准备。

原v23 SHA f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7；factory bit SHA16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61。不要变串口波特率（921600失败）；JTAG目前可用，XSDB系统复位能恢复。不要同一boot反复audio驱动热重绑（Bad of_node_put）；恢复脚本仅重绑audio/I2C，display等留正常启动。

## 已验证与否决

- PL exp与模型一致，相对v23语音SNR约79dB/最大误差3，渲染RTF约下降6.2%；20秒低缓冲现场2次欠载、2帧有声，失败结论保留。
- ARM FFT计划复用18次板测逐字节相同，文件墙钟约下降9.6–10.7%；不是PL或100ms实时通过。
- Xilinx浮点FFT/compact协议：45帧RTL位准确/背压通过；整机100MHz WNS+0.283ns/WHS+0.040ns、17255LUT/29197FF/24.5BRAM36/69DSP，外部IO约束未完整。板端192次probe最坏relativeL2 5.617e-8，语音FFT-only误差1、组合3/2，零exp fallback。
- 逐FFT接口性能失败：Round11打包优化36次逐字节一致，combined2.621563/2.608862秒，仍未快于cache+exp2.602989/2.605818。FFT不默认启用。
- Round12同位流内核计时12次完整输出一致：male1 3279调用，copy_in28.288ms/device263.459ms/copy_out132.327ms；约31%内核成本为回读。因此改完整计算阶段融合。
- 静默定速p95约114ms，排除ALSA/codec/模拟/声学，不是物理延迟验收。尚无高实时/长期稳定性通过。

## 融合核当前实现

src/hls/world_minphase.cpp首个融合核：513点float log谱→镜像→两FFT→倒谱lifter→exp/cos/sin→513复数滤波器，中间留核内。固定1024点、10级每级512蝶形、twiddle ROM、明确级间LOOP_FLATTEN off；保留WORLD/Ooura c2c输入共轭约定。尚非完整合成/D4C。

host24例relativeL2最大8.5944e-7；完整两输入PCM16误差1/SNR97.268及96.811dB。HLS估算10007LUT/7732FF/4BRAM36/38DSP、30229拍@100MHz，非routed/实际DDR。exp目标II=1未完全满足，警告保留。Round15 RTL cosim未进入执行，Windows260字符导致float IP文件登记失败；不能写RTL数值通过。

Round16已用D:/wpl_20261027_r16/m短生成工程重跑。脚本支持WORLD_HLS_PROJECT，新probe拒绝已有目录防覆盖；源码留仓库。cosim使用24例和原WORLD common/fft/matlabfunctions。工具输出在build/generated/world_minphase_round16_{synth,cosim}.log。后续先读cosim结果，再决定Vivado MCP整机/板测；完整迁移需保留RandnState种子和消费顺序、160ms历史/40ms未来/anchor状态，普通STFT不能代替CheapTrick。

## 工具与复现

Vivado/Vitis2026.1在D:/USER_Software/vivado/2026.1；HLS入口Vitis/bin/vitis-run.bat --mode hls --tcl --input_file <tcl>。WorldRoot为根工作区build/generated/world_source_v035/pyworld-0.3.5/lib/World（生成物不随克隆）。build/build_world_exp.ps1 -Target host -CacheFftPlans -MinphaseModel构建host模型；build/check_world_minphase_quality.py复现完整语音。build/gen_world_minphase_twiddles.py重生ROM。

Vivado MCP通过tools/mcp_vivado.py，session vivado-20261027-171557-994ea2b1；原FFT项目build/generated/world_fft_20261027/voice7020.xpr。不要覆盖历史routed位流；候选compact SHA9a7a45027c087a43ce2a3809945317cd892725a2ac1f891ba3db92f61cfaeee9。

每轮独立commit/push/communication；推前pull --rebase origin main，python tools/check_collaboration_policy.py --base origin/main --head HEAD、git diff --check。生成RTL/二进制/音频/位流不入Git，小证据入report。下一责任方Hardware-A/Codex。

## 今日停止（用户明确要求）

Round16短路径综合与24例C-sim成功；Verilog编译/展开已越过长路径IP错误，但RTL仿真未完成。已按用户要求停止vitis-run/HLS/xelab进程，不能自动续跑。工具日志在report/world_minphase_round16_{synth,cosim}_20261027.txt，收尾报告world_minphase_round16_paused_20261027.md。下次用户要求继续时，从该短工程cosim恢复。当前板卡原v23正常运行。迁移提案已修正D4C 3kHz频带间隔、内部FFT尺寸及历史/未来/anchor上下文约束。
