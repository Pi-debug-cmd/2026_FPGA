# Implement the already validated full audio + fused minimum-phase project.
# Build only: never programs hardware.
set root [file normalize [file join [file dirname [info script]] ..]]
set out [expr {[info exists ::env(WORLD_MINPHASE_PROJECT)] ? [file normalize $::env(WORLD_MINPHASE_PROJECT)] : [file join $root build generated world_minphase_20261029]}]
set project [file join $out voice7020.xpr]
if {![file exists $project]} {error "Missing validated project $project"}
open_project $project
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
foreach kind {utilization timing_summary drc route_status} {
  report_$kind -file [file join $out ${kind}.txt]
}
report_bus_skew -file [file join $out bus_skew.txt]
foreach delay {max min} {
  set path [get_timing_paths -max_paths 1 -delay_type $delay]
  if {![llength $path] || [get_property SLACK $path] < 0} {
    error "Routed timing failed or missing ($delay)"
  }
}
if {[llength [get_drc_violations -filter {SEVERITY == Error}]]} {error "DRC errors"}
if {[llength [get_nets -hierarchical -filter {ROUTE_STATUS == UNROUTED || ROUTE_STATUS == PARTIAL}]]} {error "Unrouted nets"}
puts WORLD_MINPHASE_BITSTREAM_BUILT
