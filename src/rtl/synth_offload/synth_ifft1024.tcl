# ============================================================================
# WORLD 合成卸载（增量 1）：1024 点 IFFT 核 out-of-context 综合
# 器件：xc7z020clg400-2（野火 Zynq-7020；-2 速度等级与板上一致）
# 时钟：clk 100 MHz（周期 10 ns），仅约束核内部时序，不涉及板上 I/O
# 用法（经 MCP）：source <此文件绝对路径>
# 产物：build/generated/pl_synth_offload/synth/ 下的报告与 DCP
# ============================================================================
set script_dir   [file dirname [info script]]
set project_root [file normalize [file join $script_dir .. .. ..]]
set out_dir      [file join $project_root build generated pl_synth_offload synth]
file mkdir $out_dir

# 允许在同一 Vivado 会话内重复运行：清掉旧设计与旧源文件引用，强制重读 RTL
catch { close_design }
catch { remove_files [get_files -quiet] }

read_verilog -sv [list \
    [file join $project_root src rtl synth_offload twiddle_rom_1024.v] \
    [file join $project_root src rtl synth_offload dpram_1024x36.v] \
    [file join $project_root src rtl synth_offload ifft1024_stream.v]]

synth_design -mode out_of_context -top ifft1024_stream -part xc7z020clg400-2
create_clock -name clk -period 10.000 [get_ports clk]

report_utilization -file [file join $out_dir utilization.txt]
report_utilization -hierarchical -file [file join $out_dir utilization_hier.txt]
report_timing_summary -file [file join $out_dir timing_summary.txt] -max_paths 5
report_design_analysis -file [file join $out_dir design_analysis.txt]
report_control_sets -file [file join $out_dir control_sets.txt]

set ram_count [llength [get_cells -hier -filter {REF_NAME =~ RAMB*}]]
set dsp_count [llength [get_cells -hier -filter {REF_NAME =~ DSP48*}]]
set lut_count [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]
set ff_count  [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
puts SYNTH_PASS_RAMB=$ram_count
puts SYNTH_PASS_DSP=$dsp_count
puts SYNTH_PASS_LUT_CELLS=$lut_count
puts SYNTH_PASS_FF_CELLS=$ff_count

set wns_path [get_timing_paths -delay_type max -max_paths 1 -nworst 1]
set whs_path [get_timing_paths -delay_type min -max_paths 1 -nworst 1]
if {[llength $wns_path] > 0} {
    puts SYNTH_PASS_WNS=[get_property SLACK $wns_path]
    puts SYNTH_PASS_WNS_START=[get_property STARTPOINT_PIN $wns_path]
    puts SYNTH_PASS_WNS_END=[get_property ENDPOINT_PIN $wns_path]
    puts SYNTH_PASS_WNS_LEVELS=[get_property LOGIC_LEVELS $wns_path]
}
if {[llength $whs_path] > 0} {
    puts SYNTH_PASS_WHS=[get_property SLACK $whs_path]
}

write_checkpoint -force [file join $out_dir ifft1024_stream_synth.dcp]
puts SYNTH_PASS_DCP=[file join $out_dir ifft1024_stream_synth.dcp]
puts SYNTH_PASS_DONE
