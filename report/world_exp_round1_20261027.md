# PL-20261027-01：WORLD v23 复数 exp 集成首轮

用户在 2026-10-27 明确放弃 Deepseek，要求以已试听认可的 WORLD v23 做 PL 加速。板端二进制 SHA 已核对为 `f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7`。本轮不修改其他音色候选，不宣称目标身份或陌生多人通过。

## 实现

复用 10-22 的已修复 exp 核（原未提交工作保留在根工作区），新接 64-bit AXIS 和独立 AXI DMA/HP1；保留音频链 HP0、地址、中断及 I2C。PS 保留双精度 FFT；每次 513 bins 的 exp/cos/sin 卸载到 PL。实部/虚部输入24位 Q5.18，输出20位 Q2.17。PS 每帧减去最大实部，返回时乘 exp(max)，避免低能量谱因绝对量化精度损失而消失；超出数值域整帧回 CPU，并统计 fallback。显式 `WORLD_EXP=pl` 遇 DMA 错误立即终止，不悄悄伪装成 PL 成功。

新内核模块使用 `dma_alloc_coherent`，单次 ioctl 同步启动 simple-mode DMA，先收后发、校验状态和接收字节数；不复用未经证实的用户页物理连续性。模块只占用空闲 0x40400000，root-only，不修改 DT、启动分区或开机服务。正式 v23 的优化 synthesis 源和头文件从原构建目录提升到 `src/ps/world_v23/`，保留 WORLD 许可证与逐件 SHA；上游 pyworld 0.3.5 源通过明确参数提供。

## 本轮检查

- xsim 2026.1，seed=20261027，96×513 bins，随机背压，数值0 LSB、TLAST零错误，见 `world_exp_round1_xsim_20261027.txt`。
- 原受控男声标准录音1/4各前5秒，均值合单声道、polyphase重采样16k、PCM16；软件整数模型相对同一程序CPU路径 SNR 79.06/78.57 dB，最大PCM16误差3/2。原始音频与生成音频不入Git。完整SHA/日志/预处理见 `world_exp_round1_20261027.json`。
- ARM/host 程序与匹配 5.15.0-xilinx ABI 的内核模块编译成功。整机 Vivado 实现仍运行，尚无本轮 P&R 或板端加速结论。

## 复现

上游：`https://files.pythonhosted.org/packages/a5/0f/c78d631ffbb4c1aaebf80ff2bf9e791213b381dbe404f9ce1a3eb3672931/pyworld-0.3.5.tar.gz`，SHA256 `1b93e53cddb67a0e4faa34d6cf919ac6c662feb1c8c0ed901d71b595ab396aa3`，解压后的 `lib/World` 为下方 `$world`。依赖 Python numpy/scipy、MinGW g++、Vivado 2026.1 ARM g++、与板卡ABI相符的Linux源码/构建目录（原准备脚本 `build/prepare_kernel_sources.py`）。

```powershell
./build/build_world_exp.ps1 -WorldRoot $world -Target host
./build/build_world_exp.ps1 -WorldRoot $world -Target arm
python build/check_world_exp_quality.py --exe build/generated/world_exp_ps/world_exp_host.exe --source '人物音频资料/男声/标准录音 1.wav' --out build/generated/world_exp_ps/male1
python build/gen_world_exp_vectors.py --out build/generated/world_exp_vectors
# 在向量目录执行 xvlog --sv ../../../src/rtl/synth_offload/{minphase_exp_unit.v,minphase_rom_1024.v,tb_minphase_exp_unit.sv}
# xelab tb_minphase_exp_unit -s world_exp_sim; xsim world_exp_sim -runall
vivado -mode batch -source build/implement_world_exp_20261027.tcl
# WSL: sh build/build_world_exp_driver.sh <kernel-source> <matching-kernel-build>
```

## 下一步与限制

整机 P&R → 确认恢复位流 → 板端向量与 DMA 开销 → 同输入 v23/CPU/PL 文件输出与 RTF → 当轮准备确认后的现场音质与延迟回归。历史 CPU 分析来自电脑，62.7%仅用于挑选算子，不能当作 Cortex-A9 已测占比或速度承诺。完整端到端 p95≤100ms 和30分钟稳定性仍待实测；用户此前对 v23 的认可不替代目标音色门。
