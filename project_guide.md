# 项目查阅与继续开发指引

**项目技术入口文档。**所有 Agent 必须先读 `AGENTS.md`，再读本文件、最新 `handoff_*.md` 和 `coummucation.md`。历史进展（2026-10-09 ～ 10-15 的逐日状态块）已从本文件移出，保留在 [每日交接](交接/归档_md_20261016/handoff) 与 [协作记录](report/ai_worklog.md)；整理前的原文备份在 [状态文档原文](交接/归档_md_20261016/状态文档原文)。

## 最新状态（2026-10-21）

- 当前优先级是第一级保底方案：固定两名输入者转换到既定女声 WAV。两人专用软件音色、Cortex-A9 文件、试听、PL 部署与音质回归、实时性和稳定性全部通过后，才进入陌生多人进阶方案；最后再做板上现场注册目标的最终方案。
- `LLVC content → FARGAN v1` 已完成并客观拒绝：身份 0.656、泄漏 0.065，但 UTMOS 1.660、CER 0.582，不安排试听。见 `report/quality_exploration_ps_round_20261019.md`。
- Seed-VC V2 历史上已被用户明确判定退步，不再恢复为主线。
- 下一任务是 `PS-20261021-10`：先冻结两名固定输入者资产和说话人隔离切分，再建立两人分别可验收的固定女声质量上限；详细门槛见 `plan.md` 和 `coummucation.md`。
- GitHub 协作采用强制轮次提交：每完成一轮方案或一轮测试，必须更新 `coummucation.md`、提交并推送；失败轮次同样提交。
- 当前共三个写作者：已经提交的两位都有板卡和 Vivado，可共同承担板测与 PL；尚未加入的第三位没有板卡和 Vivado，只负责电脑端/PS 方案、客观评测和部署预算，再交硬件方验证。

## 历史状态（2026-10-16）

> **接手后首轮，离线：** 只读审计 Seed-VC 参考（[脚本](build/audit_seed_reference_20261016.py)，无录音/播放/板卡/训练）。同一 4.8 秒窗内对目标 Track5～8 质心的身份余弦：源 0.114、WORLD 旧配方 0.216、Seed30 0.551；对源泄漏余弦 WORLD 0.383 vs Seed30 0.021；目标四轨自身两两 0.911。UTMOS 预测自然度：WORLD 2.095、Seed30 2.736、目标轨 2.99～3.34。whisper-small 相对源句字错：WORLD 7/18、Seed30 2/18。方向与用户 10-15 听感一致，仍未达目标音色。**7020 可行性：约 363M 参数、FP32 约 1.45GB＞本板 1GB DDR，30 步顺序扩散，主机 CPU RTF≈2.60 → 不能直接上板，只能作离线教师/上限参考。** 证据 [离线审计](report/seed_reference_audit_20261016.json)。

> **上一轮：** Seed-VC 30 步电脑离线参考已试听：用户确认低沉沙哑减少、清晰度明显提高，但仍有 AI 感、与目标有差距；目标音色未验收。见 [听感记录](report/seed_reference_feedback_20261015.json)。

## 现行硬约束（2026-10-16 用户确认，优先于下方历史描述）

> **2026-10-21 执行顺序更新：**最终产品的全脱机现场注册要求不变，但研发改为三级门控：①固定两名输入者到既定女声 WAV 的保底方案；②陌生多人到同一固定女声的进阶方案；③板上现场注册新目标的最终方案。每一级完成软件音色、PS 文件、试听、PL 部署、音质回归、实时与稳定性闭环后才进入下一级。详细定义以根目录 `plan.md` 为准。

1. **全脱机/裸机**：比赛演示不接电脑、板上自足。准备阶段（现场注册目标声源 + 板上构建音色转化模型）与实时转换阶段**都在板上完成**，不依赖 PC/GPU/云。板上资源可自由使用：DDR 1GB，PL 现用 8302 LUT / 13179 FF / 5 BRAM / 6 DSP，可用约 53200 LUT / 140 BRAM / 220 DSP。详见 [需求记录](report/onboard_standalone_requirement_20261016.md)。
2. **目标音色来源**：演示现场在板上录目标人几句话，当场建模；不是把 PC 生成好的配置拷进板子。
3. **输入者免录入、免校准**：只注册目标，任何未录入的陌生说话人直接讲话转换；不得要求源档案或预读校准句。详见 [权威需求修正](report/source_uncalibrated_requirement_20261015.md)。
4. **多输入者到同一目标**：多个不同输入者都要接近同一目标声线；固定倍率变调不算实现。见 [需求记录](report/multi_input_requirement_20261014.md)。
5. **大小声适应**放在基本功能完成后的最终调优，现阶段不反复调增益。
6. **现场纪律**：每轮实际录音/播放/试听**必须先取得当轮明确准备确认**，授权不复用。录音先播 300ms 提示音、留 150ms 间隔再开采集，提示音不并入录音。
7. **禁止**：切 PL、改启动分区、重烧 SD、碰物理磁盘 0、重跑会删 `D:\g_build\proj` 的厂商构建脚本、沿用旧 `/tmp` 或旧状态快照。需要用户停板时先在串口执行板上脚本 stop，再让用户断电。

## 当前技术判断（2026-10-16）

- **身份相似度是核心难点**：现役 WORLD 旧配方对目标余弦 0.216、对源泄漏 0.383，而目标自身两两 0.911。延迟与稳定性排在它之后。
- **纯参数化路线已实测触顶**：用同一四项指标审计已有参数化候选（[报告](report/param_candidate_audit_20261016.json)），全部卡在 **0.19～0.22**：按人仅音高 0.064、按人谱包络 0.187、旧谱变形+按人音高 0.200、低频架 0.199、谱平衡 0.222，源泄漏 0.37～0.63；同期 Seed-VC 为 0.551/0.021。**结论：演示现场只能拟合几个统计量的做法够不到门槛**，决定音色的映射必须在开发期从数据学出来。
- **PS 单干不够实时，且瓶颈是合成而非分析（2026-10-17 实测）**：板上 `world_budget` 分阶段计时（5 秒片段、单线程、GCC 13.4）连续语音 RTF：pitch 0.033、refine 0.020、envelope 0.107、ap 0.197、warp 0.015、**synthesis 0.550**，总 **0.816**（余量 18.4%）；真实带停顿组总 0.680。**合成占 67.4%**、AP 24.2%、包络 13.1%、基频 6.4%。因此 PL 卸载第一位是**合成**（卸载后 PS 约 0.27 RTF），第二位 D4C。详见 [实时预算与 PL 方案](report/world_realtime_plan_20261017.md)。旧结论"5 秒语音用 5.003886 秒"是 2018.3／GCC 7.3 时代数字，编译器换代后不可直接比较。
- **Vivado 已统一为 2026.1**：本机使用 `D:\USER_Software\vivado\2026.1`（含 GCC 13.4 交叉编译器）。音频链已在 2026.1 下从零重建并完成综合、实现和位流生成；2026.1 报告是当前基准，2018.3 报告只作历史对照。详见 `report/pl_vivado_20261_migration.md`。
- **注册链路（任务 A）第一步已通过**：`src/ps/world_register.cpp` 复用 WORLD 0.3.5 同一份 C++ 核，出目标画像（F0 分布、频带谱比例、AP 均值、平均谱）与质量门槛；宿主一致性 vs pyworld **ALL PASS**（最大差 ≤4.6e-7），拒绝路径返回 3/5 正确（[宿主证据](report/world_register_parity_20261016.json)）。**ARM 静态二进制已在板上跑通**：COM14／PetaLinux 2022.2／内核 5.15.0-xilinx，两条正样本画像与宿主逐项数值完全相同（含 513 点平均谱，差异 0.0，仅 CRLF/LF 不同），两条负样本返回 3/5（[板端证据](report/world_register_board_20261016.json)）。仍未验证：现场注册录音、换人重注册与回退、板上建模后立刻转换的闭环。
- **板上闭环已走通（2026-10-17）**：`world_register`（目标画像）→ `world_convert`（文件回放转换）都在板上跑通：20 秒音频 → **20.165 秒（RTF≈1.008，尚不实时）**，峰值 0.3667、零削顶；ARM 与宿主输出**相关 1.000000、频谱偏差 0.000 dB**（[证据](report/world_convert_board_20261017.json)）。闭环产物四项指标：身份 0.190、源泄漏 **0.172**、UTMOS 2.035、字错 **0.167**；相对旧配方（0.216／0.383／2.095／0.389）**泄漏与内容明显改善，身份没上去**，与 10-16 判决性结论一致。转换映射为逐频点 ±3dB 钳位版本（无 24 阶倒谱平滑），不是历史配方复现。
- **未验收**：目标音色、多人泛化、内容完整性、现场注册闭环、端到端延迟（p95≤100ms）、长期稳定性、PYNQ。板上闭环仍是文件回放，不是实时链路；注册画像来自已有录音切片，不是现场注册。

## 最短查阅顺序

1. [接手状态与已完成清单](team_project/project_status.md)：已真正验证的成果、待办、信息缺口。
2. [总计划](plan.md)：目标、日历与 G1～G7 门槛、技术顺序、风险决策。
3. 按工作选读：算法/RTL 读 `src/`、`sim/`、[接口草案](team_project/interface_draft.md)；音频/板卡读 [硬件核查](board/hardware_inventory.md)、[实时测试说明](board/world_live_trial.md)；契约读 [定点契约](team_project/fixed_point_contract.md)、[PL 接入](team_project/pl_integration.md)；复用队友成果读 [交接审阅](team_project/handoff_review.md)。
4. 需要原始证据时按总结里的链接打开 `report/` 下的日志与 JSON，不把历史摘要当当前实测。
5. 每轮结束先更新 `coummucation.md`，再更新 `team_project/project_status.md` 与 [协作记录](report/ai_worklog.md)，提交并推送 GitHub。

## 位置与可运行入口

| 用途 | 路径/入口 |
| --- | --- |
| 工作区 | `C:/Users/World/Desktop/2026_FPGA` |
| 厂商资料，只读 | `D:/BaiduNetdiskDownload/A盘（资料盘）` |
| Vivado/交叉编译器 | `D:/USER_Software/vivado/2026.1`；ARM GCC 位于其 `gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/` |
| 板级器件 | `xc7z020clg400-2`（用户指定以 A 盘资料为准） |
| Python | 系统 `python` 为 Anaconda 3.13.9（NumPy 2.3.5）；本项目隔离依赖为 cp312，用 `C:/Users/World/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`（3.12.14） |
| 隔离依赖目录 | `build/generated/` 下 `llvc_cpu_deps`（torch 2.7.1+cpu）、`seed_cpu_deps`、`seed_audio_deps`（torchaudio）、`world_deps`（pyworld）、`eval_deps_20261016`（onnxruntime） |
| 浮点变调参考 | `src/reference/pitch_shift.py`，PCM16 单声道 WAV，固定 ratio |
| 整数与 F0 参考 | `src/reference/pitch_shift_fixed.py`、`voice_profile.py`；[定点契约](team_project/fixed_point_contract.md) |
| 注册/声线算法 | `src/reference/world_registration.py`、`source_target_mapping.py`、`spectral_balance.py`、`low_frequency_guard.py` |
| Python 验证 | 根目录执行 `python -m unittest discover -s sim -v` |
| AXI 旁路 RTL | `src/rtl/axis_audio_bypass.v`，测试台 `sim/tb_axis_audio_bypass.v` |
| 旁路仿真 / 独立综合 | `build/run_bypass_sim.ps1`、`build/synth_bypass.tcl` |
| 变调核仿真 / 综合 | `build/run_pitch_sim.ps1`、`build/synth_pitch.tcl` |
| PS 程序编译 / 验证 | `build/build_ps_reference.ps1`、`sim/verify_ps_board_log.py` |
| 板端现场入口 | `board/world_live_trial.md`、`board/capture_source_mapping.py`、`board/play_voice_comparison.py` |
| 离线评测入口 | `build/audit_seed_reference_20261016.py`（四项指标：身份/泄漏/自然度/内容） |
| 交接原件，只读 | [工程总交接](交接/工程总交接_20261009.md)、`交接/核心材料/` |
| 历史归档 | `交接/归档_md_20261016/`；交接全量核验 `report/handoff_file_check.json`（8399 文件大小/SHA 全符，非重新板测） |

生成文件放 `build/generated/` 或 `tmp/`，正式证据放 `report/`，不往资料盘写输出。厂商工程与资料不直接原地重建。

## 已核实的板端与工具事实

- 串口：交接记录为 COM14/115200；**2026-10-16 本机只枚举到 COM7、COM8**，COM14 未出现。板卡已上电，但用前必须以实际枚举为准，不沿用旧端口。
- 板端：PetaLinux 2022.2 / 内核 5.15.0-xilinx，WM8960 声卡；历史上播放 `hw:0,0`、采集 `hw:0,1`，32kHz、S24_LE、双声道。板内时间与 PC 不同，用 PC 日志时间与 SHA 追踪。
- 已验证资产：Python 17 项测试；AXI 旁路仿真；变调 RTL 24576 样本全符；变调独立综合 340 LUT/117 寄存器/1 BRAM/6 DSP（100MHz 估计 WNS+4.311ns）；本板音频＋独立 DMA 候选布局布线 8302 LUT/13179 FF/5 BRAM/6 DSP、WNS+2.160ns/WHS+0.017ns（外部 IO 延时未补全，未加载）；板端 PS 定点参考 12 组数值全符；PS-only v5 实时升调可听且延迟明显减轻；WORLD v22/200ms 现场 3 分钟零欠载、2 个输入触顶。
- 未通过：G1（真实音频旁路与块回传的完整证据）、目标音色、多人泛化、新目标现场注册闭环、定量端到端延迟、10 分钟以上稳定性。

## 队友历史版本：按 SHA 而非文件名识别

路径以 `交接/核心材料/` 为根，完整 SHA 见 [交接审阅总结](team_project/handoff_review.md)。

- 通过历史音频/GEMM 测试的位流：`g_build/proj/zynq_gemm_irq_swap.bin`，SHA 前缀 `721a788816aa`。
- v2 模型：`board_budget_20261005/llvc_deploy_model_reduced.bin`，头版本 2，SHA 前缀 `4e635452493b`；听感已被用户否决，只作历史对照。
- 融合程序实际包名：`deploy_runtime/kv_fuse_candidate_20261009/deploy_kv_fused_20261009`，板端历史名 `deploy_kv_fused`。
- 历史 500ms 脚本：`board_native32_live_500ms_backup.sh`，SHA 前缀 `e6779db674d1`；包内同目录 `board_native32_live.sh` 是 150ms 失败试验，不能按同名直接上传。
- 偏置候选：要求头版本 3，包内没有成功导出的 `model_bias.bin`；未通过编译、数值、速度和真人验证，不要与 v2 程序混搭。
- 交接里的"四名留出说话人"实为同一 SSB0434 的四段音频；完整验证集 8 对/2 人，不作为四人泛化结论。

## 音频与板端注意事项

- 原理图：外接 MIC 走 WM8960 左输入（粉色 J12），音响接绿色 J13；板载咪头不用。队友历史设备树靠右输入路由维持 MICB 供电，后续必须查当前 DAPM，不能因为不用板载咪头就关掉所有右输入。
- 历史 ALSA 为 32kHz S24_LE 双声道，模型为 16kHz 单声道浮点。PCM16/32 位 AXI 草案是另一份格式契约，必须显式转换，不能直接替换。
- 现场规则：需要讲话/录音/试听时先问准备；未获确认不启动音频、不播放。停止服务用板上脚本，不用全局 kill。
