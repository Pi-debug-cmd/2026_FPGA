set root [file normalize [file join [file dirname [info script]] ..]]
if {![info exists ::env(WORLD_SYNTH_HLS_PROJECT)]} {
  error "Set WORLD_SYNTH_HLS_PROJECT to the completed fresh synthesis project"
}
set project $::env(WORLD_SYNTH_HLS_PROJECT)
if {![file exists $project]} {error "Missing HLS project: $project"}
open_project $project
open_solution solution
cosim_design -rtl verilog -tool xsim
exit
