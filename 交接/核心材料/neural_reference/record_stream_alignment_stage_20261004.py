from pathlib import Path
import json, re, hashlib

PROJECT=Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020')
OUT=PROJECT/'board_budget_20261004'
ALIGN=Path('D:/总进度/目标人物分析/小模型监督对齐试验_2026-10-04')

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

geometry=read(OUT/'full_llvc_geometry/geometry_profile.json')
stream=read(OUT/'causal_stream_audit/decision.json')
quant=read(OUT/'encoder_quantization/decision.json')
alignment=read(ALIGN/'decision.json')
screen=read(ALIGN/'free_acoustic_screening.json')
assert all(r['hanzi_matches_input'] and r['pinyin_unchanged'] for r in screen['cases'])

folder=PROJECT/'pl_kernels/gemm_s8_128'
rpt=folder/'gemm_s8_hls/solution1/sim/report/verilog/result.transaction.rpt'
transactions=[dict(index=int(i),latency=int(l),interval=int(v) if v!='x' else None) for i,l,v in re.findall(r'transaction\s+(\d+):\s+(\d+)\s+(\d+|x)',rpt.read_text())]
assert len(transactions)==16
lat=[r['latency'] for r in transactions]
interval=[r['interval'] for r in transactions]
mapping=[dict(group='encoder_pointwise',shape=[512,512,13],calls=8,transaction=2),
         dict(group='two_attention_query_and_output_projections',shape=[256,256,13],calls=4,transaction=7),
         dict(group='two_attention_key_and_value_projections',shape=[256,256,26],calls=4,transaction=3),
         dict(group='feedforward_expand',shape=[256,512,13],calls=1,transaction=4),
         dict(group='feedforward_contract',shape=[512,256,13],calls=1,transaction=5)]
for r in mapping:
    r['rtl_latency_cycles_per_call']=lat[r['transaction']]
    r['rtl_interval_cycles_per_call']=interval[r['transaction']]
    r['macs']=r['calls']*r['shape'][0]*r['shape'][1]*r['shape'][2]
cycles=sum(r['calls']*r['rtl_interval_cycles_per_call'] for r in mapping)
mapped_macs=sum(r['macs'] for r in mapping)
timing=(folder/'gemm_s8_ooc_timing.rpt').read_text()
assert 'All user specified timing constraints are met.' in timing
assert 'There are 0 pins that are not constrained for maximum delay.' in timing
route=(folder/'gemm_s8_ooc_route_status.rpt').read_text()
assert re.search(r'nets with routing errors.*:\s+0',route)
evidence=dict(status='standalone_stream_and_hardware_prototypes_pass_training_review_pending',
    geometry_profile=geometry,online_stream_audit=stream,encoder_quantization_audit=quant,
    preferred_prototype='gemm_s8_128',model_dense_operator_mapping=mapping,
    rtl_dense_interval_cycles=cycles,clock_mhz=100,ideal_rtl_dense_ms=cycles/100000,
    unallocated_chunk_budget_ms=13-cycles/100000,
    remaining_tracked_macs=geometry['tracked_macs_per_chunk_upper_bound']-geometry['static_label_macs_per_call']-mapped_macs,
    dense_weight_bytes_per_chunk=sum(r['calls']*r['shape'][0]*r['shape'][1] for r in mapping),
    standalone_resources=dict(lut=17375,ff=10463,bram36_equivalent=73,dsp=4),
    ooc_setup_wns_ns=.407,ooc_hold_whs_ns=.053,
    ooc_unconstrained_input_ports=198,ooc_unconstrained_output_ports=189,
    ooc_hd_clk_src_unset=True,actual_ddr_stalls_not_modeled=True,
    omitted_budget=['CPU quantize/dequantize/bias','normalization','depthwise and input/output convolutions','attention score/softmax/value reduction','state moves','DDR contention','driver/control','audio IO'],
    target_student_trained=False,target_student_identity_approved=False,board_deployed=False,
    sd_card_changed=False,official_audio_project_version='2022.2',installed_cad_version='2018.3',
    full_system_version_compatibility_unresolved=True,
    supervision_alignment_pilot=alignment,alignment_screening=screen,
    human_alignment_acceptance=False,training_pairs_approved=False,
    next_required_user_action='Listen to raw teacher vs rhythm-aligned teacher; compare first/second clarity and naturalness.',
    running_jobs=0,
    file_evidence=[dict(path=str(p),sha256=sha(p)) for p in [
        folder/'gemm_s8.cpp',folder/'gemm_s8.h',folder/'test_gemm_s8.cpp',rpt,
        folder/'gemm_s8_ooc_timing.rpt',folder/'gemm_s8_ooc_utilization.rpt',folder/'gemm_s8_ooc_route_status.rpt',
        folder/'gemm_s8_ooc_routed.dcp']])
(OUT/'stream_gemm_alignment_stage_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')

readme='''# 可变尺寸 signed8 矩阵模块（128并行乘法）

这是待整合的独立计算模块，不是完整变声系统。固定512行跨度，支持128/256/384/512输入和输出通道、1～26帧，输入和权重按低字节优先打包为64bit，输出为signed32点积。每次重装活动权重，非活动输出不改写；非法尺寸返回错误且不写输出。缩放、偏置、激活、归一化和层间状态由调用方负责，尚未实现完整板载运行。

## 验证

- Vivado HLS 2018.3，xc7z020clg400-2，100MHz。
- C与RTL各40832个输出逐项一致，含矩形矩阵、26帧上下文、正负极值、形状切换、8类非法参数。
- 单独布局布线完成，setup WNS +0.407ns、hold WHS +0.053ns，0路由错误。
- 17375 LUT、10463 FF、73 BRAM36等效、4 DSP。乘法主体实际映射LUT，不能按128个DSP描述。
- 198输入和189输出未设外部延迟，HD.CLK_SRC未设置；独立检查不能代替PS/DDR/音频全工程时序。

## 模型映射预算

以LLVC官方默认结构为几何参照，18次主要矩阵调用的RTL仿真启动间隔总计852428周期，即100MHz下8.52428ms。剩余4.47572ms只是尚未分配的理论余量。仿真为理想AXI内存，不能作为板上持续实时或端到端延迟实测。卷积、注意力分数/softmax、归一化、量化、状态、驱动、DDR仲裁与音频IO都还需计入。

当前仅对官方其他人物的预训练LLVC做了流式与数值审计；用户目标人物的学生模型尚未训练、尚未试听、尚未部署。已认可的CosyVoice3声音是电脑教师参照，不能把本模块通过当作目标变声完成。

## 复现

在本目录运行 `D:\\Vivado\\Vivado\\2018.3\\bin\\vivado_hls.bat -f run_hls.tcl`，然后运行 `D:\\Vivado\\Vivado\\2018.3\\bin\\vivado.bat -mode batch -source check_ooc_timing.tcl`。完整文件哈希、周期及限制见 `../../board_budget_20261004/stream_gemm_alignment_stage_evidence.json`。
'''
(folder/'README.md').write_text(readme,encoding='utf8')

report=f'''# 本轮结果：流式接口、计算预算与训练参照

目标仍是任意未登记说话人→同一目标人物，低延迟连续麦克风输入/音箱输出，核心在野火7020。

已认可的电脑教师音色保留。本轮没有改SD卡、没有要求上电，也没有把官方其他人物的LLVC声音当作你的目标。

完成真实录音分块接口验证，3种分块方式与官方输出逐采样完全一致，第一块需224个16k采样（14ms输入可用性），不等于实际端到端延迟。完成64/128并行可变尺寸矩阵模块；128版主要矩阵仿真预算8.52428ms/13ms块，独立100MHz时序通过，全系统与DDR仍未验证。官方完整模型3258720参数；只量化8个编码器点层后，单段真实语音波形SNR约28dB，这是数值诊断，不能验收音色和咬字。

## 需要一次必要试听

原录音与目标合成音节奏不同，直接成对训练会让模型在错误时刻学习错误音节。为此先准备两名开发集真人的对齐参照，未使用4名保留说话人训练/对齐。采用约60ms间隔CTC内容标记与保持音高的节奏调整；这是粗对齐，不是精确音素边界，也不是最终训练集。

初版开头拉伸导致机器拼音“这”从zhe4变zhi3，失败波形和检查记录完整留在 `pre_padding_diagnostic`。修正后用补停顿保留首字/尾字时长，两段自由汉字识别一致、拼音序列与调整前一致。识别器已知会漏掉真实发音错误，因此不能自动通过。

试听文件：{alignment['preview_path']}

先播放原目标合成声3.6秒，停0.3秒，再播放对齐后的同一目标声4.11秒。台词：“这是第一次国家层面应用人脸识别技术”。这两段都来自同一个固定目标参考；第二段只调整节奏，尚不是小模型转换输出。

请判断第二段有没有比第一段明显更糊、拖字、金属声或不自然，尤其“这是”和“识别”。自然度可以保留才继续更细的对齐与小模型试训。两段内容机器筛查通过不等于全部目标音色/发音人工验收。两对粗CTC标记最大误差分别为 {screen['cases'][0]['coarse_ctc_landmark_max_error_seconds']:.3f}s、{screen['cases'][1]['coarse_ctc_landmark_max_error_seconds']:.3f}s，不能声称13ms精确标签。

下一步依听感决定是否保留节奏处理，再做更细监督对齐、小模型试训与未见说话人验证；完整音频工程2022.2和现有工具2018.3的整合兼容仍待解决。当前所有后台作业已结束，用户不需开板或补录。
'''
(ALIGN/'本轮结果与必要试听.md').write_text(report,encoding='utf8')

header='''## 最新状态：计算原型通过，等待一次训练参照试听（2026-10-04）

用户允许持续执行直到需要协助/试听。本轮完成LLVC完整结构分析（3258720参数、13ms块）、严格加载官方预训练模型的真正分块接口验证（不同输入分块逐采样一致、224采样14ms首块输入要求、EOF/未来输入隔离通过）。官方LLVC声音不是用户目标，当前目标学生没有训练、没有验收，不可将其演示为完成变声。

完成可变尺寸64/128并行signed8矩阵模块。128版C/RTL各40832输出一致、8类非法输入通过；独立100MHz setup/hold +0.407/+0.053ns，17375LUT、10463FF、73BRAM36等效、4DSP。18次主要矩阵仿真启动间隔总预算8.52428ms/13ms块，未计其余运算/实际DDR/驱动/音频，不是实板实时成绩。官方其他人物模型仅编码器8点层W8A8数值诊断：单段波形SNR约28dB，不接受目标音色/咬字。完整2022.2音频工程与2018.3工具整合仍未解决。

训练参照节奏对齐先做2名开发集真人，保留说话人未使用。初版首字被拖长、机器zhe4→zhi3警告，已保存失败；补停顿修正后两段汉字、拼音与原教师一致，仍不能代替听感。粗CTC标记约60ms，尚非精确13ms监督。当前需要试听约8秒：先原目标合成声，再同台词节奏对齐后的目标声；确认第二段是否更糊、拖字或不自然，尤其“这是/识别”。这是训练参照审核，尚非学生输出；不得直接据机器通过开大规模训练或宣称实时目标完成。

试听/报告目录：D:\\总进度\\目标人物分析\\小模型监督对齐试验_2026-10-04。完整证据：D:\\Tools_FPGA\\workspace\\voice_conversion_zynq7020\\board_budget_20261004\\stream_gemm_alignment_stage_evidence.json。所有作业结束、板卡/SD未改变，不需要上电/新录音。下一步：听感通过后做更细对齐与小模型试训、保留说话人回归、完整板卡整合。当前任务：确认节奏对齐没有破坏自然度和咬字。

'''
for path in [PROJECT/'PROJECT_STATUS.md',Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md')]:
    old=path.read_text(encoding='utf8')
    path.write_text(header+old,encoding='utf8')
print('RECORDED dense_interval_cycles=',cycles,'remaining_macs=',evidence['remaining_tracked_macs'],flush=True)
