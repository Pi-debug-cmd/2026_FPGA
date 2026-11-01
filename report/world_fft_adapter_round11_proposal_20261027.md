# Round 11 PS浮点适配开销优化方案

任务 PL-20261027-01，2026-10-27，源基准 6193bc8。保留compact FFT位流 SHA 9a7a45027c087a43ce2a3809945317cd892725a2ac1f891ba3db92f61cfaeee9。

ARM反汇编显示逐bin std::isfinite产生VFP abs/compare/vmrs同步；改为float32指数位检查，累积后在DMA前及解包后拒绝Inf/NaN，有限值转换/顺序不变。实输入单独循环，省略无用虚部构造和条件。

构建：`build/build_world_exp.ps1 -Target arm -CacheFftPlans -FftPl -WorldRoot <pyworld-0.3.5/lib/World>`，使用既有GCC13.4 Cortex-A9工具链，上游路径见Round1报告。

ARM静态程序 SHA256 2b9d98466955262f68462e78256fb5f8e192bc9fecb265d666f3910e80807d65。编译通过；旧新程序保留不同文件名，禁止覆盖Round10基准。

板测入口：`python3 world_fft_adapter_trial.py --base /tmp/codex_world_fft_round10 --old /tmp/codex_world_fft_round10/world_exp_arm_cache_fftpl --new /tmp/codex_world_fft_round10/adapter_round11 --output /tmp/codex_world_fft_round10/adapter_round11_result.json`。两输入各5秒，CPU/exp_only/combined三模式，旧新交错三遍，共36次。每次要求与Round10同模式输出逐字节相同，exp无fallback，记录完整计时和二进制SHA。

这是方案而非性能结论。无ALSA、无现场录放。性能若仍退步不将FFT设默认。
