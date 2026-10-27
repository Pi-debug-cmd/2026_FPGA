# Build only: no hardware programming.
set root [file normalize [file join [file dirname [info script]] ..]]
source [file join $root build create_world_exp_20261027.tcl]
set out [file join $root build generated $tag]
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
foreach kind {utilization timing_summary drc} {
  report_$kind -file [file join $out ${kind}.txt]
}
report_bus_skew -file [file join $out bus_skew.txt]
foreach delay {max min} {
  if {[get_property SLACK [get_timing_paths -max_paths 1 -delay_type $delay]] < 0} {
    error "Routed timing failed ($delay)"
  }
}
if {[llength [get_drc_violations -filter {SEVERITY == Error}]]} {error "DRC errors"}
puts [expr {$with_fft ? "WORLD_FFT_BITSTREAM_BUILT" : "WORLD_EXP_BITSTREAM_BUILT"}]
