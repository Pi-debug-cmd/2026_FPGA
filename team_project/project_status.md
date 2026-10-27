# 项目接手状态

检查日期：2026-10-21。用户已确认截止 2026-11-06。项目共有三个写作者：当前已提交的两位都有板卡和 Vivado，尚未加入的第三位只做电脑端/PS 方案；实际日历见根目录 [plan.md](../plan.md)，任务与结果统一写入 [coummucation.md](../coummucation.md)。

**当前任务入口：**本页保留大量 10 月 16 日历史证据；执行范围以根目录 [三级计划](../plan.md) 为准。现在只开放 `PS-20261021-10`：固定一名男性输入者到既定女性目标声的一对一电脑端质量上限。目标音色、Cortex-A9 部署、PL 音质回归和实时性均未通过。旧 `PS-20261021-01/02`、G1～G7 顺序和“需要第二名固定输入者”的说法均已被替代，不得作为新任务认领依据。

逐日进展与历史状态块见 [每日交接](../交接/归档_md_20261016/handoff) 与 [协作记录](../report/ai_worklog.md)。

## 现行硬约束（2026-10-16）

- **全脱机/裸机**：不接电脑、板上自足；准备阶段（现场注册目标声源 + 板上构建音色转化模型）与实时转换阶段都在板上完成，板上资源可自由使用。详见 [需求记录](../report/onboard_standalone_requirement_20261016.md)。
- **现场注册目标声源**：演示时在板上录目标人几句话，板上当场建模；含质量门槛（时长/有声帧/触顶/静音）、重注册与回退；产物是目标画像参数，不是波形。
- **输入者免录入免校准**：只注册目标，陌生说话人直接讲话转换。见 [权威需求修正](../report/source_uncalibrated_requirement_20261015.md)。
- **多输入者到同一目标**：固定倍率变调不算实现。见 [需求记录](../report/multi_input_requirement_20261014.md)。
- 大小声适应放最后；每轮实际录放先取得当轮准备确认。

## 当前依据

当前范围以根目录 `plan.md` 和 `AGENTS.md` 为准；`team_project/README.md`、`development_plan.md`、`team_roles.md` 仅保留历史设计与分工参考。沿用野火 Zynq-7020、Vivado 2026.1、`xc7z020clg400-2`，不回到候选题重新选题。

当前还没有通过音色门的 PS 方案。`LLVC content → FARGAN v1` 虽通过身份和源泄漏门，但 UTMOS 1.660、CER 0.582，已拒绝。下一开放任务为 `PS-20261021-10`；按 `plan.md` 完成第一级的电脑音色、Cortex-A9 文件、真人试听后才进入 PL 资源评估、部署与加速。

根目录 PDF 的自主选题条款已核对：需要板级实测、基线比较、可复现构建、资源时序证据、AI 协作记录和技能包。PDF 页 23（印刷页 20）允许其他工具版本，但需说明并保证脚本可复现。用户提供截止日期 2026-11-06，具体提交时刻与最终规则仍须核对。

## 本轮新增（2026-10-16）

| 项目 | 状态 | 证据或限制 |
| --- | --- | --- |
| Seed-VC 参考离线审计 | 已完成（四项指标） | 身份余弦 0.551、对源泄漏 0.021、UTMOS 2.736、字错 2/18；对照 WORLD 0.216/0.383/2.095/7 字与目标自身 0.911。单人、同句、非盲评，Track8 既是提示又属质心故偏高。`report/seed_reference_audit_20261016.json` |
| Seed-VC 7020 可行性 | 判定为不可直接上板 | 约 363M 参数、FP32 约 1.45GB＞1GB DDR、30 步顺序扩散、主机 CPU RTF≈2.60；只能作离线教师/上限参考 |
| 全脱机需求与准备阶段两项任务 | 已记录，待接入实现 | `report/onboard_standalone_requirement_20261016.md`；尚未移植到板上 |
| 参数化路线身份天花板 | 未验证（判决性实验待跑） | 决定主线投入方向的关键实验，尚未执行 |
| 参数化路线身份天花板 | 已实测，判定触顶 | 已有候选全部 0.19～0.22、源泄漏 0.37～0.63（按人仅音高反而 0.064）；同期 Seed-VC 0.551/0.021。`report/param_candidate_audit_20261016.json` |
| 目标注册工具（任务 A 第一步） | 宿主 + ARM 编译通过；**板端运行通过** | `src/ps/world_register.cpp`：F0 分布/频带谱比例/AP 均值 + 质量门槛；宿主 vs pyworld 最大差 ≤4.6e-7；板上两条正样本与宿主逐项差异 0.0（含 513 点平均谱）、负样本返回 3/5；ARM SHA `D5BDB272…`。`report/world_register_parity_20261016.json`、`report/world_register_board_20261016.json` |
| 现场注册闭环（录目标→建模→立刻转换→重注册/回退） | 部分：文件回放闭环已通 | `world_register`→`world_convert` 均在板上跑通，ARM/宿主输出相关 1.000000；**20 秒音频耗时 20.165 秒（RTF≈1.008）**；身份 0.190／泄漏 0.172／UTMOS 2.035／字错 0.167。现场录音、实时链路与回退未验证。`report/world_convert_board_20261017.json` |
| 文档结构整理 | 已完成 | 归档候选阶段与历史交接至 `交接/归档_md_20261016/`，三份状态文档去重；原文备份同目录 |

## 已检查与已完成

| 项目 | 状态 | 证据或限制 |
| --- | --- | --- |
| 初次接手文件 | 已检查 | 初次范围只有 PDF 和规划 Markdown；后续补充"交接"目录 |
| 队友交接材料 | 本地文件核验完成 | 8399 文件全量大小/SHA 一致；历史录放、GEMM、模型有日志，但当前未复测；见 `handoff_review.md` |
| 最新选题 | 文档已确定 | 不回到候选题重新选题 |
| 执行责任 | 用户已明确 | 接手方全盘接手；旧 A/B/C 仅为工作职责参考 |
| 编码规范 | 已读取根目录副本 | AGENTS.md 指定的另一个 `code_rule.md` 路径不存在；按本工作区 [code_rule.md](../code_rule.md) 执行 |
| 流式浮点参考 | 已实现并通过合成信号验证 | `src/reference/pitch_shift.py`；不是定点黄金参考或目标音色模型 |
| 自动验证 | 17 项已通过 | `report/reference_tests.txt`；含定点误差、F0、注册拒绝、PCM24 与降采样 |
| 基础变调定点/RTL | 本机比对通过 | 六档 24576 样本全符；`report/pitch_sim.txt`；完整音频/DMA 工程未接入 |
| 变调独立综合 | 通过资源/估计时序检查 | 340 LUT、117 寄存器、1 BRAM、6 DSP；100MHz 估计 WNS+4.311ns，非布局布线/整机时序 |
| 单目标注册参考 | 离线 F0 档案已实现 | 正常文件注册、无效录音保留旧配置；不含目标音色模型，现场闭环未实现 |
| 开源参考 | 已初查 | `report/reference_review.md`；未复制第三方代码、未锁定提交或完成源码审计 |
| AXI 旁路 RTL | Vivado 仿真通过 | 1024 样本、符号边界、随机背压、TLAST、待发送数据复位；`report/axis_bypass_sim.txt` |
| 独立模块综合 | Vivado 2018.3 通过 | -1 器件，4 LUT、38 寄存器；仅旁路核，非整机资源/实现时序 |
| Vivado/仿真器 | 已实际运行 | `D:/USER_Software/Xilinx_Vivado/Vivado/2018.3`，xvlog/xelab/xsim 可用 |
| 板卡资料 | 用户指定 A 盘为准 | 使用 `xc7z020clg400-2`；交接 531 项 PS 参数与厂商全同；`report/vendor_audio_audit.json` |
| 音频连接 | 用户已明确 | 麦克风粉色 J12/音响绿色 J13；按 WM8960 路线推进 |
| 镜像与连接 | 历史上 COM14 已核查 | PetaLinux2022.2/内核 5.15.0-xilinx，WM8960 播放 hw:0,0、采集 hw:0,1。**2026-10-16 本机只枚举到 COM7/COM8，用前须现场核对** |
| 板端 PS 定点参考 | 12 组格式/比例测试通过 | PCM16/S24_LE 输出 SHA 全符，非法比例拒绝；`report/board_ps_pitch_check.json` |
| 麦克风短时试听 | v5 短时听辨通过 | 讲话/升调持续可听、延迟明显减轻；20 秒及额外 60 秒零 xrun，非长期验收，见 `report/live_audio_20261010.md` |
| 本板音频＋独立变调 DMA 候选 | -2 布局布线及位流生成完成 | 8302 LUT/13179 寄存器/5 BRAM/6 DSP，WNS+2.160ns/WHS+0.017ns；外部 IO 延时未补全，尚未加载；`report/pl_board_build_20261010.md` |
| 新 DMA 客户端 ABI | 板端注册/卸载通过 | A 盘源码＋实际内核配置重建匹配符号；未启动 DMA |
| WORLD 实时链路 | 可听但未达稳定性门槛 | v22/200ms 现场 3 分钟零欠载、2 个输入触顶；10 分钟 1 欠载/13 触顶/221 输出削顶；`report/world_live600_v22_200ms_20261014.json` |
| 现场注册→新句转换闭环 | 未实现（原流程依赖 PC） | 现为 `world_registration.py` + PC 生成配置；须移植为板上流程 |
| 实时音频、DMA、音色、资源、延迟 | 未验证 | 不把软件测试当板上或语音质量结果 |

## 历史执行顺序（已由 2026-10-21 三级计划取代）

以下是旧路线的存档，不作为当前任务清单；当前任务和出口门见 [plan.md](../plan.md)。

1. **判决性实验（离线）**：量出参数化（WORLD 系）目标化能到的身份天花板，用同一套四项指标（身份/泄漏/自然度/内容）评价；据此决定主线是"参数化 + PL 加速"还是"轻量目标条件化网络"。
2. **板上现场注册链路（任务 A）**：把 C 端实现移植到板上（先做文件回放复现，不需要用户讲话），含质量门槛、画像落盘、重注册与回退。该任务与路线选择无关，可并行。
3. **实时预算专项**：评估 DIO/cheaptrick/合成搬入 PL 的方案与工程量；纯 PS 在连续语音下 RTF≈1.0，不足以实时。
4. **板上构建转换模型（任务 B）**：以画像为输入在板上生成映射/条件参数，可复现、留校验值。
5. 音色候选仅在留出语句上明显优于仅变调后进入硬件；10/26 冻结算法范围。单目标完成后再考虑多目标。
6. 评测口径按 [权威需求修正](../report/source_uncalibrated_requirement_20261015.md) 第 4 条：冻结源说话人独立划分，测试人不得参与任何拟合。

历史规划曾把 G1 列为下一项共同验收；现行优先级已改为 `PS-20261021-10` 一对一音色上限。G1 未通过的历史事实不等于当前应先做 G1。

## 需要补齐的信息

- 演示现场的目标说话人安排（谁来、录几句、语言与内容）与现场环境噪声条件。
- 板卡实际串口与当前上电状态（本机 2026-10-16 只见 COM7/COM8）。
- 端到端延迟的实际测量方法（麦克风到音响），以及与 p95≤100ms 目标的关系。
- 至少 3 位不同基频范围输入者的留出句录音（未开始，且不得用于任何拟合）。

这些条件限制实物验收；电脑端算法、定点和 RTL 可继续推进。总计划已落地，不再等待人员信息。

## 队友成果的使用范围

先读 [交接审阅总结](handoff_review.md)。已有历史 WM8960 音频/GEMM 工程可减少重复工作；固定目标 LLVC 路线未满足实时稳定性/音色目标，也未证明现场新目标注册。保持我们当前范围与基线，按独立验证决定是否复用，不直接将队友 A/B/C 结论换算为我们的 G1～G7 通过。

## 2026-10-18 并行开发结论

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| A3 目标条件化网络 | **正式终结**（身份 0.561、字错 0.056 达标，UTMOS 1.401 未达 1.8；三种后处理无法挽回，根因是包络系统性形状偏差） | `report/a3_neural_feasibility.md` §0c、`report/a3_neural_round3_summary.json`、`build/generated/a3_neural/postproc_sweep.json` |
| 主线 | 回到 A1（参数化 WORLD，0.190/0.172/2.035/0.167） | 同上 |
| 身份上限（技术结论） | 参数域可达 **0.53～0.56**，不再是 0.19～0.22 | 第三轮 + 复核 |
| PL 合成卸载 | 时分复用版开发中；首版全并行 LUT 超限 132%/141%；最新综合 363 LUT 可疑，待核对是否被优化 | `build/generated/pl_synth_offload/`、`report/pl_synth_offload_sim.json` |
| 历史待办（已过期） | 当时提出 A1 与 A3 听感取舍及 PL 资源/时序检查；A3 后来已被用户否决，当前任务依 `plan.md` | 见 worklog |

2026-10-26 Remote-PS-C / PS-20261025-20：已接收 main PR #12 的配对语料，独立下载校验 `PASS 200 800`；代理和 Git 凭据可用。仅资产接收通过，训练及五门评测待运行。见 `report/ps_20261025_20_corpus_receipt_20261026.md`。

2026-10-26 Remote-PS-C / PS-20261025-20：HuBERT→目标 FARGAN v1 首轮电脑端筛选 **REJECTED**。身份 0.778815/P10 0.751712/UTMOS 2.418010 达标，源泄漏 0.252929、CER 0.235294 未达标；未启动试听/板测。辅助 192/8 训练选择检查点后仅评价固定男性 4，男性 5/Track 9 保持锁定。证据：`report/ps_20261025_20_hubert_fargan_v1_20261026.md`；完整数值、代码/资产 SHA 与历史见同名 JSON。模型交付接收测试另轮记录。

2026-10-26 Remote-PS-C / PS-20261025-20：修复 portable CLI 路径后，完整模型归档 198734997 bytes/466 文件在新干净检出本地 smoke PASS，输出 SHA 与评价 WAV 相同。质量仍 REJECTED；线上交付 BLOCKED：仓库 API 显示公开，与私有 Release 约束冲突，尚未上传模型。证据：`report/ps_20261025_20_model_archive_local_smoke_20261026.md` 及 model_delivery JSON；下一步仅在交付位置明确后做线上下载复现。

2026-10-26 Remote-PS-C / PS-20261025-20：用户明确授权当前公开仓库发布完整模型包后，已发布 `model-PS-20261025-20-hubert-fargan-v1`（源码 94d2aa2、198734997 bytes、SHA 9532fe32d5ab707a51662b224f82a95abba901d9fc4fcc4276cedd0cf2ca4e6a），GitHub 空目录重新下载/466 文件校验/干净检出推理 PASS，输出 SHA 与原评价完全相同。交付 VERIFIED，质量仍 REJECTED（泄漏/CER），不进入 WAIT_LOCAL_TEST。完整接收证据和复现命令：`report/ps_20261025_20_github_model_receipt_20261026.md`；保留此前阻塞历史，未改规则/可见性/分工，无试听或硬件验收。

2026-10-26 Remote-PS-C / PS-20261025-20：冻结 v1 完成 200 对配对特征诊断，800 项 SHA 和缓存 target 全匹配；重新提取的倒谱 MAE 约 1e-7，音高/周期相关存在局部差异，不宣称历史逐位一致。能量最佳时移最大 20ms，不能代替音素对齐验证。辅助 validation 8 对/4616 帧归一化 MAE 0.452731 vs 常数基线 0.806939，部分高阶倒谱及音高差分动态偏弱。证据：`report/ps_20261025_20_feature_diagnostic_20261026.md`/JSON/TXT。没有新训练或五门评分，质量仍 REJECTED，无试听/板测；下一单变量候选待 Remote-PS-C 执行。


### [PS-20261025-20] v2 delta=1.0 单变量结果
- 日期：2026-10-26；角色：Remote-PS-C / Codex；状态：REJECTED；基准 e8bb8e016caf987ad0f2dc99521794c97b8fd192；main 9c42263ea3aa12898ad451f3c00915e816f039c4；开放 PR #9/#11/#13 无本任务冲突。
- 路径/复现：build/remote_ps_c_hubert_fargan_v2.py train --cache-root build/generated/remote_ps_c_hubert_fargan_v1，然后 infer，再运行原 strict evaluator；report/ps_20261025_20_hubert_fargan_v2_20261026.md/JSON/TXT 保存完整命令/日志/转写/哈希。共享入口只增加版本输出名与显式缓存复用；状态/工作日志追加。
- 唯一训练变量：delta loss 0.25→1.0；其余配置逐项相同，200 缓存 SHA 已核验，重算统计数组与 v1 完全相同；v1 权重/统计/缓存不变。辅助 validation 最优step400、停止step1200、损失0.2605001032、272.828秒；跨权重总损失不可直接比较。
- 一次 Male4 原五门：身份 0.778145609 / P10 0.755978229 / 泄漏 0.255133692 / UTMOS 2.574109713 / CER 0.235294118；通过项 {'identity': True, 'identity_p10': True, 'leakage': False, 'utmos': True, 'cer': False}。输出SHA 9e7f37895e8188b96909edad73b140fbcf5e7a14ebd3c1202605a27b339745e7；mapper 610f592539fd51420409ca413e04232f3cd20da57f885957d050c6157569791c。
- 限制/下一责任方：仅电脑端；辅助192train/8validation，未拟合Fixed-Male1–3；Male5/Track9锁定；无参数扫描/门槛更改/录音/播放/试听/板卡/ARM/Vivado/RTL/PL/实时验收。Remote-PS-C 完成版本化模型归档与干净下载；未全过不进入 WAIT_LOCAL_TEST，不给Hardware-A/B启动板测。


### [PS-20261025-20] v2 完整 Release 与干净下载结果
- 日期：2026-10-26；角色：Remote-PS-C / Codex；基准/源码 0a8ae4e261cc098cc8c489a12865d9c28452fe64；状态：交付 VERIFIED_GITHUB_DOWNLOAD_AND_INFERENCE，质量 REJECTED；PR #11。
- 授权/资产：沿用用户“授权在当前公开仓库发布完整模型包”；https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/model-PS-20261025-20-hubert-fargan-v2；附件 PS-20261025-20_hubert_fargan_v2_windows_cpu.zip，198735391 bytes，SHA a669cb614dc4f71090b898da48e7fc127fbf016892dc3d655be1a535042a4441。标签指向精确源码，server digest/下载大小/SHA及466个内部文件全匹配；无WAV/语料/缓存，v1未改。
- 路径/复现：report/ps_20261025_20_github_model_receipt_v2_20261026.md/JSON/TXT（完整下载/校验/依赖/推理命令）；model_delivery_PS-20261025-20_hubert_fargan_v2_20261026.json（逐文件SHA）；独立新目录执行 build/remote_ps_c_hubert_fargan_v2.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe。状态/工作日志同步追加。
- 量化：干净GitHub下载推理exit0，2.750s/RTF0.151098901，封装53.756680s；16kHz mono PCM16/291200 samples，输出SHA 9e7f37895e8188b96909edad73b140fbcf5e7a14ebd3c1202605a27b339745e7 与本轮五门原WAV完全相同，未重新评分。Python峰值工作集1110630400 bytes/pagefile2384629760 bytes，不含native子进程。
- 失败保留：首次上传后/下载前缺少接收父目录报WinError3；创建父目录后核对同一附件，未覆盖发布。日志保留失败及最终成功；独立venv复制锁定库，未测试新pip安装；同机隔离复验，非第二台实体电脑。
- 限制/下一责任方：身份0.778145609/P10 0.755978229/泄漏0.255133692/UTMOS2.574109713/CER0.235294118，泄漏/CER仍失败，非WAIT_LOCAL_TEST。Remote-PS-C保存证据，Hardware-A/B不启动试听/板测；Male5/Track9锁定，无录音/播放/真人/ARM/Vivado/RTL/PL/实时验收，未改分配/规则/可见性。


### [PS-20261025-20] 冻结教师→声码器→映射器诊断结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：DIAGNOSTIC_COMPLETE，v1/v2 质量仍 REJECTED，非 WAIT_LOCAL_TEST；基准 04819add786e0c07f9772afadaf7a2ba67f565d7；main 9c42263ea3aa12898ad451f3c00915e816f039c4（提交前再次 fetch，保持祖先）；PR #11，未改分工/规则。
- 路径/复现：build/diagnose_remote_ps_c_fargan_chain.py；report/ps_20261025_20_chain_diagnostic_20261027.md/JSON/TXT。项目根目录执行 build/generated/remote_ps_c_env/Scripts/python.exe -m py_compile build/diagnose_remote_ps_c_fargan_chain.py，再以 -u 运行同脚本；完整 PowerShell 命令、资产前提及 SHA 见报告。固定现有辅助 validation 8 对/2 人/4616 帧、5 条件共40波形；冻结模型/统计/缓存，无训练或新权重。
- 量化：source/teacher PCM/teacher features oracle/v1/v2 的 CER（相对源自动转写）为0/150、15/150、16/150、20/150、20/150；相对清单文本为21/152、22/152、25/152、28/152、31/152。目标身份均值0.186086690/0.868033508/0.799975958/0.780120042/0.778752680；描述性源相似度均值0.842271856/0.234730201/0.242190654/0.225207688/0.229753263。
- 验证：exit0、90.219秒；8对/40条件/4616帧、有限值、CER及均值重算、127个不同文件大小/SHA及WAV格式/时长核对PASS。权重/统计未变；保留原ASR警告。运行后D余量378846371840 bytes/C92113235968 bytes；生成物留D项目忽略目录，无下载。
- 限制：辅助集已用于选检查点；清单未经本轮人工复核，源ASR与清单已有13.82%差异。源画像逐句留一且不同于Fixed-Male验收，不能套用泄漏门；未算UTMOS，指标差值不能证明因果或固定男性失败根因。v2无内容改善。原五门数值/拒绝结论不变，不继续delta扫描；未读Fixed-Male音频/Track9，Python保护非OS全量审计；无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时验收。
- 下一责任方：Remote-PS-C提交本轮证据及更新PR #11，维护者审核；既有v1/v2模型Release保持不变，Hardware-A/B不由本轮启动试听或板测。本轮停止，不新增训练。


### [PS-20261025-20] v3 PCA192 单变量结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准60364cb333dc0f3474797f05222a8948bbcb9e26；main9c42263ea3aa12898ad451f3c00915e816f039c4，开放PR #9/#11/#13无冲突。
- 路径/复现：build/remote_ps_c_hubert_fargan_v3.py、build/run_remote_ps_c_hubert_fargan_v3.py；report/ps_20261025_20_hubert_fargan_v3_20261027.md/JSON/TXT。驱动固定train复用v1缓存、infer、原strict evaluator一次五门；完整命令与资产SHA见报告。
- 唯一配置变量：相对v1 pca_dim96→192，delta0.25不变；保留训练方差0.862445935（v1为0.749045423），参数1155284；维度改变初始化随机数消耗，非同初始化。训练/验证192/8，最佳step400、停止1200、loss0.1972120106、271.313s。mean/y统计/分位、投影前96和旧模型/缓存保持一致。
- 一次Male4五门：身份0.763920106/P100.747006375/泄漏0.261376895/UTMOS2.508168141/CER0.558823529；通过项{'identity': True, 'identity_p10': True, 'leakage': False, 'utmos': True, 'cer': False}。输出SHAd1fb89990a7c5cdc2a57174d1f1e0f5b5c3715239fd19c5e07594469c39cf703，mapper836a4595e6fc2bc8992107645b58a6ffd97ecdb724ef91186093009058b397aa。各阶段exit0，语法/有限JSON/格式/哈希/原评估器口径检查PASS；首次启动自动审核超时、未启动进程，重试一次成功。
- 限制/下一责任方：辅助集选检查点，Male4开发筛选非独立验收；Male1–3只作源画像，Male5/Track9锁定。Python保护非OS全量审计，无录音/播放/真人/硬件/ARM/Vivado/RTL/PL/实时验收，不改规则/分工。Remote-PS-C另轮发布完整模型与干净下载；未全过不进入WAIT_LOCAL_TEST，不据结果追加本轮维度扫描。


### [PS-20261025-20] v3 完整 Release 与干净下载结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；基准/源码 ce4f2c7e9e7b3bc09b8c37532dbfb3f8d258c1bb；状态：交付 VERIFIED_GITHUB_DOWNLOAD_AND_INFERENCE，质量 REJECTED；PR #11。
- 授权/资产：沿用用户“授权在当前公开仓库发布完整模型包”；https://github.com/Pi-debug-cmd/2026_FPGA/releases/tag/model-PS-20261025-20-hubert-fargan-v3；附件 PS-20261025-20_hubert_fargan_v3_windows_cpu.zip，199369174 bytes，SHA 02d6a414f68d220916718dbaf6402ad8a73dd1d6d84a698151816353a19b76ae。标签指向精确源码，server digest/下载大小/SHA及466个内部文件全匹配；无WAV/语料/缓存，v1未改。
- 路径/复现：report/ps_20261025_20_github_model_receipt_v3_20261027.md/JSON/TXT（完整下载/校验/依赖/推理命令）；model_delivery_PS-20261025-20_hubert_fargan_v3_20261027.json（逐文件SHA）；独立新目录执行 build/remote_ps_c_hubert_fargan_v3.py infer --assets bundle --output bundle --native bundle/native/fargan_probe_host.exe。状态/工作日志同步追加。
- 量化：干净GitHub下载推理exit0，2.563s/RTF0.140824176，封装49.830876s；16kHz mono PCM16/291200 samples，输出SHA d1fb89990a7c5cdc2a57174d1f1e0f5b5c3715239fd19c5e07594469c39cf703 与本轮五门原WAV完全相同，未重新评分。Python峰值工作集1113186304 bytes/pagefile2382503936 bytes，不含native子进程。
- 验证边界：发布/下载/校验/推理日志完整保留；独立venv复制锁定库，未测试新pip安装；同机隔离复验，非第二台实体电脑。
- 限制/下一责任方：身份0.763920106/P10 0.747006375/泄漏0.261376895/UTMOS2.508168141/CER0.558823529，泄漏/CER仍失败，非WAIT_LOCAL_TEST。Remote-PS-C保存证据，Hardware-A/B不启动试听/板测；Male5/Track9锁定，无录音/播放/真人/ARM/Vivado/RTL/PL/实时验收，未改分配/规则/可见性。
- 公开证据处理：自动审批阻止发布本机容量/绝对路径后，新增交付收据只保留通用项目路径；原始日志/容量检查留本地，模型/指标/哈希未变。

### [PS-20261025-20] v4 源说话人对抗映射认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `6d940c927f4ba7ffefb97761dafa68c2f4295750`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11，未发现同任务冲突。
- 假设/范围：v1/v2/v3 的源泄漏分别约 0.253/0.255/0.261，且 PCA 与 delta 单变量均未改善。v4 保留 PCA96、delta0.25、数据切分、HuBERT layer9、双向 GRU192、优化器、早停与原五门；只新增训练期源说话人对抗分类器和梯度反转约束（20 个辅助训练说话人，权重0.05），推理仅使用映射器输出。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v4.py`、`build/run_remote_ps_c_hubert_fargan_v4.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v4/`；正式报告 `report/ps_20261025_20_hubert_fargan_v4_20261027.*`。复用经 SHA 核验的 v1 200 对缓存，不读取 Male5/Track9。
- 停止条件：辅助 validation 选 checkpoint 后只做一次 Fixed-Male4 原五门；未全过不进入 WAIT_LOCAL_TEST、不启动试听或硬件，不继续本轮参数扫描。若该约束有效，再决定是否只调整一个对抗权重。
- 限制/下一责任方：电脑端非因果上限；无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C 负责提交失败或通过证据，维护者审核 PR #11。

### [PS-20261025-20] v4 源说话人对抗映射结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准6d940c927f4ba7ffefb97761dafa68c2f4295750；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v4.py、build/run_remote_ps_c_hubert_fargan_v4.py；report/ps_20261025_20_hubert_fargan_v4_20261027.md/JSON/TXT。训练复用v1缓存，三阶段exit0，原strict evaluator只筛选一次Male4；完整SHA/日志见报告。
- 唯一新增变量：训练期20类源说话人分类器+梯度反转，speaker_adv_weight0.05；PCA96、delta0.25、数据切分、seed、双向GRU192、优化器、早停和五门口径不变。统计逐元素等于v1，v4参数1144552，最佳step800、停止step1600、训练359.391s。
- 一次Male4五门：身份0.773824141/P100.745913965/泄漏0.239771249/UTMOS2.426944574/CER0.470588235；通过项{'identity': True, 'identity_p10': True, 'leakage': False, 'utmos': True, 'cer': False}。相对v1泄漏下降但CER恶化，仍REJECTED，不进入WAIT_LOCAL_TEST。
- 限制/下一责任方：对抗项只训练电脑端映射，非因果、无板卡/试听/实时声明；Male5/Track9锁定。Remote-PS-C提交本轮失败证据，下一轮只考虑对抗权重单变量调整。

### [PS-20261025-20] v5 对抗权重 0.01 单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `38f54d0`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：v4 对抗权重0.05使源泄漏降至0.2398但CER升至0.4706。v5 只将 `speaker_adv_weight` 从0.05降为0.01，PCA96、delta0.25、数据、seed、网络、优化器、早停和原五门不变，检验较弱对抗是否恢复内容并保留泄漏改善。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v5.py`、`build/run_remote_ps_c_hubert_fargan_v5.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v5/`；报告 `report/ps_20261025_20_hubert_fargan_v5_20261027.*`。复用 v1 缓存，不读取 Male5/Track9。
- 停止条件：辅助 validation 选 checkpoint后只做一次 Fixed-Male4 五门；未全过不进入 WAIT_LOCAL_TEST，不发布模型包；本轮不扫描其它权重。
- 限制/下一责任方：电脑端非因果实验，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果并维护PR #11。

### [PS-20261025-20] v5 源说话人对抗映射结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准6d940c927f4ba7ffefb97761dafa68c2f4295750；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v5.py、build/run_remote_ps_c_hubert_fargan_v5.py；report/ps_20261025_20_hubert_fargan_v5_20261027.md/JSON/TXT。训练复用v1缓存，三阶段exit0，原strict evaluator只筛选一次Male4；完整SHA/日志见报告。
- 唯一新增变量：训练期20类源说话人分类器+梯度反转，speaker_adv_weight0.01；PCA96、delta0.25、数据切分、seed、双向GRU192、优化器、早停和五门口径不变。统计逐元素等于v1，v5参数1144552，最佳step400、停止step1200、训练266.797s。
- 一次Male4五门：身份0.777850780/P100.750804871/泄漏0.266084400/UTMOS2.461675485/CER0.323529412；通过项{'identity': True, 'identity_p10': True, 'leakage': False, 'utmos': True, 'cer': False}。相对v1泄漏下降但CER恶化，仍REJECTED，不进入WAIT_LOCAL_TEST。
- 限制/下一责任方：对抗项只训练电脑端映射，非因果、无板卡/试听/实时声明；Male5/Track9锁定。Remote-PS-C提交本轮失败证据，下一轮只考虑对抗权重单变量调整。

### [PS-20261025-20] v6 目标特征均值收缩单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `ca3e709`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：v1身份0.779但泄漏0.253，v4对抗虽降泄漏仍损伤CER。v6 不重训，只复用冻结v1 mapper/statistics/native，将20D输出逐帧向训练目标均值收缩50%，再合成与评价；不改变数据、模型权重、五门口径或源/目标锁定。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v6.py`、`build/run_remote_ps_c_hubert_fargan_v6.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v6/`；报告 `report/ps_20261025_20_hubert_fargan_v6_20261027.*`。只读取 Fixed-Male4，Male5/Track9锁定。
- 停止条件：只做一次原五门；若未同时过门则记录并继续下一明确单变量假设，不发布模型包。
- 限制/下一责任方：电脑端离线实验，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果并维护PR #11。

### [PS-20261025-20] v6 目标特征均值收缩结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准ca3e709；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v6.py、build/run_remote_ps_c_hubert_fargan_v6.py；report/ps_20261025_20_hubert_fargan_v6_20261027.md/JSON/TXT。只复用v1冻结mapper/statistics/native，输出逐帧向target y_mean收缩50%，infer/evaluate exit0。
- 一次Male4五门：身份0.579423544/P100.550014264/泄漏0.251125215/UTMOS1.350889683/CER0.338235294；泄漏未改善且身份/UTMOS下降，仍REJECTED。
- 限制/下一责任方：Male5/Track9锁定，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时验收；Remote-PS-C保留失败证据，下一轮改特征级方法。

### [PS-20261025-20] v7 能量/周期性列目标均值替换认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `268f311`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：历史 FARGAN 控制确认 20D 第0列能量、第19列周期性是源泄漏敏感项。v7 只将冻结v1输出的这两列替换为训练目标 `y_mean`，保持其余18列、mapper、统计、native、数据和五门不变；不重训。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v7.py`、`build/run_remote_ps_c_hubert_fargan_v7.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v7/`；报告 `report/ps_20261025_20_hubert_fargan_v7_20261027.*`。只读取 Fixed-Male4，Male5/Track9锁定。
- 停止条件：只做一次原五门；未同时过门不进入 WAIT_LOCAL_TEST，不发布模型包。
- 限制/下一责任方：电脑端离线后处理，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果并维护PR #11。

### [PS-20261025-20] v7 能量/周期性列目标均值替换结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准268f311；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v7.py、build/run_remote_ps_c_hubert_fargan_v7.py；report/ps_20261025_20_hubert_fargan_v7_20261027.md/JSON/TXT。v1冻结mapper/statistics/native，仅替换输出列0/19为target y_mean；首次索引失败后最小修复，成功infer/evaluate exit0。
- 一次Male4五门：身份0.566145985/P100.549324480/泄漏0.283425730/UTMOS1.436652144/CER0.352941176；针对性列替换未改善，仍REJECTED。
- 限制/下一责任方：Male5/Track9锁定，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时验收；Remote-PS-C保留失败与修复证据，后续改训练目标或内容表示。

### [PS-20261025-20] v8 HuBERT layer12 单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `ba06fd3`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：v1/v4/v5显示输出后处理或对抗权重难以兼顾CER与泄漏。v8 只将 HuBERT hidden layer9 改为 layer12，PCA96、delta0.25、双向GRU192、数据切分、seed、优化器、早停和原五门不变；重新生成独立 layer12 缓存，不复用 layer9缓存。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v8.py`、`build/run_remote_ps_c_hubert_fargan_v8.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v8/`；报告 `report/ps_20261025_20_hubert_fargan_v8_20261027.*`。只读取辅助配对语料，Male5/Track9锁定。
- 停止条件：cache/train/infer/evaluate完成后只做一次Fixed-Male4五门；未全过不进入WAIT_LOCAL_TEST、不发布模型包、不扫描其它HuBERT层。
- 限制/下一责任方：电脑端非因果实验，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果并维护PR #11。

### [PS-20261025-20] v8 HuBERT layer12 结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准ba06fd3；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v8.py、build/run_remote_ps_c_hubert_fargan_v8.py；report/ps_20261025_20_hubert_fargan_v8_20261027.md/JSON/TXT。唯一变量HuBERT layer9→12，独立cache后train/infer/evaluate exit0。
- 一次Male4五门：身份0.778674664/P100.747804710/泄漏0.240292771/UTMOS2.555467367/CER0.426470588；UTMOS改善但CER失败，仍REJECTED。
- 限制/下一责任方：Male5/Track9锁定，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时验收；Remote-PS-C保留失败证据，下一轮测试layer6内容折中。

### [PS-20261025-20] v9 HuBERT layer6 单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `be4875d`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：v8 layer12提升UTMOS但CER恶化。v9只将HuBERT hidden layer12改为layer6，保持PCA96、delta0.25、网络、seed、数据切分、优化器、早停和五门不变；重新生成独立layer6缓存。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v9.py`、`build/run_remote_ps_c_hubert_fargan_v9.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v9/`；报告 `report/ps_20261025_20_hubert_fargan_v9_20261027.*`。Male5/Track9锁定。
- 停止条件：cache/train/infer/evaluate后只做一次Fixed-Male4五门；未全过不进入WAIT_LOCAL_TEST、不发布模型包、不扫描其它层。
- 限制/下一责任方：电脑端非因果实验，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果并维护PR #11。

### [PS-20261025-20] v9 HuBERT layer6 结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准be4875d；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v9.py、build/run_remote_ps_c_hubert_fargan_v9.py；report/ps_20261025_20_hubert_fargan_v9_20261027.md/JSON/TXT。唯一变量HuBERT layer12→6，独立cache后train/infer/evaluate exit0。
- 一次Male4五门：身份0.553576857/P100.512674765/泄漏0.233601927/UTMOS1.299599926/CER0.794117647；泄漏下降但其余门恶化，仍REJECTED。
- 限制/下一责任方：Male5/Track9锁定，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时验收；Remote-PS-C停止层扫描，改研究训练目标/内容保真。

### [PS-20261025-20] v10 三帧特征平滑单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `1e34f2b`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：v1仍是CER最佳但泄漏未过；layer6/12改变内容-自然度折中均失败。v10不重训，只复用冻结v1 mapper/statistics/native，对20D输出沿时间做3帧居中滑动平均，再合成评价；其它协议不变。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v10.py`、`build/run_remote_ps_c_hubert_fargan_v10.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v10/`；报告 `report/ps_20261025_20_hubert_fargan_v10_20261027.*`。Male5/Track9锁定。
- 停止条件：只做一次原五门；未同时过门不进入WAIT_LOCAL_TEST、不发布模型包。
- 限制/下一责任方：电脑端离线后处理，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果。

### [PS-20261025-20] v10 三帧时间平滑结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准1e34f2b；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v10.py、build/run_remote_ps_c_hubert_fargan_v10.py；report/ps_20261025_20_hubert_fargan_v10_20261027.md/JSON/TXT。冻结v1输出做3帧平滑，infer/evaluate exit0。
- 一次Male4五门：身份0.741703006/P100.705845421/泄漏0.269384651/UTMOS2.244268338/CER0.323529412；仍REJECTED。
- 限制/下一责任方：停止后处理平滑路线，Male5/Track9锁定，无现场或硬件测试；Remote-PS-C继续改训练目标。

### [PS-20261025-20] v11 内容帧 +10ms 对齐单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `465b70a`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：冻结链诊断显示辅助对齐最佳时移中位0ms、P90 10ms；v11只将HuBERT内容插值到FARGAN帧的时间坐标固定向后偏移+1帧（10ms），其余layer9/PCA96/delta0.25/网络/数据/seed/训练和五门不变，重新生成缓存。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v11.py`、`build/run_remote_ps_c_hubert_fargan_v11.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v11/`；报告 `report/ps_20261025_20_hubert_fargan_v11_20261027.*`。Male5/Track9锁定。
- 停止条件：cache/train/infer/evaluate后只做一次Fixed-Male4五门；不扫描其它时移，不发布未达标模型包。
- 限制/下一责任方：电脑端非因果实验，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果。

### [PS-20261025-20] v12 对抗权重 0.02 结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准提交 `2d09f52`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 路径/复现：`build/remote_ps_c_hubert_fargan_v12.py`、`build/run_remote_ps_c_hubert_fargan_v12.py`；`report/ps_20261025_20_hubert_fargan_v12_20261027.md/JSON/TXT`；三阶段 exit 0，audio guard 无拒绝。
- 五门：identity 0.770142852 / P10 0.737552752 / leakage 0.256829248 / UTMOS 2.436301072 / CER 0.323529412；身份、P10、UTMOS通过，leakage 与 CER 失败，未进入 `WAIT_LOCAL_TEST`。
- 边界：仅电脑端；Male5/Track9锁定，无播放、录音、试听、板卡、ARM、Vivado、RTL、PL 或实时验收；v12 不发布模型包，继续下一单变量方案。

### [PS-20261025-20] v13 逐帧源说话人对抗约束认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `82458d7`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 仅改变 speaker adversarial head：片段均值分类改为逐帧分类并平均 CE；其余配置和五门口径不变。路径为 `build/remote_ps_c_hubert_fargan_v13.py`、`build/run_remote_ps_c_hubert_fargan_v13.py`。
- 仍只读辅助配对缓存与 Fixed-Male4；Male5/Track9锁定；电脑端、无播放/录音/试听/板卡/ARM/Vivado/RTL/PL。

### [PS-20261025-20] v13 运行时阻塞记录
- v13 训练 exit 0，生成 mapper/statistics/features；推理阶段启动既有 FARGAN native 时报 Windows `WinError 623`，重试和历史同 SHA native 均失败，未产生可评价 WAV。
- 本轮不产生五门质量结论；保留 `build/generated/remote_ps_c_v13_train.log`、`remote_ps_c_v13_infer.log`、`remote_ps_c_v13_execution.json`，等待电脑端 native 运行时恢复后重试。

### [PS-20261025-20] v11 内容帧 +10ms 对齐结果
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：REJECTED；基准465b70a；main9c42263ea3aa12898ad451f3c00915e816f039c4；PR #11。
- 路径/复现：build/remote_ps_c_hubert_fargan_v11.py、build/run_remote_ps_c_hubert_fargan_v11.py；report/ps_20261025_20_hubert_fargan_v11_20261027.md/JSON/TXT。唯一变量内容帧+1（10ms），独立cache后全阶段exit0。
- 一次Male4五门：身份0.692620680/P100.649548035/泄漏0.264168332/UTMOS1.904939890/CER0.500000000；相对v1恶化，仍REJECTED。
- 限制/下一责任方：Male5/Track9锁定，无现场或硬件测试；Remote-PS-C保留失败证据，继续改训练目标/内容表示。

### [PS-20261025-20] v12 对抗权重 0.02 单变量认领
- 日期：2026-10-27；角色：Remote-PS-C / Codex；状态：CLAIMED；基准提交 `2d09f52`；main `9c42263ea3aa12898ad451f3c00915e816f039c4`；PR #11。
- 假设/范围：v4权重0.05降低泄漏但CER=0.4706，v5权重0.01恢复部分CER但泄漏=0.2661。v12只将speaker_adv_weight改为0.02，其余v4/v5配置、数据、seed、网络、优化器、早停和五门不变。
- 路径/复现：拟新增 `build/remote_ps_c_hubert_fargan_v12.py`、`build/run_remote_ps_c_hubert_fargan_v12.py`；输出 `build/generated/remote_ps_c_hubert_fargan_v12/`；报告 `report/ps_20261025_20_hubert_fargan_v12_20261027.*`。复用v1缓存，Male5/Track9锁定。
- 停止条件：训练、推理和一次原五门评价；未全过不进入WAIT_LOCAL_TEST、不发布模型包。
- 限制/下一责任方：电脑端非因果实验，无录音/播放/真人/板卡/ARM/Vivado/RTL/PL/实时声明；Remote-PS-C提交结果。
