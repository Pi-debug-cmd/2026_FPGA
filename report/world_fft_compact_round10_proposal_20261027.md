# WORLD v23 实输入FFT紧凑协议 Round 10

任务PL-20261027-01，基准098f57b。Round9全复数DMA正确但比计划复用CPU慢。本轮只改变r2c格式，FFT核参数、时钟、帧批次和声学算法不变。

- 配置头bit9为compact real，bit8仍为forward，低5位长度；头进入IP前清bit9，不污染原IP scaling字段。
- r2c TX由N个复数缩为N个float（每64bit两实样本），PL保持AXI上游数据直到两个实样本都被FFT接收；每个样本扩展零虚部。
- RX只返回前N/2+1复数，最后有效bin给DMA TLAST；PL继续接收丢弃内部共轭后半谱，直到IP真实TLAST才接受下一头，避免污染。
- complex/c2r完整模式保持；ioctl request.forward bit1表示compact（仅允许3），输入N*4字节、输出(N/2+1)*8字节。PS使用memcpy避免uint64工作区float别名未定义行为。
- probe增加compact real r2c，保留复数正反向，与原WORLD double比较；共192次，SHA见build JSON。
- 仿真保留30帧旧格式，再追加15帧compact，包含1024/2048切换、零/脉冲/常量/随机/弱信号和背压；全部输出float必须与同配置官方C模型逐位一致。新的mem由quality checker --vectors-only生成。

ARM和匹配kernel module已编译；RTL仿真与增量整机综合进行中。旧位流与routed checkpoint复制到忽略目录world_fft_round9_archive保存，报告中的SHA不变。复现仍用完整build/implement_world_exp_20261027.tcl -tclargs fft，在干净生成目录从本轮源码构建；本机仅增量重跑包装/OOC与整机，复用未变IP。

Round9恢复补充：world_exp_switch.py --restore --keep-stopped 已成功恢复原厂PL并只重绑audio/I2C，两个自有DMA module先卸载；显示/相机推迟正常启动，避免之前死锁。原始恢复日志随本轮提交。当前原厂operating，服务暂时停止用于后续静默传输；无新录放。

本轮尚无紧凑协议RTL/板端性能结论；必须先过仿真、整机时序与数值门，再与相同输入的cache+exp基线比较。物理延迟和稳定性未验收。
