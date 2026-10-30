set root [file normalize [file join [file dirname [info script]] ..]]
set project [file join $root build generated world_synthesis_pulse_hls]
if {[info exists ::env(WORLD_SYNTH_HLS_PROJECT)]} {
  set project $::env(WORLD_SYNTH_HLS_PROJECT)
}
if {[file exists $project]} {
  error "Use a fresh WORLD_SYNTH_HLS_PROJECT to preserve prior HLS evidence"
}
open_project $project
set_top world_synthesis_pulse
add_files [file join $root src hls world_synthesis_pulse.cpp]
add_files -tb [file join $root sim tb_world_synthesis_pulse.cpp]
open_solution -reset solution -flow_target vivado
set_part xc7z020clg400-2
create_clock -period 10 -name default
csim_design
csynth_design
exit
