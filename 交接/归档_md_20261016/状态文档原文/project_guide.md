# 项目查阅与继续开发指引

> **最新（2026-10-16，接手后首轮，离线）：** 只读审计 Seed-VC 参考（[脚本](build/audit_seed_reference_20261016.py)，无录音/播放/板卡/训练）。同一4.8秒窗内对目标Track5～8质心的身份余弦：源 0.114、WORLD旧配方 0.216、Seed30 0.551；对源泄漏余弦 WORLD 0.383 vs Seed30 0.021；目标四轨自身两两 0.911。UTMOS 预测自然度：WORLD 2.095、Seed30 2.736、目标轨 2.99～3.34。whisper-small 相对源句字错：WORLD 7/18、Seed30 2/18。方向与用户 10-15 听感一致，但仍未达目标音色。**7020 可行性：约 363M 参数（DiT 35.5M＋声码器 20.5M＋campplus 7M＋xls-r-300m 300M），FP32 约 1.45GB＞本板 1GB DDR，30 步顺序扩散，主机 CPU RTF≈2.60 → 不能直接上板，只能作离线教师/上限参考与“只注册目标”接口的设计依据。** 详见 [离线审计报告](report/seed_reference_audit_20261016.json)。

> **当前进展（2026-10-15，用户休息，已暂停）：** Seed-VC 30步电脑离线参考已试听：用户确认低沉沙哑减少、清晰度明显提高，但仍有AI感，与目标有差距；目标音色尚未验收。播放零underrun、mixer恢复成功、录放closed。该模型CPU推理RTF约2.60，尚不能在7020板上实时运行。下次先分析自然度、目标相似度及板端实现可行性，再决定方案；多人、新句和内容完整性仍需验证。每轮现场测试重新确认准备，大小声适应专项仍后置。见 [听感记录](report/seed_reference_feedback_20261015.json)。

> **最新听感（2026-10-15）：** 旧配方音色/清晰度最佳，按人完整候选音高更像但略不清晰，按人仅音高发闷。已生成“旧频谱处理＋按人音高映射”组合候选，零削顶、试听待确认。原样本现作开发对照，最终需新句与其他输入者验证；未证明多人目标音色或实时接入。见 [听感记录](report/prepared_world_listening_speaker01_20261015.json)。

> **最新留出句验证（2026-10-15）：** speaker01另录20秒新句，904有声帧、无采集溢出/触顶、恢复0、PCMclosed。冻结准备配置SHA不变，旧配方/按人音高/按人音色三组离线输出完整且零削顶；24秒对照已生成，目标相似度和实时接入尚未验收。下一步单独确认后试听。证据 [留出句报告](report/prepared_world_holdout_speaker01_20261015.json)。

> **最新实测（2026-10-15）：** 两声提示音已单独试听确认可听；随后20秒准备录音835有声帧、无采集溢出/触顶，恢复0、PCMclosed。已生成speaker01实验转换配置，尚未做后续新句转换/试听或实时C++接入，不能称目标音色通过。下一步另取准备确认录留出新句。证据 [准备录音结果](report/source_preparation_speaker01_cue_v2_20261015.json)。

> **当前执行方案（2026-10-15，用户已确认并要求开始）：** 陌生输入者先录准备音频，算法生成转换配置，加载后启动实时变声。准备音频不作为正式输出，换人重新准备；后续新句单独评价音色，不能只验证升调。配置生成入口与9项主机检查已通过，尚未真人准备录音或接入实时C++。下文“免录入”和自动首句缓存属于已被本方案覆盖的历史。见 [实现与下一步](report/prepared_conversion_20261015.md)。

> **最新候选思路（2026-10-15）：** 用户提出陌生输入者本次先录入分析、算出转换参数，再开始输出。纳入自动起始分析候选；输入者无需已有源档案。初始等待、缓存首句如何输出和换人重估需单独验证，尚未选定时长或证明目标音色效果。此候选允许当次先分析，补充下方较早的免校准表述，不恢复此前20秒录音安排。见 [思路与验证边界](report/automatic_start_analysis_20261015.md)。

> **当前权威要求（2026-10-15）：只注册目标，任何未录入、未校准的输入者直接讲话即可转换。** 不得要求源档案、选择输入者或预读校准句。此前按人校准路线不满足要求，仅留作对照；源校准录音安排取消。优先验证未见源说话人的音色转换与目标注册能力，再优化有效算法的板端性能。下方允许源校准的旧规划已被覆盖。详见 [需求修正](report/source_uncalibrated_requirement_20261015.md)。

> **2026-10-15 已恢复：** 优先多输入者到同一目标。按人log-F0与谱包络离线候选已生成，5项数值检查通过；目前仅一位历史输入者的分段检查，多人身份相似度未验收。下一步按身份分开采集校准句与留出句，每轮录放另问准备。大小声适应后置。详见 [今日交接](handoff_20261015.md)。下列10月14日暂停为历史记录。

> **已暂停（2026-10-14）：** 已暂停（2026-10-14用户休息）：当前WORLD实时变声稳定性/延迟优化阶段。200ms有效60秒及20秒零欠载/削顶、听感自然；3分钟零欠载但2个输入触顶；v22/200ms十分钟1次播放欠载（至少0.204ms）、13个输入触顶及221个输出削顶，用户自然连续无异常，日志门槛仍未通过。输入触顶约18.862～384.099秒，非纯启动瞬态；按约定不先调增益。mixer恢复0、PCMclosed。下次继续核心调度/计算余量与启停可靠性，大小声适应专项最后处理。 先读 [今天交接](handoff_20261014.md)，证据见 [开发记录](report/world_stream_development_20261014.md)。

> 核心要求补充（2026-10-14）：多个不同输入者均须转换得接近同一已注册目标声线。用户今天反馈其他人试说时相似度不足、像统一升调；现有固定基频倍率/谱包络变形未实现按输入者校准的映射，多输入者目标相似度未通过。恢复后优先验证源校准、源到目标映射和跨输入者留出句，不能以自然连续或固定倍率代替目标相似度。大小声适应仍最后处理；本次仅保存需求，今天继续暂停，不启动板卡或构建。 详见 [需求与验收修正](report/multi_input_requirement_20261014.md)。

> **现场规则（恢复后适用）：** 需要用户讲话/录音/试听时，必须先取得本轮明确准备确认。用户授权其它开发及无需其配合的文件/只读验证自主继续。2026-10-13七次现场录放均先获准备确认；最后历史现场目录 `/tmp/codex_world_20261013/live_8468102955132`，重启后不可沿用暂存或状态。禁止摄像头热绑定恢复，启动分区未改。

> 双核文件调度的40ms/180ms门槛通过仅是历史文件证据，不能替代上述真实录放失败项。[双核调度报告](report/world_dual_development_20261013.md)、[真实录放报告](report/world_live_development_20261013.md)。

## 当前决定：不重复询问

- 题目：可注册目标声线实时变声器，首期单目标、多个不同输入者转换到同一目标；陌生输入者先录准备语音生成配置，再启动实时转换，以后续留出句实测目标相似度。基础变调保底，多目标后续再做。
- 截止：2026-11-06；由Codex全盘接手，不等待人员分配。用户要求连续推进，直到必须由其验证或有影响实现的未知条件再询问/停止。
- 平台：野火Zynq-7020，优先本板适配PYNQ，Vivado 2018.3。用户2026-10-10明确以A盘厂商资料为准，板级器件采用 `xc7z020clg400-2`，硬件引脚/DDR依据同盘原理图与工程；不再等待丝印确认。已有-1独立综合保持历史证据，不改写成-2结果。
- 音频：外接3.5mm麦克风→粉色J12，音响→绿色J13；板载咪头不用，WM8960 ADC/DAC仍使用。
- 交接是参考，不自动改变上述范围。历史Linux/C/GEMM模型没有证明现场新目标注册或PYNQ已运行。
- 原AGENTS.md指定的另一个code_rule.md路径不存在，实际编码规范读工作区根目录副本。用户新指令优先于旧三人分工文档。

## 最短查阅顺序

1. [当前状态](team_project/project_status.md)：本会话真正验证的成果和待办。
2. [总计划](plan.md)：日期、G1～G7和停止新增功能的节点。
3. 按工作选读：算法/RTL读 `src/`、`sim/` 和 [接口草案](team_project/interface_draft.md)；音频读 [硬件核查](board/hardware_inventory.md)；复用队友成果读 [交接审阅](team_project/handoff_review.md)。
4. 需要原始证据时再打开总结里的指定日志，不把历史摘要直接当当前实测。
5. 每轮结束更新状态与 [AI记录](report/ai_worklog.md)，并在本文件末尾更新当前开发位置。

## 位置与可运行入口

| 用途 | 路径/入口 |
| --- | --- |
| 工作区 | `C:/Users/World/Desktop/2026_FPGA` |
| 厂商资料，只读 | `D:/BaiduNetdiskDownload/A盘（资料盘）` |
| Vivado/SDK | `D:/USER_Software/Xilinx_Vivado/Vivado/2018.3`、同安装根目录 `SDK/2018.3` |
| 已用Python | `C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`，3.12，NumPy 2.3.5 |
| 浮点变调参考 | `src/reference/pitch_shift.py`，PCM16单声道WAV，固定ratio |
| 整数与F0参考 | `src/reference/pitch_shift_fixed.py`、`voice_profile.py`；[定点契约](team_project/fixed_point_contract.md) |
| Python验证 | 根目录执行 `python -m unittest discover -s sim -v` |
| AXI旁路RTL | `src/rtl/axis_audio_bypass.v`，测试台 `sim/tb_axis_audio_bypass.v` |
| 旁路仿真 | `build/run_bypass_sim.ps1`，输出 `report/axis_bypass_sim.txt` |
| 独立综合 | `build/synth_bypass.tcl`，仅模块，不生成完整板级位流 |
| 变调核仿真/综合 | `build/run_pitch_sim.ps1`、`build/synth_pitch.tcl` |
| PS程序编译/验证 | `build/build_ps_reference.ps1`、`sim/verify_ps_board_log.py`；实测12组SHA全符 |
| 麦克风试听接续 | [板端测试说明](board/pitch_trial.md)，当前等待用户短时听辨 |
| 交接原件，只读 | `交接/工程总交接_20261009.md`、`交接/核心材料/` |
| 交接全量文件核验 | `report/handoff_file_check.json`，8399文件大小/SHA全符，非重新板测 |

Windows沙箱内Vivado批处理可能无法切换到安装目录；本会话已通过自动审查允许在工作区启动厂商脚本，安装文件未修改。常规Python使用附带运行时，不默认安装新环境。生成文件放 `build/generated/` 或 `tmp/`，正式证据放 `report/`，不往资料盘写输出。

## 队友历史版本：按SHA而非文件名识别

路径以 `交接/核心材料/` 为根，完整SHA见交接审阅总结。

- 通过历史音频/GEMM测试的位流：`g_build/proj/zynq_gemm_irq_swap.bin`，SHA前缀 `721a788816aa`。
- v2模型：`board_budget_20261005/llvc_deploy_model_reduced.bin`，头版本2，SHA前缀 `4e635452493b`。
- 融合程序实际包名：`deploy_runtime/kv_fuse_candidate_20261009/deploy_kv_fused_20261009`，板端历史名 `deploy_kv_fused`。
- 历史500ms脚本：`board_native32_live_500ms_backup.sh`，SHA前缀 `e6779db674d1`；包内同目录 `board_native32_live.sh` 是150ms失败试验，不能按同名直接上传。
- 偏置候选：要求头版本3，包内没有成功导出的 `model_bias.bin`；未通过编译、数值、速度和真人验证。不要与v2程序混搭。
- 交接里的“四名留出说话人”实为同一SSB0434的四段音频；完整验证集8对/2人，不作为四人泛化结论。

## 音频与板端注意事项

- 原理图：外接MIC走WM8960左输入。队友历史设备树却靠右输入路由维持MICB供电；后续必须查当前DAPM，不因为不用板载咪头就关掉所有右输入。
- 历史ALSA为32kHz S24_LE双声道，模型为16kHz单声道浮点。我们的PCM16/32位AXI草案是另一份格式契约；明确转换，不能直接替换。
- 用户已确认COM14、115200，本会话已实际连接，内核5.15.0-xilinx与WM8960声卡可见。COM9是历史端口，不再默认使用。板端时间与PC不同，用PC日志时间和SHA追踪。
- 88号历史快照有483次overrun、396次underrun；不能因五进程存活称长期实时通过。其运行状态、PID、累计值都不是当前事实。
- 不运行原交接构建脚本（会删D:/g_build/proj）或打包脚本，不重烧SD/重启/全局kill；需要复用时复制到独立工作目录并修路径、核版本。

## 当前开发位置

- 已验证：Python17项测试；旁路仿真；变调RTL24576样本完全一致；变调独立综合340 LUT/117寄存器/1 BRAM/6 DSP，100MHz综合估计WNS+4.311ns。详见 [本轮开发证据](report/pitch_development.md)。
- COM14：当前厂商Linux已确认，旧神经链路未运行；本项目PS-only程序已上传/tmp并完成PCM16/S24_LE共12组板端数值验证，不曾加载新的PL位流。
- 当前进展：用户确认同一音响/线缆接电脑正常。厂商音乐、同源44.1kHz/32kHz音乐均可听；在同一连续流里，音乐/原录音/音乐/变调录音均可听，音调确实提高。录音临时放大8倍，无削波；不算正式音质验收。先读 [本日实测记录](report/live_audio_20261010.md)。
- 当前脚本v4：保存/恢复mixer，保留左右输入MICBIAS路由、左ADC复制；采用厂商default（plug/mmap_emul）播放路径、Headphone ZC开启、Headphone105/Playback230；模拟LINPUT1 boost临时设1。播放period4000/buffer16000（32kHz），先验证声音再降延迟。板端入口 `/tmp/codex_live_pitch_trial_v4.sh`，已有测试目录不覆盖；第一次20秒零xrun但用户未准备，不能当听辨通过。此前v3及小缓冲配置不是已通过基线；无声根因尚未唯一定位。
- 核心目标仍未完成：PL完整音频/DMA接入、现场注册闭环、清音/抗混叠与音色逼近、长期稳定性、端到端延迟、独立多人评价。硬件规格按用户指定A盘资料执行。
- v4 repeat听辨已确认：能听到讲话、音调升高，但延迟明显。20秒零xrun，录放closed、原音量恢复；日志 `report/board_live_pitch_v4_repeat_20261010.log` 和 `report/board_live_v4_repeat_state_20261010.log`。尚未验收音质、长期稳定性或实际端到端延迟。
- 当前可听基线v5：`board/live_pitch_low_latency_trial.sh` / 板端 `/tmp/codex_live_pitch_trial_v5.sh`，保留v4路由与增益，播放period512/buffer3072/start-delay32000μs。20秒用户确认延迟明显减轻、持续可听、无明显断续/杂音/颤动，零xrun；额外60秒连续检查亦零xrun。实际采集/播放均period512/buffer3072，播放起播阈值1024帧。测试均结束、原音量恢复，端到端延迟尚未定量测量，非长期稳定性验收。原v4保留作回退。
- 开发已转向PL：旧默认PS原型 `build/generated/pitch_dma_prototype_v2/` 仅作连接验证。A盘核对 `report/vendor_audio_audit.json`：交接531项PS参数全同、抽取24条音频/I2C约束；新入口 `build/prepare_vendor_audio.py` → `build/create_audio_pitch_dma.tcl`，厂商输入放 `board/vendor_inputs/`。按 [PL接入约束](team_project/pl_integration.md) 继续本板音频＋HP1独立变调DMA、驱动和实现验证；运行中设备树核对日志 `report/board_platform_inventory_20261010.log`。当前系统还有视频等PL驱动，精简工程不可直接替换运行中PL。
- 本板候选已构建：`build/generated/pl_bundle/manifest.json`，-2器件、固定Q16=86856、DMA 0x40400000、F2P位12/13（避开已占用0/1）；布局布线8302 LUT/13179寄存器/5 BRAM/6 DSP，WNS+2.160ns/WHS+0.017ns。外部IO延时3输入/6输出未约束，非完整音频IO签核。详见 [本轮板级构建](report/pl_board_build_20261010.md)。候选尚未加载，G1未通过。
- 内核环境：已用A盘源码和板端配置在Ubuntu20.04 WSL `/var/tmp/2026_fpga_kernel_20261010` 重建5.15.0-xilinx及非空Module.symvers，索引 `build/generated/kernel_abi_v2/`。不要再用/tmp保存WSL长期构建。DMA新客户端加载/仅注册/卸载均0，工具能运行；没有启动DMA。入口 `build/build_pitch_dma_driver.sh`、`src/kernel/`、`src/ps/pitch_dma_stream.c`。模块故障锁定后要求PL恢复，原型无独立DSP复位/改比例。
- 板测准备：原厂 `/boot/bit/zynq7020.bit` 已核SHA并转换回退镜像到 `/tmp/codex_pl_trial_20261010/factory_restore_swap.bin`，尚未验证实际恢复。候选字节交换镜像正上传同目录，期间COM14独占；读传输日志 `report/upload_audio_pitch_dma_bitstream_20261010.log`。下一步上传/执行只读 `board/pl_switch_preflight.py`，检查GPIO消费者、音频按键进程及PL依赖，再编制切换/回退流程。PCM32黄金向量 `data/diagnostics/dma_vectors/` 已准备，8195样本、257帧块、初态须新PL复位。


2026-10-13已恢复并完成双核文件调度初测：40ms滑窗连续60秒，160ms模拟输出预算出现741/7500块晚到、最大8.03ms；单独确认准备后180ms预算零晚到、最小余量12.50ms。两轮均1502块全部消费、FIFO峰值2/8、参数存活3/16、CPU0/1绑定成功，ARM输出SHA与主机一致。13项本地检查通过。当前原厂PL、无DMA、录放closed；未播放或修改mixer。180ms不是实测端到端延迟，原p95≤100ms目标未通过。下一步实现真实I/O的有界缓存和退出恢复，再单独询问现场测试准备状态。详见report/world_dual_development_20261013.md。


2026-10-13用户要求休息，已停止板端操作、编译和测试，仅保存本地交接。WORLD真实录放已可听自然，v16/200ms和240ms各20秒零xrun/削波；180ms一次欠载并可闻短断音。v17/200ms/60秒音量自然度正常、用户未察觉断音，输入/输出零饱和，但日志2次播放欠载，不能称稳定通过。v18 FIFO候选已通过主机/ARM文件与退出验证，60秒现场测试未执行。用户新增优先级：适应不同说话音量并保持不失真和音质，列入基本功能完成后的最终调优/验收，现阶段不反复围绕大小声调整增益。下次先读handoff_20261013.md和project_guide.md，收到恢复请求后继续；需要用户现场测试时另问准备状态。




## 录音起始提示规则（用户2026-10-15新增）

用户要求先有一段提示音再开始录音。以后每轮准备确认须说明音响绿色口已连接并开启，先播放300ms短提示音，播放完成并留150ms间隔后才打开采集；提示音不并入准备录音。每轮实际录放仍先确认准备。board/capture_source_mapping.py已增加该流程和播放失败拒绝启动采集，保存恢复mixer覆盖提示音与录音全过程；尚未执行带提示音的现场测试，不自动重录。

本日首次无提示音20秒准备录音已结束：目录/tmp/codex_source_mapping_20261015/speaker01_calibration_925022275789，采集退出0、录音完整、无overrun及原始触顶，恢复0、录放closed。日志report/source_capture_speaker01_20261015.log。WAV SHA8313d6622dac0a52107ab6df5e34865500987b4de60be4baeb4084665ecac594；gzip SHA943132244e09fdf82e95d482cf30a32ecbe934b424bb6d64f42d1c9a4a6d0059。有效讲话与配置生成尚待下载后的分析，不因采集退出0就判准备语音可用。
