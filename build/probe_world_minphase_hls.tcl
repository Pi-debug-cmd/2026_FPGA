set root [file normalize [file join [file dirname [info script]] ..]]
open_project -reset [file join $root build generated world_minphase_hls]
set_top world_minphase
add_files [file join $root src hls world_minphase.cpp]
open_solution -reset solution -flow_target vivado
set_part xc7z020clg400-2
create_clock -period 10 -name default
csynth_design
exit
