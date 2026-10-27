# WORLD v23 ARM 算子剖析 Round 4

- 日期：2026-10-27；任务 PL-20261027-01；实现提交 fccd97b。
- 原厂 PL，音频服务暂时停止；只跑静默文件，没有录放或听感结论。
- 同一受控男声1前5秒、16k PCM16，参数 `5 pcm16 0 39322`，`WORLD_EXP=cpu`；baseline一次，剖析三次。二进制和输入 SHA 见同名 JSON manifest。
- 三次剖析80000输出样本均与板上原v23逐字节相同。基线墙钟 2.833727s，剖析中位 2.883378s，插桩扰动约 1.75%；单次baseline不能证明此百分比全由插桩导致。

| 阶段 | FFT建表秒 | FFT执行秒 |
| --- | ---: | ---: |
| render/other | 0.000491 | 0.654678 |
| dio | 0.185305 | 0.280401 |
| refine | 0.026538 | 0.063993 |
| spectrum | 0.016908 | 0.130775 |
| aperiodic | 0.039251 | 0.324211 |

执行累计1.454058s，建表0.268492s，为双核线程累计，不能直接除以整链墙钟当成加速比。最大单项是D4C 2048 r2c执行0.324211s/1827次；合成1024三种FFT累计0.654678s。分析仍决定静默文件关键路径。

结论：接受本轮计时与数值诊断；不宣称高实时性通过。下一步先复用同尺寸的建表结果（保持double FFT不变），再为2048/1024 FFT评估PL数值精度、DMA和真实收益。先前18bit FFT不满足log谱要求，不能直接接入。

复现：`build/build_world_exp.ps1 -Target arm -ProfileOperators -WorldRoot <WORLD0.3.5>`，按脚本生成manifest并上传，板上 `python3 world_operator_profile_trial.py --base /tmp/codex_world_profile_round4`。板上Python缺少statistics，本轮runner使用三个结果排序取中值，不新增板端依赖。原始计时行完整保留在同名JSON。
