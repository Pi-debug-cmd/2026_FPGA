# 2018.3 synthesis for the stft_dma block design.
set root [file normalize [file join [file dirname [info script]] ..]]
set out [file join $root build generated stft_dma]
open_project [file join $out voice7020.xpr]
open_bd_design [get_files zynq.bd]
validate_bd_design
save_bd_design
set_property GENERATE_SYNTH_CHECKPOINT true [get_files zynq.bd]
generate_target all [get_files zynq.bd]
if {[catch {create_ip_run [get_files zynq.bd]} msg]} {puts "create_ip_run note: $msg"}
update_compile_order -fileset sources_1
reset_run synth_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed: inspect run log"}
open_run synth_1
report_utilization -file [file join $root report synth_utilization.txt]
report_utilization -hierarchical -file [file join $root report synth_utilization_hier.txt]
report_timing_summary -file [file join $root report synth_timing.txt]
report_drc -file [file join $root report synth_drc.txt]
puts STFT_DMA_SYNTHESIZED
exit
