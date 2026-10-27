# Behavioral simulation of the STFT/gain frame engine against the numpy stimulus.
set root [file normalize [file join [file dirname [info script]] ..]]
source [file join $root tcl ip_fft.tcl]

create_project -force sim [file join $root build sim] -part xc7z020clg400-2
make_fft_ips

add_files -norecurse [list \
    [file join $root rtl axis_stft_gain.v] \
    [file join $root sim tb_axis_stft_gain.v] ]
set_property top tb_axis_stft_gain [get_filesets sources_1]
set_property top tb_axis_stft_gain [get_filesets sim_1]
update_compile_order -fileset sources_1

set xsimdir [file join $root build sim sim.sim sim_1 behav xsim]
file mkdir $xsimdir
file copy -force [file join $root data x_in.hex] $xsimdir
file copy -force [file join $root data g_in.hex] $xsimdir

launch_simulation
run all
puts "SIM_DONE"
