# WORLD v23 FFT计划复用 Round 5

基准bf748af。ARM诊断中5秒文件重复FFT建表约0.268s。本轮不改WORLD音色参数或FFT算术，只复用同一线程、同尺寸、同类型的空闲FFT计划和工作区；同时存活的计划各有独立槽，不跨线程共享。每线程最多32槽/4MiB，超限正常分配释放。默认构建不变，候选使用`-CacheFftPlans`；`WORLD_FFT_CACHE=0`可在同一二进制禁用。不得与`-ProfileOperators`同时启用。

开发中发现MinGW静态winpthread与C++ thread_local复杂析构组合在工作线程退出时读取已释放内存（gdb见0xfeeefeee，部分输入异常退出）；改用pthread_key的析构，并为主线程注册atexit清理。WSL AddressSanitizer未报告FFT数据越界，不能将其推断为ARM通过。修复后Windows两段受控男声、开关各5次，共20次正常退出，逐字节一致；机器记录见`world_fft_cache_host_round5_20261027.json`。

复现：`build/build_world_exp.ps1 -Target arm -CacheFftPlans -WorldRoot <WORLD0.3.5>`；候选SHA c15e8b0fdfabcd73f2d6c1aa04657df8b7b1206feb18d312802a5213f99a7dd9。板端`python3 world_fft_cache_trial.py --base /tmp/codex_world_cache_round5`，manifest校验全部文件，然后两输入各3轮交错运行原v23、缓存关、缓存开；输出必须与v23逐字节一致。只做静默文件，不加载新PL或打开ALSA；测后恢复v23。

本轮是FFT加速前的PS开销清理，不代替PL部署，也没有高实时验收结论。下一步根据板端耗时确定PL FFT精度/吞吐与接口预算。
