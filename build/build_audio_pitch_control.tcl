# Constructed separately from the already tested fixed-ratio project.
set root [file normalize [file join [file dirname [info script]] ..]]
open_project [file join $root build generated audio_pitch_dma_control voice7020.xpr]
set_property GENERATE_SYNTH_CHECKPOINT true [get_files zynq.bd]
generate_target all [get_files zynq.bd]
create_ip_run [get_files zynq.bd]
update_compile_order -fileset sources_1
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed"}
set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
report_utilization -file [file join $root report audio_pitch_control_utilization.txt]
report_timing_summary -file [file join $root report audio_pitch_control_timing.txt]
report_bus_skew -file [file join $root report audio_pitch_control_bus_skew.txt]
report_drc -file [file join $root report audio_pitch_control_drc.txt]
puts AUDIO_PITCH_CONTROL_BUILT
exit
