# Standalone arithmetic/memory implementation, not a complete PS/audio system.
set project_root [file normalize [file join [file dirname [info script]] ..]]
set output_dir [file join $project_root build generated pitch_synth]
file mkdir $output_dir
read_verilog [list [file join $project_root src rtl pcm_delay_ram.v] [file join $project_root src rtl axis_pitch_shift.v]]
synth_design -mode out_of_context -top axis_pitch_shift -part xc7z020clg400-1
create_clock -name aclk -period 10.000 [get_ports aclk]
report_utilization -file [file join $project_root report pitch_utilization.txt]
report_timing_summary -file [file join $project_root report pitch_synth_timing.txt]
if {[llength [get_cells -hier -filter {REF_NAME =~ RAMB*}]] == 0} {
    error "Delay RAM did not map to BRAM; inspect synthesis report"
}
write_checkpoint -force [file join $output_dir axis_pitch_shift.dcp]
puts "PASS: pitch out-of-context synthesis; not a board implementation"
