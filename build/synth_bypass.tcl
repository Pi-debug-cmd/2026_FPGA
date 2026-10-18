# Out-of-context smoke synthesis only; no PS preset, pin binding or bitstream.
set project_root [file normalize [file join [file dirname [info script]] ..]]
set output_dir [file join $project_root build generated axis_bypass_synth]
file mkdir $output_dir
read_verilog [file join $project_root src rtl axis_audio_bypass.v]
# User-supplied grade -1 used conservatively until actual marking is checked.
synth_design -mode out_of_context -top axis_audio_bypass -part xc7z020clg400-1
create_clock -name aclk -period 10.000 [get_ports aclk]
report_utilization -file [file join $project_root report axis_bypass_utilization.txt]
report_timing_summary -file [file join $project_root report axis_bypass_synth_timing.txt]
write_checkpoint -force [file join $output_dir axis_audio_bypass.dcp]
puts "PASS: bypass out-of-context synthesis; not a board implementation"
