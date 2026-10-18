from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET
ROOT=Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020');P=ROOT/'pl_kernels/pointwise_s8';B=ROOT/'board_budget_20261004';Q=Path('D:/总进度/目标人物分析/固定人物多说话人中文回归_2026-10-04')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=read(B/'wildfire_spec_extracted.json');manifest=[]
for name in ['pointwise_s8.h','pointwise_s8_packed.cpp','test_pointwise_s8.cpp','run_hls_packed.tcl','check_ooc_timing.tcl','report_ooc_min_max.tcl','pointwise_s8_packed_hls/solution1/syn/report/pointwise_s8_csynth.rpt','pointwise_s8_packed_hls/solution1/sim/report/pointwise_s8_cosim.rpt','pointwise_packed_ooc_min_max_timing.rpt','pointwise_packed_ooc_utilization.rpt','pointwise_packed_ooc_route_status.rpt','pointwise_packed_ooc_routed.dcp']:
 path=P/name;manifest.append(dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size))
timing=(P/'pointwise_packed_ooc_min_max_timing.rpt').read_text();assert 'All user specified timing constraints are met.' in timing
cosim=(P/'pointwise_s8_packed_hls/solution1/sim/report/pointwise_s8_cosim.rpt').read_text();assert re.search(r'Verilog\|\s*Pass',cosim)
assert 'ALL PASS checked_outputs=30720' in (P/'hls_packed_console.log').read_text(errors='replace')
d=dict(status='standalone_signed8_matrix_primitive_csim_rtl_ooc_checked',device='xc7z020clg400-2',spec_source=meta['path'],spec_sha256=meta['sha256'],spec_pages=[9,11,12],board_ddr_bytes=1073741824,clock_target_MHz=100,wns_ns=.611,whs_ns=.068,unconstrained_internal_endpoints=0,unconstrained_external_input_ports=196,unconstrained_external_output_ports=189,hd_clk_src_unset_warning=True,checks_cover='OOC internal paths only; no integrated AXI/DDR clocks, audio, Linux driver or board validation.',placed_resource=dict(LUT=7456,FF=5925,BRAM36_tiles_equivalent=69,DSP=0),csim_and_rtl_checked_outputs=30720,invalid_frame_calls=2,packed_weight_load_achieved_II=1,previous_weight_load_II=8,old_synthesis_max_cycles=323666,new_synthesis_max_cycles=94290,rtl_test_max_cycles=94409,eight_layer_pointwise_only_ideal_rtl_ms=94409*8/100000,frame_audio_budget_ms=13,host_board_fp32_neon_baseline_ms=234.346,fp32_to_signed8_quality_validated=False,speedup_ratio_claimed=False,contains_learned_voice_model=False,contains_bias_or_layernorm=False,exact_signed8_accumulator_bits=32,integration_done=False,board_deployed=False,active_jobs=0,artifacts=manifest)
save(B/'hardware_budget_and_operator_evidence.json',d)
(P/'README.md').write_text('''# Signed8 pointwise accelerator prototype

Purpose: evaluate the512-channel pointwise bottleneck already measured on the ARM board, before committing a small causal voice model. This is a matrix primitive with synthetic validation weights, not a trained voice converter.

Final checked source: `pointwise_s8_packed.cpp`. `pointwise_s8.cpp` preserves the first byte-banked design for comparison. Both versions pass C/RTL checks; the first weight loader achieves II8, the packed64-bit loader II1.

Contract:512 input and512 output channels,1–13 frames per call. Matrix layout is W[input][output], packed8 signed bytes per64-bit word, low byte first. X[frame][input] uses the same packing. Y[frame][output] is an exact signed32 sum. No bias, activation, normalization, output requantization or learned weights. Invalid frame counts0/>13 return1 without writing output. Repeated calls load a new complete weight matrix. Host inputs require packed buffers and Linux DMA/cache-coherency support not yet implemented.

Reproduce with local Vivado HLS2018.3: run `run_hls_packed.tcl`, which performs C simulation, synthesis and Verilog co-simulation. Then Vivado batch runs `check_ooc_timing.tcl` and `report_ooc_min_max.tcl`. Outputs remain in this D-drive directory.

Validation:30720 exact outputs per C and RTL test suite, including zero, both signed8 extrema, randomized mixed signs, partial blocks and two invalid calls. Worst positive sum8,388,608 needs more than signed24; signed32 accumulation is used. Verilog co-simulation passes. At100MHz, max tested call94409cycles~0.94409ms; multiplying by8 gives~7.55272ms for eight pointwise-only calls under the RTL AXI memory model. This is not physical DDR timing or a complete inference result.

Placed/routed OOC resource:7456LUT,5925FF,69 BRAM36-equivalent tiles,0DSP. Both setup and hold checks for internal paths pass (WNS+0.611ns,WHS+0.068ns).196input/189output ports have no input/output-delay constraints; HD.CLK_SRC is unset. The real PS clock tree, AXI arbitration and vendor audio peripherals are absent. Do not advertise this as timing closure for the whole board.

Current kernel uses LUT multipliers, not the220 device DSP units. The retained tool-generated resource reports are authoritative. Original invalid Mul_DSP directive was replaced with the locally supported Mul core; no DSP usage is inferred from that pragma.

Remaining: parameterize matrix shapes for256-channel projections and attention; measure the full candidate geometry; train/verify causal target voice model; perform quantization-quality checks; add driver/cache handling; rebuild and time the complete audio design; test physical latency and multiple live speakers. The existing official project is2022.2 while installed tools are2018.3, so integration requires a deliberate compatible rebuild or matched tools, not automatic project downgrade. No SD/board writes were made.
''',encoding='utf8')
rows=read(Q/'evaluation_items.json');checks=read(Q/'free_hanzi_and_pinyin_screening.json')['files'];chars=sum(len(re.sub(r'[^\u4e00-\u9fff]','',r['publisher_text'])) for r in rows)
assert len(rows)==6 and len({r['speaker_id'] for r in rows})==6
for r in rows:assert sha(Path(r['path']))==r['sha256']
qc=dict(status='six_real_speakers_fixed_target_text_pipeline_regression_complete',speakers=6,male=3,female=3,reference_characters=chars,source_asr_character_ed=sum(r['asr_character_edit_distance'] for r in rows),generated_vs_actual_text_character_ed=sum(r['character_edit_distance'] for r in checks),actual_source_asr_reused_not_timed_end_to_end=True,source_speaker_registration=False,target_reference_unchanged=True,no_training=True,no_source_or_publisher_text_rewriting=True,automatic_phonetic_acceptance=False,remaining_pinyin_warning='SSB0316 空着: zhuo2 rather than expected contextual zhe5; existing warning persists.',timbre_naturalness_of_all6_not_human_accepted=True,frame_alignment_for_student_training=False,board_deployed=False,causal_streaming=False,active_jobs=0)
save(Q/'decision.json',qc)
(Q/'多说话人检查结果.md').write_text(f'''# 固定目标人物、多说话人文字路线回归

6名AISHELL-3真人说话者，3男3女，保持同一个模型和Track6前8秒参考，无输入者登记、无训练。均使用此前对各原始文件实际声学识别的原样文字，并核对原文件SHA；本轮复用识别结果，不冒充现场识别计时。只对上下文字典判为bie2的别使用用户反馈改善的官方拼音控制；别扭/别拗保守不加控制，其中别拗暴露了字典回退不可靠。

6句共{chars}汉字。源识别对发布者文本的编辑差异0，生成后的自由Hanzi识别对实际输入文字的编辑差异0。只有在这个小诊断集合上成立；该识别器对别的听感有已知盲点，同一家族声学检查存在关联偏差。空着在SSB0316的拼音仍给出zhuo2警告，不能宣布中文咬字全面通过。所有6句的新音色/自然度未单独人耳验收；无需把每句都交给用户听。

②仍保留为用户认可的音色/自然度基准；同一句原③与别字控制版用户反馈后半段更好。新6句用于跨输入者内容检查，尚不构成任意输入者现场实时证明。文字路线生成节奏与输入不同，不能直接把这些音频当作按帧对齐的LLVC监督对。小因果学生必须解决对齐/内容监督、中文覆盖与量化后的音质，而不是把电脑大模型直接写进SD卡。

全部作业结束。板卡没有上电要求或SD修改。后续推进小因果模型的计算预算与矩阵接口尺寸。
''',encoding='utf8')
header=f'''## 最新工程状态（2026-10-04；覆盖历史待试听）

用户认可②音色/自然度，之后确认原③对照的别字控制版“后半段更好”，保留该局部改动。已做上下文输入适配并保护别扭/别拗，原始识别文字不偷偷改写。6真人说话者（3男3女）同模型/同目标参考、无输入者登记，{chars}汉字源ASR和生成Hanzi检查均0编辑；仅小样本内容检查，空着的zhuo2警告保留，全部音色/发音并未人耳通过。

完成7020 signed8矩阵原型：C/RTL各30720输出一致；改成64bit权重存储解决II8瓶颈，单层RTL仿真最慢94409周期，100MHz下8层点计算约7.553ms，非完整模型/实板DDR时间。独立布局布线使用7456LUT、5925FF、69BRAM36等效、0DSP，内部100MHz setup/hold通过（+0.611/+0.068ns）。196输入/189输出时序未约束，HD.CLK_SRC未设；完整PS/音频工程尚未整合。规格书确认1GB DDR、220DSP，现有大教师不能原样板载；模型压缩/训练/量化质量与因果输入仍未实现。官方工程2022.2、安装2018.3的集成兼容问题保留。

下一步：扩展矩阵尺寸、检查小因果模型全算子预算与监督对齐；再做量化和完整音频整合。当前不需用户开板/录音/再逐句听。所有作业结束，无SD/板卡修改。详见 `D:\\Tools_FPGA\\workspace\\voice_conversion_zynq7020\\pl_kernels\\pointwise_s8\\README.md` 与 `D:\\总进度\\目标人物分析\\固定人物多说话人中文回归_2026-10-04\\多说话人检查结果.md`。

'''
for f in [Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),ROOT/'PROJECT_STATUS.md']:f.write_text(header+f.read_text(encoding='utf8'),encoding='utf8')
print('HARDWARE AND SIX SPEAKER EVIDENCE SAVED',chars)
