set root [file normalize [file join [file dirname [info script]] ..]]
if {[llength $argv] != 1} {error "Pass the WORLD 0.3.5 lib/World source directory"}
set world [file normalize [lindex $argv 0]]
open_project [file join $root build generated world_minphase_hls]
set_top world_minphase
add_files -tb [file join $root sim tb_world_minphase.cpp] -cflags "-I\"$world/src\""
foreach name {common fft matlabfunctions} {
  add_files -tb [file join $world src ${name}.cpp] -cflags "-I\"$world/src\""
}
open_solution solution
csim_design
csynth_design
cosim_design -rtl verilog -tool xsim
exit
