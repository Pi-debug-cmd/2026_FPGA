from pathlib import Path
import json,statistics
OUT=Path('D:/总进度/目标人物分析/固定人物缓存与流式测量_2026-10-04');W=OUT/'预热复测'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
a=read(W/'warmed_frontend_repeats.json');b=read(W/'benchmark_results.json');r=read(W/'cache_reproducibility.json');p=read(W/'tokenizer_prefix_future_context_probe.json');m=read(W/'frontend_and_resources.json')
uncached=statistics.median(x['uncached_frontend_seconds'] for x in a);cached=statistics.median(x['cached_source_only_seconds'] for x in a)
tts=next(x for x in b if x['label']=='actual_asr_cached_text_stream');native=next(x for x in b if x['label']=='native_cached_stream')
d=dict(status='measured_output_stream_only_input_noncausal',warmed_uncached_frontend_median_seconds=uncached,warmed_cached_frontend_median_seconds=cached,reference_work_saved_median_seconds=uncached-cached,exact_whole_audio_reproduced=r,tts_first_audio_seconds=tts['first_audio_with_preprocessing_seconds'],tts_playout_lateness_seconds=tts['playout_lateness_after_immediate_start_seconds'],native_first_audio_after_complete_input_seconds=native['first_audio_with_preprocessing_seconds'],all_time_is_pc_only=True,asr_and_capture_excluded=True,board_deployed=False,input_causal=False,reference_cache_allowed=True,source_enrollment=False,quality_acceptance=False,tokenizer_prefixes_not_stable=True,prefix_probe_does_not_isolate_normalization_from_neural_attention=True,active_jobs=0)
(OUT/'decision.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
text=f'''# 固定目标人物缓存与分块输出测量（2026-10-04）

这是电脑端工程测量，输入为预先完整录音，不是板卡现场延迟验收。

## 缓存正确性

参考人物的音频单位、频谱、身份向量可以提前提取。缓存张量129576字节，约126.5KiB。输入张量逐项相同；缓存与未缓存整段音频逐采样差异0，且原生VC和实际识别→生成都逐采样复现之前音频。

预热后3次测量，中位数：未缓存前端{uncached:.3f}秒，缓存后仅输入编码{cached:.3f}秒；省去约{uncached-cached:.3f}秒参考分析。不能把第一轮GPU预热差额全归因于缓存。

## 分块输出

电脑原生VC读取完整10.38秒录音后，缓存输入编码+第一次输出约{native['first_audio_with_preprocessing_seconds']:.3f}秒；之后0.84/2/4/3.56秒分块输出。该次计算事件模拟不积累欠播，但没有音箱播放或系统负载验证。

文字→目标音色：拿到完整识别文字后第一次输出约{tts['first_audio_with_preprocessing_seconds']:.3f}秒，4.68秒音频总生成{tts['render_seconds']:.3f}秒。立即开播会出现约{tts['playout_lateness_after_immediate_start_seconds']:.3f}秒的累计欠播。还未计语音识别、录入、传输、声卡缓冲。因此尚不能直接当低延迟连续讲话方案。

## 输入是否因果

同一真实输入仅提供前1/2/4/8秒，得到的离散音频单位与完整10.38秒对应前缀不同，差异也出现在末尾3单位之前；完整FLOAT容器副本单位逐项一致，排除了文件转换产生的波形差异。此试验只证明当前整体前端前缀不稳定；未隔离Whisper频谱全局归一化和神经模型上下文各自影响，不能单独断言哪个模块造成全部差异。不能简单把原生VC的整文件前端逐块调用就宣布因果实时成功。

## 资源与下一步

当前电脑教师仅LLM/flow/HiFT共{sum(m['component_parameter_counts'].values()):,}参数，另有约969MB的音频单位编码ONNX。这里没有板卡运行结果。参考缓存解决重复分析成本，不能把大型模型变成7020可部署模型。

②已获用户音色/自然度积极反馈，可保留为听感基准；③仍未完全认可。继续以官方拼音控制对照检查中文咬字，再确定有实际质量依据的教师；板卡方案需要另外实现并验证因果小模型、资源预算和现场端到端延迟。

无板卡/SD修改。测量任务已结束。完整数字见预热复测目录，不将ASR一致作为发音通过。
'''
(OUT/'测量结果与实时限制.md').write_text(text,encoding='utf8')
Q=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
f=read(Q/'human_feedback_20261004.json');f['followup_verbatim']='2就很好，3我感觉再改就得费很大劲了吧';f['clip2']['user_accepts_as_likeness_and_naturalness_baseline']=True;f['clip3']['fully_accepted']=False;(Q/'human_feedback_20261004.json').write_text(json.dumps(f,ensure_ascii=False,indent=2),encoding='utf8')
header='## 当前状态（2026-10-04，覆盖下面历史状态）\n\n用户认可新14秒对照②的音色和自然度：“2就很好”。②只是同台词文字合成基准，不代表任意现场输入或板卡通过。③真实输入识别→合成仍未完整认可。已完成缓存与预热复测，缓存前后整段音频逐采样相同；缓存省去约1.01秒参考分析。文字分块输出首音约1.81秒（不含识别和采集），生成4.68秒音频需5.19秒，立即开播累计欠播约1.20秒。输入音频前端前缀不稳定，不能直接当因果实时；7020神经部署仍未完成。正在运行官方拼音控制对照，检查这是别的发音，原版保留。详见 `D:\\总进度\\目标人物分析\\固定人物缓存与流式测量_2026-10-04\\测量结果与实时限制.md`。用户无需开板或补录。\n\n'
for file in [Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/PROJECT_STATUS.md')]:
 old=file.read_text(encoding='utf8');file.write_text(header+old,encoding='utf8')
print('PERFORMANCE REPORT AND HANDOFF UPDATED')
