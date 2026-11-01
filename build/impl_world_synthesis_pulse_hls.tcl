# Implement an already synthesized WORLD pulse HLS project out of context.
# Build only: never opens or programs hardware.
set root [file normalize [file join [file dirname [info script]] ..]]
set project [file join $root build generated world_synthesis_pulse_hls]
if {[info exists ::env(WORLD_SYNTH_HLS_PROJECT)]} {
  set project [file normalize $::env(WORLD_SYNTH_HLS_PROJECT)]
}
if {![file exists $project]} {
  error "WORLD_SYNTH_HLS_PROJECT does not exist: $project"
}
open_project $project
open_solution solution
export_design -flow impl -rtl verilog -format ip_catalog
exit
