# 固定男声监督与教师依赖盘点

任务PS-20261021-10，Hardware-A，2026-10-27。基准7b9bd19；本次为只读资产诊断，不是新训练轮或五门验收。

## 已核实证据

- 固定男声录音1～3逐件SHA-256和字节数匹配冻结清单；未读取录音4/5和Track9音频。
- 现行公共训练192对、888.1089375秒，验证8对、46.1948125秒。400个源/教师float32文件的SHA和样本数全部匹配manifest。所有条目均为公共SSB身份/文件名，Fixed-Male标记条目为0。此项核验不是全盘解码音频去重；没有发现固定男声的内容配对目标监督。
- 历史teacher_content_timing报告48条，与当前训练192条和验证8条的文件名交集均为0。不能引用该报告的低平均时移来证明现行训练配对音素对齐。近期8句能量包络零时移诊断仍有效，但不等于局部音素对齐。
- 历史期望位置缺少CosyVoice_reference源码、模型metadata/manifest及全部6个关键模型/配置文件。定向rg检索项目与D:/Tools_FPGA未发现llm.pt、flow.pt、hift.pt；不声称全机所有目录都已穷尽。
- 历史make_expanded_student_pairs_20261006.py使用源语音token的native VC，不是ASR转TTS；冻结模型revision为29e01c4e8d000f4bcd70751be16fa94bf3d85a18。不能用不对应内容的目标WAV直接监督男声。

## 恢复可行性与下一动作

官方Hugging Face API只读查询成功；当前revision与历史一致（29e01c4e8d000f4bcd70751be16fa94bf3d85a18）。llm/flow/hift/tokenizer/campplus五个主要文件合计约4.43GB十进制，另需配置、tokenizer资源与源码/依赖。本机RTX5060 Laptop总显存8151MiB、查询时空闲7555MiB；D盘空闲约98.1GB。这些只是下载/硬件可用证据，不证明CUDA算子、依赖或教师推理已通过。

下一步在D盘单一任务目录恢复精确revision的官方教师资产与源码，记录逐件SHA并完成只用训练录音的离线烟测。先审计教师对录音1～3的内容保留，再决定是否作为源专用配对监督。不得直接运行历史脚本：其含失效D盘绝对路径、环境修改及旧诊断素材引用。恢复教师不重开Seed路线，不访问锁定素材、不播放、不操作板卡。保留原Round108总上限。

本次诊断支持优先修复监督覆盖，尚未证明缺少源专用监督就是当前CER失败的唯一原因。现有公共学生对两位公共验证输入同样损坏内容，后续仍需定位预测环节。

## 复现

在任务分支检出根目录执行：

```powershell
& 'C:/Users/World/AppData/Local/Python/pythoncore-3.12-64/python.exe' build/audit_fixed_male_supervision_20261027.py --asset-root C:/Users/World/Desktop/2026_FPGA --output report/fixed_male_supervision_inventory_20261027.json
```

退出0，结果JSON记录脚本/输入manifest/历史时序报告SHA。GPU与磁盘为本次终端查询快照；官方API查询地址为https://huggingface.co/api/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512?blobs=true 。无训练、合成、播放、板端或听感结论。
