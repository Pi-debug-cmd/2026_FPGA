# Round14 固定循环融合核结果（待RTL验证）

任务PL-20261027-01，2026-10-27，实现bfb9327。24例host最坏relativeL2 8.5944e-7；完整两输入最大PCM16误差1，SNR97.268/96.811dB（原始JSON附后）。HLS估算9972LUT/7734FF/8 BRAM18K/38DSP，顶层29813拍（100MHz约298.13µs），比首版资源下降且有周期估计。

注意：报告显示工具把FFT级循环和蝶形循环flatten，源码inter false依赖声明需要防止跨级错误重叠；当前没有RTL cosim证据，不能称为RTL数值或板端加速通过。下一轮明确禁止跨级flatten，再进行24例C/RTL cosim。输出exp请求II=1实际未满足（流水资源约束）；保留原始报告不隐去警告。HLS估算并非整机routed签核/包含真实DDR延迟。

无新板测/现场录放，compact候选驻留、服务停止。
