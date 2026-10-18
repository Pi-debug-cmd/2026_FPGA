# 2026-10-12 持续合成开发

用户恢复开发，先读根目录指引和昨天优选的DIO10ms候选。COM14首次不存在，用户确认忘记上电；上电后核对5.15.0-xilinx、刚冷启动、PCM录放closed、DMA不存在、昨天/tmp文件清除。今天使用原厂PL环境，临时文件仅在 `/tmp/codex_world_20261012`，未加载新位流、未打开PCM或修改启动文件。证据 `report/board_resume_poweron_20261012.log`。

上传首先失败两次：新临时目录未创建，接收器打印PREFIX后打开.b64失败。修复 `board/upload_file.ps1` 自动创建经路径校验的项目/tmp目录，超时报错附带有限长度接收尾部；随后大文件上传并SHA验证成功。不是板卡需重启或PL故障。

## 等价相位优化

`build/prepare_world_phase_optimization.py` 从固定上游源文件生成隔离副本 `build/generated/world_budget/optimized_world/synthesis.cpp`，不修改第三方原始源码。将每个频点cos/正平方根计算换为一次sin/cos加单位复数递推。上游脉冲分数时移限定0～1/fs，频点相位范围0～π，两者数学等价。生成器核对原始函数文本只出现一次，并记录原始/生成源SHA。

102组系数覆盖端点和极小系数，最大复相位/单位幅度误差约3.01e-14；主机整段输出PCM逐字节相同。报告 `report/world_phase_math_20261012.json`、`report/world_phase_host_agreement_20261012.json`。

同一冷启动实板对照：原v3总5.082864秒/合成2.567618秒，v4总4.953025秒/合成2.456313秒，均处理五秒同一输入。另一次v4总4.977048秒。三个输出WAV SHA均为 `c4fa9d018df5411bcc4a548ee1b1d991da0e7dfdf709b453f22a628cb5c8b911`，与昨天优选B一致。优化小，不足以单独实现实时；只有单输入A/B初测，不作为统计性能结论。原始日志 `report/board_world_phase_ab_20261012.log`、`report/board_phase_agreement_20261012.log`。PCM仍closed。

## 分批参数持续合成原型

`src/ps/world_stream_synthesis.h` 使用固定上游的WorldSynthesizer/AddParameters/Synthesis2。单个合成器保持整个录音的相位和随机状态；输出128样本/8ms，参数队列16项，参数存储保持到消费完成。末尾补12帧只用于排空FFT响应，不能计作真实麦克风未来上下文。明确检查队列满和输出长度，失败不生成有效结果。

计算探针新增 `stream5` / `stream25` 参数模式（同一DIO10ms/三帧平滑及共振峰映射），分别一次喂5/25帧参数，对应50/250ms。**当前分析仍一次读取完整五秒音频；只验证合成状态与分批调度，不是实时采集链路。** 不应将8ms合成输出块大小当作端到端延迟。

主机两种参数分批输出PCM完全相同，长度80000样本/五秒、无削波；与批量接口相关系数0.981584、RMSE0.008399，因合成实现存在差异，需另行听辨。证据 `report/world_stream_partition_host_20261012.json`。ARM原型v5已编译，待板端预算与数值核对，再准备有限时音质对照。原厂PL、原始音色参考、现有注册配方不变。

## ARM验证与听辨准备

ARM v5按5帧/25帧参数分批均完整生成五秒WAV，SHA同为 `b195736de5f3a820faf7a08084cad8ad49ad59fcc9c3f8ddba160fd30f26a290`。总计算4.973577/4.981974秒，合成2.465847/2.474556秒，无实时余量。分批并未显著提速，它解决的是合成状态保持；后续需分析/合成调度及只计算新参数的滑窗分析。原始证据 `report/board_world_stream_v5_20261012.log`。

下载5帧分批WAV并核对传输/解压SHA，归档 `data/registrations/source_20261011/world_stream_comparison_20261012/stream5_arm.wav`。与主机同接口同分批输出逐字节相同，相关系数1、RMSE0、无削波，记录 `report/world_stream_arm_agreement_20261012.json`。

`build/create_world_budget_comparison.py --stream` 生成17秒对照：目标5秒→停1秒→昨天认可的ARM DIO10ms批量版本5秒→停1秒→持续合成版本5秒。后两段分析同一五秒录音、完全相同F0/谱包络/非周期参数，只更换合成接口；分批合成不是实时采集试听。共用可满足峰值余量的RMS目标0.08847，峰值0.89930、无削波。文件与manifest位于 `data/registrations/source_20261011/world_stream_comparison_20261012`。

播放助手新增经路径校验的 `--base`，仍默认昨天目录，支持今日临时目录，SHA/PCM空闲/保存恢复mixer机制保留。准备命令如下；必须先收到用户本轮明确准备回复：

```sh
python3 /tmp/codex_world_20261012/play_voice_comparison_v3.py --base /tmp/codex_world_20261012 --manifest stream_comparison_manifest_v1.json --audio stream_comparison_v1.wav.gz
```

当日尚未播放任何音频，不将数值一致性、8ms输出块或17秒离线听辨当作实时链路验收。

17秒对照及manifest/助手已上传：gzip 838640字节，SHA `01965bbcc5d27365fb799e7ecbb6addd19581612253a830c0524e328254e1373`。板端压缩/解压双SHA、助手语法、PCM均closed核对通过，日志 `report/board_world_stream_comparison_staging_20261012.log`。实际三段WAV RMS约0.088453/0.088444/0.088445，无削波。等待用户本轮明确准备回复，尚未播放。

用户本轮明确回复“准备好了，开始”后完成17秒播放，返回0；目录 `/tmp/codex_world_20261012/comparison_1559624164301`，日志 `report/board_world_stream_comparison_20261012.log`。mixer恢复命令成功，既有UCM配置缺失提示仍在。等待三段可听性以及持续合成相对批量版本的音色、自然度、颤动反馈，不提前判定音质或今日实际输出恢复已通过。

## 最新反馈、诊断与用户暂停

用户反馈：“都听到了，第三段稍微模糊但是差别不大，最好的还是第二段”。今日实际播放可听确认通过；持续合成v5音质仍逊于批量B，不能用数值一致性替代音质门槛，优选参考维持批量B。

读固定上游源码发现：持续合成的直流分量处理与批量接口不同，且没有批量版本的分数采样时移。尚未证明哪项导致用户听到的模糊。新增 `build/prepare_world_stream_alignment.py`，仅将直流去除公式、窗口长度和相应缓冲分配对齐到批量接口，生成隔离副本 `build/generated/world_budget/aligned_world/synthesisrealtime.cpp`；原上游未改。构建脚本新增可选 `-AlignedStreamDC`，此实验仅完成主机验证，未生成/上传ARM候选。

主机v6的50/250ms参数分批PCM仍完全一致、无削波；但相对批量基准相关系数从0.981584降至0.979353、RMSE从0.008399升至0.012109，故不拿该改动请求试听。记录 `report/world_stream_dc_host_20261012.json`。源码检查进一步显示，持续合成目前仅在输出块范围内调度脉冲，而批量直流响应含前半段；对齐为非因果响应时需要一起检查未来脉冲调度、有效样本释放、缓冲边界及参数保留，不能只改窗口。仍为待验证推断，不是已定位的模糊根因。

用户随后明确要求临时暂停。已停止开发，仅保存本地交接；没有再次调用串口、编译或试听。最后板端操作为已完成的17秒播放，mixer恢复返回0；板卡保留原厂PL、今日计算暂存目录，暂停后的状态未重新查询。恢复入口：先读本节，保持批量B基准；检查相位与前视输出调度，先做数值/边界验证，再决定是否上板和请求用户试听。

## 用户恢复后的完整合成对齐

用户再次要求“开始吧”。COM14最初无提示符，用户确认重新打开板卡后冷启动核对通过，旧暂存已清空；重新上传仅用于计算的探针及已有输入，不播放、不更换PL。WSL编译的自动审批超时两次，默认权限下WSL访问被拒；改用本机 `D:/mingw64/bin/g++.exe`、SDK ARM编译器和默认权限串口工具继续，未要求用户审批。原始恢复日志 `report/board_resume_second_poweron_20261012.log`。

`build/prepare_world_stream_alignment.py --full` 生成隔离副本 `aligned_world_full/synthesisrealtime.cpp`：匹配批量直流处理，保持整数脉冲位置并补充分数采样相位；输出释放前累计FFT前半段所需的未来脉冲（32ms），同时修正队列就绪/锁定检查；非周期分量的对数公式与批量版本一致。原始上游文件、原v5和批量音质基准均未改。中途编译发现重复相位函数，已修正生成器，最终生成源SHA `93fc89e3e4c51e99d4eca94dd2d427133e5593e36f94a718634ebdd08210fad3`。

主机v7：50/250ms参数分批PCM一致；与批量B相同输入的输出，排除最终80ms结束处理后，PCM逐字节相同（RMSE0、最大误差0）。整段相关系数0.999939、RMSE0.000478，差异集中在结束处理：批量最终噪声区间归零，而持续合成通过填充参数排空尾部。不能将排除尾部的结果写成整段完全相同。`report/world_stream_full_host_20261012.json`。

扩展验证静音、低音/较高音启停和连续F0变化，均通过分批一致性、主体PCM与批量一致性、无削波；`build/check_world_stream_alignment.py`、`report/world_stream_alignment_checks_20261012.json`。该检查仍分析完整输入，尚未实时录放。

ARM v7参数5/25帧两种分批SHA均 `e8f943ad163d9aef7cda909d1530b4619c9e02d92e60e212b07c2f0106526fd4`，五秒总计算5.108642/5.120989秒，完整相位恢复后仍不具备实时余量。`report/board_world_stream_full_v7_20261012.log`。

## 快速F0与新增参数滑窗原型

探针新增独立 `fast4` / `stream5fast4` 实验，用DIO既有speed=4选项替代speed=1，其余参数不变。主机YIN中位数196.511Hz，基准196.539Hz，覆盖2.57/2.56秒，均无削波；不能据此认定听感无差异。ARM v8五秒总4.557772秒（RTF0.911554），F0估计0.166秒，较原约0.727秒减少，合成仍2.614秒。`report/world_stream_speed4_host_20261012.json`、`report/board_world_stream_speed4_v8_20261012.log`。未试听此配置，未替换优选B。

新增 `src/ps/world_sliding_probe.cpp`：30ms提交步长、160ms历史、40ms分析未来上下文；每个窗口估计F0，仅对新增帧及中值滤波邻居做StoneMask，谱包络/非周期分量只计算新增帧。单个持续合成器保留相位，16个参数所有者槽保障被库引用的数据生命周期；检查队列满、输出完整长度、有限值和削波。输入仍来自预读文件，但分析函数仅可读取规定窗口；还没有ALSA、生产者/消费者并行或PL处理。

主机原型完整生成五秒，YIN约195.361Hz、2.35秒覆盖，无削波。相比整段分析的2.56秒覆盖已有变化，需要单独听辨，不能假设滑窗听感与基准一致。主机分析块P95约2.25ms只适用于电脑，不代表ARM。原始日志 `report/world_sliding_native_20261012.log`；ARM v9已编译、正在准备板端预算。下一步先测分析阶段块耗时与合成阶段耗时，判断双核调度空间，再核对输出、准备一次音质对照；不能把文件串行总时间当作实际端到端延迟。

## 滑窗ARM预算与质量门槛

ARM v9（30ms步长）：五秒分析3.824476秒/合成2.651871秒，两个阶段RTF0.764895/0.530374，串行总6.477096秒。分析块P95 32.542ms、最大33.249ms，偶尔超出30ms周期，不能只看平均负载宣称实时。日志 `report/board_world_sliding_v9_20261012.log`，结构化 `report/world_sliding_budget_v9_20261012.json`。

新增独立hop40模式，参数历史/未来上下文、合成前视均不变。ARM v10（40ms步长）：五秒分析3.524103秒/合成2.648399秒，RTF0.704821/0.529680，串行总6.173072秒；P95 40.222ms、最大41.054ms。平均分析负载减轻，但块预算仍接近/略超周期，仍需实际并行调度、缓冲与持续负载测试。不存在已通过的实时录放或端到端延迟结果。日志 `report/board_world_sliding_v10_20261012.log`。

两种ARM输出均下载并核对传输SHA，归档 `data/registrations/source_20261011/world_sliding_comparison_20261012/sliding30_arm.wav`、`sliding40_arm.wav`。与相同源输入/相同参数的MinGW原型PCM逐字节一致，RMSE0，无削波。YIN分别195.361/195.730Hz、有声覆盖2.35/2.43秒；优选B约196.539Hz、2.56秒覆盖。`report/world_sliding_arm_agreement_20261012.json`。有声判断的变化不能仅用中位F0接近来替代听辨。

下一步23秒离线质量预览：目标→优选B→30ms滑窗→40ms滑窗，每段5秒、中间1秒静音。同一输入者五秒裁剪，共用RMS目标0.085816，峰值0.904175、无削波。生成器 `build/create_world_budget_comparison.py --sliding`，文件与manifest在 `data/registrations/source_20261011/world_sliding_comparison_20261012`。输出来自串行计算文件，不是真实实时录放，不测延迟。暂停后恢复至今尚未播放新音频；本轮必须再次确认用户准备好。

准备的播放命令：

```sh
python3 /tmp/codex_world_20261012/play_voice_comparison_v3.py --base /tmp/codex_world_20261012 --manifest sliding_comparison_manifest_v1.json --audio sliding_comparison_v1.wav.gz
```

滑窗23秒对照、manifest和助手已上传，gzip 1,113,815字节、SHA `edcb6345217e1d8c2e739340248645640792593914a1c6a2f1bad9a77859e0d2`；WORLD许可证已放入暂存目录。板端压缩/解压SHA、助手语法及PCM均closed核对通过，日志 `report/board_world_sliding_comparison_staging_20261012.log`。四段实际WAV RMS约0.085798/0.085790/0.085791/0.085790，无削波。等待本轮明确准备确认，尚未播放。


2026-10-12最终暂停：23秒目标/批量B/30ms滑窗/40ms滑窗对照完成，用户确认都听到，三段转换差别不大，后两段可能略清晰。滑窗离线听辨通过，实时/身份相似度仍未验收。最后播放及mixer恢复返回0；用户要求休息后只保存本地文件，不再操作板卡。明日新对话先读根目录handoff_20261012.md，再核对板况，推进双核调度及持续负载；每次现场测试单独确认准备。
