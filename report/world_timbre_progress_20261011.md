# 2026-10-11 音色候选实验

用户听到17秒三段对照后确认：音色不像目标，更像单独升调，并带一点颤。基础F0校准成功不能作为目标音色验收。本轮不再反复用同一升调算法请求试听。

采用 [PyWORLD](https://github.com/JeremyCCHsu/Python-Wrapper-for-World-Vocoder) 0.3.5（独立目录 `build/generated/world_deps`），将F0、谱包络和非周期分量分开。源录音15秒，16kHz分析、5ms帧移、1024点谱；Harvest/StoneMask估计F0，在有声连续段内做5帧中值平滑。沿用实际Q16=108722。目标平均归一化对数谱仅用Track5～8拟合，Track9完全留出。全局谱平均会混入语音内容和麦克风差异，不能当作说话人身份模型。

候选采用共振峰频率轴缩放与低倒谱阶平均谱修正，拟合缩放1.15、使用强度0.65（实际频率轴缩放1.0975），功率修正限制±6dB，有声帧保持总谱功率，无声帧保持原谱；非周期分量保留源值。身份重合成、只改F0、改F0及谱包络分别保存。源/目标原始文件、现有PL位流与当前实时配方未改。

`build/create_world_comparison.py` 生成音频和完整版本/参数/哈希/耗时记录；`build/check_world_comparison.py` 独立YIN检查归档WAV。25项Python测试通过；YIN测得身份重合成116.395Hz、WORLD升调192.986Hz、音色候选193.114Hz，各有5秒以上有声覆盖，无削波。源分析约1.72秒，15秒音色合成约0.19秒；均是本机耗时，不代表ARM性能或实时延迟。数据在 `report/world_experiment_20261011.json`、`report/world_quality_20261011.json`。

23秒对照：目标5秒→旧升调5秒→WORLD升调5秒→WORLD音色调整5秒，各段之间1秒静音。后三段使用同一讲话片段，各段相同RMS目标与峰值上限，32kHz PCM16单声道，峰值0.6684，无削波。生成文件 `data/registrations/source_20261011/world_experiment/comparison.wav`；第三与第四段用于隔离音色调整效果，第二与第三段比较算法颤动/自然度。暂未进行新候选物理试听。

板端准备：COM14只读检查通过，PCM录放均closed，DMA设备存在。预定文件名 `world_comparison_v1.wav.gz`、`world_manifest_v1.json`、`play_voice_comparison_v2.py`，位于 `/tmp/codex_pl_control_20261011`。准备文件不播放。必须先问本轮是否准备好，收到明确回复后才运行：

```sh
python3 /tmp/codex_pl_control_20261011/play_voice_comparison_v2.py --manifest world_manifest_v1.json --audio world_comparison_v1.wav.gz
```

播放助手核对双SHA、检查PCM空闲、保存/恢复mixer，唯一目录保存日志。下一步由用户判断四段可听性、第三段颤动与第四段是否更接近目标；听辨通过后才评估实时迁移。重复启停无声故障及最终端到端量化延迟仍未解决。

上传完成：音频gzip 1,132,370字节，音频/manifest/助手均由上传工具核对SHA。电脑独立核对WAV为32kHz单声道PCM16、736000帧/23秒，压缩与解压SHA均一致。测试日志 `report/python_timbre_tests_20261011.log`。本轮尚未启动播放。

用户明确回复“准备好了，开始”后，已进行本轮23秒播放，助手与串口命令均返回0，完成目录 `/tmp/codex_pl_control_20261011/comparison_6777756168067`，日志 `report/board_world_comparison_20261011.log`。mixer恢复命令返回成功，ALSA仍打印既有UCM配置缺失提示。此处仅证明播放命令完成，实际可听性、颤动及音色相似度等待用户反馈；不得提前判定音色验收通过。

## 用户反馈与减轻厚重感的第二轮

用户反馈：“听到了，有一点但不是很明显，还是不太像，这次相比之前的会更厚重一些，而之前的显得灵动一些”。四段可听确认通过；相似度未通过；不将“有一点”解释为颤动消除已验收。

检查前一版平均谱修正（强度0.65后）：300～600Hz平均+3.35dB、600～1200Hz +1.27dB、1200～2400Hz +3.46dB，而2400～4000Hz仅+0.66dB。这可能解释偏厚听感，但不是已证明的因果。下一轮先隔离全局平均谱修正，避免在同一候选上反复盲调。

`build/create_world_comparison.py --variant light` 生成独立目录 `data/registrations/source_20261011/world_light_experiment`，保留原实验音频与记录。共振峰候选仅保留原频率轴缩放（实际1.0975），取消平均谱修正；减弱候选保持同一缩放，将功率修正上限±6dB降为±3dB，800Hz以下取消正增益、800～1200Hz平滑恢复，负修正保留。有声帧总谱功率仍保持，F0/非周期分量/有声边界处理一致，不使用Track9拟合。

23秒对照：目标→上一轮偏厚候选→只调整共振峰→减弱谱修正，每段5秒、中间1秒静音、同一讲话截段与响度目标。YIN共振峰候选193.211Hz、减弱候选193.126Hz，各超过5秒有声覆盖；WAV无削波，对照峰值0.6924。数据 `report/world_light_experiment_20261011.json`、`report/world_light_quality_20261011.json`。这些检查不能证明自然度或说话人相似度。

预定板端音频 `world_light_comparison_v1.wav.gz` 与manifest `world_light_manifest_v1.json`，复用已校验的 `play_voice_comparison_v2.py`。先等待本轮明确准备回复，再执行：

```sh
python3 /tmp/codex_pl_control_20261011/play_voice_comparison_v2.py --manifest world_light_manifest_v1.json --audio world_light_comparison_v1.wav.gz
```

若只调整共振峰也仍不像目标，则不能继续把平均谱/EQ微调当作完整目标声线转换；应先评估表达/音质信息缺失及更完整模型在Zynq资源上的可行性。两轮目前都仅离线实验，不能覆盖实时基线。

第二轮文件准备完成：gzip 1,130,741字节，SHA256 `7d888f6a094cf52a86fb612d1e2e8392b47f76331399bff0920b44f9115e4603`，manifest上传校验成功。板端独立核对压缩及解压SHA均通过、录放PCM均closed，日志 `report/board_world_light_staging_20261011.log`。未启动本轮播放，等待本轮明确准备确认。

第二轮播放：用户明确回复“准备好了，开始”后执行23秒对照，返回0；完成目录 `/tmp/codex_pl_control_20261011/comparison_7251903830522`，日志 `report/board_world_light_comparison_20261011.log`。mixer恢复命令成功，仍有既有UCM配置缺失提示。当前等待用户反馈，不将命令成功等同于可听性或音色验收。

## 第二轮反馈与候选选择

用户确认全部听到、厚重感明显减轻，“这一次比之前像很多，更接近女声”。仍有一点颤动，用户认为可能来自原始讲话；此原因未验证。追问第三与第四段差异后，用户回复“两段差不多，第四段声音会小一些”。两段已按相同RMS目标制作，但感知响度仍会随频谱变化，不强行解释为连接故障或处理增益错误。

先选择第三段（只调整共振峰，实际频率轴缩放1.0975、无平均谱修正），因为效果接近且处理更简单。这是初步听感改善，尚不能证明说话人身份相似度、完整实时转换或正式盲评通过。候选参数、波形SHA、验收边界保存在 `data/profiles/timbre_candidate_20261011.json`；现有实时PL配方不变。第二轮结束后PCM均closed、DMA设备仍在，日志 `report/board_world_light_final_state_20261011.log`。

下一步先测完整WORLD分析/共振峰调整/合成的Cortex-A9离线预算，不播放、不采集、不加载新PL。源码使用与已试听依赖相同的PyWORLD 0.3.5源码包，PyPI SHA核对通过；官方GitHub clone遇连接重置后改用官方发布源码。源码包SHA `1b93e53cddb67a0e4faa34d6cf919ac6c662feb1c8c0ed901d71b595ab396aa3`，清单 `build/generated/world_source_v035/source_manifest.json`。

计算探针 `src/ps/world_budget.cpp`、构建 `build/build_world_budget.ps1`，SDK ARM GCC 7.3.1、-O3、Cortex-A9/NEON、静态链接，未使用fast-math。独立输出 `build/generated/world_budget`，含WORLD许可证。输入为源录音4～9秒的16kHz PCM16裁剪，不修改源文件。分别测Harvest与DIO版本的F0、修正、谱包络、非周期分量、共振峰调整和合成耗时；DIO是预算替代实验，尚未试听。五秒整段耗时即使小于五秒也不能证明流式低延迟。

## ARM计算预算结果

实板分别处理同一5秒裁剪，录放PCM未打开，未修改PL或mixer；两个进程均正常退出，输出有限且未削波。原始日志 `report/board_world_budget_harvest_20261011.log`、`report/board_world_budget_dio_20261011.log`，结构化结果 `report/world_arm_budget_20261011.json`。

| 阶段 | Harvest版本/秒 | DIO版本/秒 |
| --- | ---: | ---: |
| F0估计 | 23.845 | 0.736 |
| StoneMask及门限/平滑 | 0.544 | 0.384 |
| CheapTrick谱包络 | 1.403 | 1.404 |
| D4C非周期分量 | 3.550 | 2.751 |
| 共振峰调整 | 0.356 | 0.269 |
| 合成 | 2.444 | 2.542 |
| 总计算 | 32.142 | 8.084 |
| 实时因子（计算秒/音频秒） | 6.428 | 1.617 |

当前单线程完整流水线均不满足实时，因此只保留为离线音色证据，不能直接接入现有PL实时路径。DIO虽显著加速F0，但仍需优化其余分析/合成阶段，并评估双核调度、PL加速和分块连续性；本次五秒整段并未测试这些能力。DIO与Harvest有声帧分别581与771，质量不能由更快或帧数推定，必须先核对波形参考并试听。

板端两个输出已下载并验证传输SHA。`build/check_world_budget.py` 以同一16kHz五秒输入、同版PyWORLD、同F0门限/中值平滑/谱包络缩放计算电脑参考：Harvest相关系数0.9999999476、RMSE0.0000183902；DIO相关系数0.9999999450、RMSE0.0000184016，无削波，数值一致性通过。差异包含WORLD原生WAV写入的截断/32767量化与参考浮点的差别。证据 `report/world_budget_agreement_20261011.json`。此处不证明DIO听感通过。

另建v2计算探针，保留v1二进制和实测日志：可选`fast`参数，将帧间隔改为10ms，连续有声段中值平滑改3帧（约30ms），谱包络与非周期分析并行，其余参数保持。使用`-pthread`，各分析调用有独立输出/FFT和随机状态，上游源码未修改。先测五秒及短块预算，再做v2数值比对；双核处理及参数帧减少是计算实验，尚未试听和流式验收。

v2实板在线程创建时抛出`std::system_error`，退出134，没有有效速度结果；日志 `report/board_world_budget_dio_fast_20261011.log`。v3改用直接POSIX pthread接口，明确报告创建/等待的错误码，避免C++线程异常掩盖失败。v2失败原因尚未唯一定位，不能只凭改接口就声称线程库问题已修复。构建 `build/build_world_budget.ps1 -BinaryName world_budget_v3`，v1/v2文件和证据保留。

## v3速度实验与下一轮质量门槛

POSIX pthread版实板正常退出：同一五秒输入，DIO 0.735秒、修正0.199秒、谱包络0.689秒和非周期分量1.393秒并行、共振峰0.136秒、合成2.531秒，总5.003886秒（RTF1.000777）。两个并行阶段的单项时间不能再相加当作总墙钟时间。对比原DIO总8.084秒有改善，但仍无I/O及分块重叠余量；`report/board_world_budget_dio_fast_v3_20261011.log`。

另测0.25/0.5秒裁剪：计算0.224/0.429秒、RTF0.896/0.857，各有声帧10/15。这两段有声比例较低，不能替代五秒代表性负载或推定全天稳定。整块积累与计算会产生额外延迟，本次未完成跨块连续重构。日志 `report/board_world_budget_short_v3_20261011.log`。不得宣称实时验收通过。

v3输出已下载，电脑10ms/3帧平滑参考相关系数0.999987713、RMSE0.000214608，无削波，达到本轮数值一致性阈值（相关系数≥0.999、RMSE≤0.001）。包括初版的三组结果在 `report/world_budget_agreement_20261011.json`。v3当前仅是值得进一步评估的速度候选；仍有质量与流式调度门槛。

下一轮23秒试听文件已生成 `data/registrations/source_20261011/world_budget_comparison`：目标→上一轮认可的Harvest共振峰候选→ARM DIO 5ms→ARM DIO 10ms并行版本，每段5秒、中间1秒静音。后三段相同讲话截段，共振峰缩放及F0比例相同；认可候选在完整15秒录音内分析，ARM两段按5秒裁剪独立分析，存在边界上下文差异，不能把第二与第三段的全部差异只归因于F0估计器。第三与第四段共用相同裁剪上下文。

制作时为四段选择同一个可满足峰值余量的RMS（插值前0.08436），避免某段因单独峰值限幅而额外降低增益；仍不能保证不同频谱的感知响度完全一致。对照峰值0.90007、无削波。生成器 `build/create_world_budget_comparison.py`，SHA与增益在manifest。下一轮需用户单独准备确认后才可播放：

```sh
python3 /tmp/codex_pl_control_20261011/play_voice_comparison_v2.py --manifest world_budget_comparison_manifest_v1.json --audio world_budget_comparison_v1.wav.gz
```

这轮用于决定快速版本是否值得继续优化，不是实时试听或延迟测量。当前PL实时基础升降调链路、现有注册配方均未改。

快速版本对照准备完成：gzip 1,112,923字节，SHA `7264f1a28e4f4146080a224ada8bf6f1de1f475582b6fbd3c2e02a2a14418f02`，manifest上传成功；板端压缩/解压双SHA通过，录放PCM均closed、DMA设备在，日志 `report/board_world_budget_comparison_staging_20261011.log`。WAV四段实际RMS 0.0843425、0.0843162、0.0843329、0.0843345，电平差异小于0.04%，无削波。未开始播放，等待用户本轮明确准备确认。

用户本轮明确回复“准备好了，开始”后，快速版本23秒质量对照已完成，返回0；目录 `/tmp/codex_pl_control_20261011/comparison_9234524720087`，日志 `report/board_world_budget_comparison_20261011.log`。mixer恢复命令成功，既有UCM配置缺失提示仍在。等待本轮可听性、音色、自然度及颤动反馈，不提前验收快速版本。

## 今日停止与下次入口

最终用户反馈：“都听到了，相比第二段没有变差，我觉得第四段会好一点点。然后今天就到这里，我要休息了”。四段可听、快速A/B整体音质未变差，第四段（DIO10ms/并行谱分析）略优；并未单独确认所有颤动已消除，也不是正式身份相似度盲评。

保留第四段作为下一步优先速度候选，参数与波形SHA保存至 `data/profiles/timbre_candidate_fast_20261011.json`，不覆盖原Harvest音色参考或现有PL实时配方。五秒计算5.004秒仍不具备实时余量；后续先处理计算/调度余量与跨块连续合成，不能仅缩录放缓冲就宣称实时音色完成。

用户明确要求今天停止，后续仅保存本地文档和候选归档，没有再次调用串口、播放、录音或改PL。最后播放助手返回0、mixer恢复命令成功；停止后的PCM状态未重新查询。临时板端目录会随断电消失，已有启动文件未改。用户恢复工作后先读根目录指引，再核对是否重启/实际板况；任何新现场测试均重新询问准备状态。
