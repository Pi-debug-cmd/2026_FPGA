# 2026-10-11 可调比例与独立DSP复位开发

> **最新结果：位流已生成并加载；16组黄金向量及非法参数/连续状态/独占open测试实板全部通过。原声、升调、降调各8秒试听脚本全部成功，三轮均零xrun；用户听感待回答。** 当前板上为控制版PL，音频流已停止；原厂监听PID549暂停，旧视频/GPIO等PL驱动解绑。后文构建中/原厂PL/新控制未实测描述为此前进度，以本段及末尾实板结果为准。

固定比例实测包 `build/generated/pl_bundle` 保留不变。新工程 `build/generated/audio_pitch_dma_control`，输入仍为A盘PS配置和音频引脚，新增AXI GPIO双输出控制，无新增外部引脚。地址0x41200000，18位比例和1位DSP_RUN；默认保持DSP复位。DMA、Formatter、Codec不受该局部复位控制。

代码：`build/create_audio_pitch_control.py`派生独立Tcl，`build/build_audio_pitch_control.tcl`综合至位流；寄存器/ioctl契约见 `team_project/pitch_control_contract.md`。`src/kernel/pitch_dma_proxy.c`兼容v1并新增v2配置、比例校验、配置后清零等待、未配置拒绝传输及独占open。DMA故障锁不因局部复位解除。`src/ps/pitch_dma_stream.c`增加可选第四参数ratio_q16，配置后才处理输入。新的驱动构建目录更新，旧固定包中的驱动副本保留原SHA。

## 已完成验证

- 新工程BD连接验证通过，0x41200000已分配，无位流加载。
- 变调核原六比例仿真24576样本全符，随机背压/TLAST/RAM和相位wrap/待输出复位检查通过；新GPIO控制路径仍需实板验证。
- 17项Python测试通过（`python_tests_verified_20261011.log`）。首次默认Anaconda沙箱运行3项临时文件权限错误，改用项目已验证Python运行时并获得环境访问后全通过，未修改测试逻辑。
- 匹配内核ABI的新版模块和ARM32工具编译通过；板上新版insmod/rmmod各0，无匹配设备和DMA流量。比例32767、131073在工具端拒绝返回2，合法86856无设备返回3。原厂PL operating保持不变。日志 `board_control_driver_abi_20261011.log`。
- 设备树v2已编译；生成16组双格式/比例/重复复位黄金结果并上传。`board/verify_dma_control.py`还验证非法配置中途拒绝后保持连续状态、独占open、非法块长和未知ioctl。**这些新硬件测试尚未执行。**

## 当前执行位置

Vivado位流构建运行中：`report/audio_pitch_control_build.log`，主机exec session60653。未修改SD启动文件。板上仍为10/11重启后的原厂PL；监听PID549运行，录放已停止；本轮没有暂停监听或解绑驱动。

暂存 `/tmp/codex_pl_control_20261011`：新版模块/可执行工具、DTO、切换/测试脚本与输入文件（黄金向量清单名 `vectors_manifest.json`，区别于将要上传的位流 `manifest.json`）。`board/load_pitch_candidate.py`采用本次实际监听PID，保存绑定/mixer及逐步状态；加载必须先检查校验包，且会解绑不再存在的旧PL消费者。完整恢复采取冷启动，不热绑定摄像头。

下一步：综合/实现通过并核对时序、DRC→`build/package_audio_pitch_control.py`独立打包→上传位流/清单→加载候选→数值16组与接口错误契约→原声/升调/降调试听→10分钟稳定性。新版包地址相同但控制能力不同，禁止与旧DTO/驱动随意混配。比例=1旁路依然有设备延迟和PCM16量化。

## 实现与实板结果

- 完整布局布线：8381 LUT、13286寄存器、5 BRAM、6 DSP；WNS +1.080ns、WHS +0.019ns，已约束路径满足要求，bus skew无VIOLATED。DRC零错误/critical，6个输入流水警告、1个无负载警告、2个BRAM advisory。仍有3输入/6输出缺少IO延时约束，不算完整外部IO时序签核。
- 独立包 `build/generated/pl_control_bundle/manifest.json`。原始交换位流4045564字节，SHA `c8e3e23e60a7c53ac0269ebb0bb210359b520aa5e75769ec54320cdbf293a517`；gzip338060字节，SHA `9379aa2dddb67cbc77c193c10ed2ad6153452b29c544de3673f05fc0ec49ae10`。压缩传输后板端解压核对原始长度和SHA，显著缩短串口传输。原固定包SHA全未改。
- 首次目录检查因 `/tmp` 为 `/var/volatile/tmp` 软链接提前失败，未操作硬件。路径边界已改为同时核对传入/tmp直接子目录及其真实父目录。
- 加载成功后声卡异步注册尚未完成，音量恢复失败，脚本停止在 `candidate_loaded`，未启动DMA。声卡随后注册正常；续接恢复mixer、insmod及DTO成功。源加载器已增加等待 `/dev/snd/controlC0` 最多10秒，完整修正版首次流程尚未从冷启动再跑一遍。
- `/tmp/codex_pl_control_20261011/verify_dma_control_v3.py` 实板执行：7比例×2格式，再重复86856×2，共16组各8195帧SHA全符；另验证中途非法比例不改变连续状态、比例边界/reserved、非法块长、独占open、未知ioctl。返回0。精简Python没有ctypes/py_compile，已改为array获取ARM32样本地址；array/fcntl/signal/subprocess等依赖核对可用。
- 三轮实时录放：65536原声、86856升调、52429降调，各8秒；所有脚本返回0、capture_overruns=0、playback_underruns=0、处理无报错。听感待回答，不冒充目标音色转换成功或端到端延迟测量。
- 日志：`board_control_pl_load_retry_20261011.log`、`board_control_golden_20261011.log`、`board_control_listen_suite_20261011.log`；实现报告前缀 `audio_pitch_control_`。

当前入口：板上控制版和DTO `codex_pitch_control` 保留，监听PID549停止，录放closed。状态保存 `/tmp/codex_pl_control_20261011/switch_state.json` 已更新为 `numeric_passed_listening_completed_await_feedback`，mixer快照同目录；最终快照日志 `board_control_final_state_20261011.log`，两个DMA中断各3544次。8秒三轮目录已存在，脚本拒绝覆盖；可使用新时长或新试验目录。不要再执行loader重复解绑/加载，已加载后测试直接使用工具第四参数配置/复位。10分钟稳定性、目标注册参数接入、定量延迟和完整冷启动复现仍待完成。全外设恢复采用冷启动，不热绑定摄像头。
