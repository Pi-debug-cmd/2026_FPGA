set root [file normalize [file join [file dirname [info script]] ..]]
set project [file join $root build generated world_minphase_hls]
if {[info exists ::env(WORLD_HLS_PROJECT)]} {set project $::env(WORLD_HLS_PROJECT)}
if {![file exists $project]} {error "WORLD_HLS_PROJECT does not exist: $project"}
open_project $project
open_solution solution
export_design -flow impl -rtl verilog -format ip_catalog
exit
