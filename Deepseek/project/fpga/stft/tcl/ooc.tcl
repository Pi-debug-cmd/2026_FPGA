# Out-of-context synth + implementation for one module: resource utilisation,
# WNS and an fmax estimate, without the rest of the block design.
#   vivado -mode batch -source ooc.tcl -tclargs m1_fft fft_pair
#   vivado -mode batch -source ooc.tcl -tclargs m2_core axis_stft_gain
set root [file normalize [file join [file dirname [info script]] ..]]
source [file join $root tcl ip_fft.tcl]

set tag [lindex $argv 0]
set top [lindex $argv 1]
if {$tag eq ""} { set tag m2_core }
if {$top eq ""} { set top axis_stft_gain }

set proj [file join $root build ooc_$tag]
create_project -force $tag $proj -part xc7z020clg400-2
make_fft_ips
add_files -norecurse [list \
    [file join $root rtl axis_stft_gain.v] \
    [file join $root rtl fft_pair.v] ]
# 100 MHz out-of-context clock on aclk
set xdc [file join $root tcl ooc_clock.xdc]
set fh [open $xdc w]
puts $fh {create_clock -period 10.000 -name aclk [get_ports aclk]}
close $fh
add_files -fileset constrs_1 -norecurse $xdc
set_property top $top [current_fileset]
update_compile_order -fileset sources_1

# out-of-context synthesis through a run, so the xfft IPs are synth'd as OOC IP
reset_run synth_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} { error "synth failed" }
open_run synth_1
report_utilization -file [file join $root report ooc_${tag}_util.txt]
report_utilization -hierarchical -file [file join $root report ooc_${tag}_util_hier.txt]
report_timing_summary -file [file join $root report ooc_${tag}_timing_synth.txt]

launch_runs impl_1 -to_step route_design -jobs 8
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} { error "impl failed" }
open_run impl_1
report_utilization -file [file join $root report ooc_${tag}_impl_util.txt]
report_timing_summary -file [file join $root report ooc_${tag}_timing.txt] -max_paths 5
set wns [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
puts "OOC_${tag}_WNS=$wns"
puts "OOC_${tag}_FMAX_MHZ=[expr {1000.0 / (10.0 - $wns)}]"
puts "OOC_${tag}_DONE"
exit
