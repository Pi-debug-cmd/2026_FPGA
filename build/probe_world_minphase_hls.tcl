set root [file normalize [file join [file dirname [info script]] ..]]
set project [file join $root build generated world_minphase_hls]
if {[info exists ::env(WORLD_HLS_PROJECT)]} {set project $::env(WORLD_HLS_PROJECT)}
if {[file exists $project]} {error "Use a fresh WORLD_HLS_PROJECT to preserve prior HLS evidence"}
open_project $project
set_top world_minphase
add_files [file join $root src hls world_minphase.cpp]
open_solution -reset solution -flow_target vivado
set_part xc7z020clg400-2
create_clock -period 10 -name default
csynth_design
exit
