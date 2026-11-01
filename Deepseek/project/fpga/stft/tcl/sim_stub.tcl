# Fast control-path simulation: the frame engine with pass-through FFT stubs
# (the real xfft behavioral models are too slow to elaborate at 1024 points).
set root [file normalize [file join [file dirname [info script]] ..]]

create_project -force simstub [file join $root build simstub] -part xc7z020clg400-2
add_files -norecurse [list \
    [file join $root rtl axis_stft_gain.v] \
    [file join $root sim fft_stub.v] \
    [file join $root sim tb_axis_stft_gain.v] ]
set_property top tb_axis_stft_gain [get_filesets sources_1]
set_property top tb_axis_stft_gain [get_filesets sim_1]
update_compile_order -fileset sources_1

set xsimdir [file join $root build simstub simstub.sim sim_1 behav xsim]
file mkdir $xsimdir
file copy -force [file join $root data x_in.hex] $xsimdir
file copy -force [file join $root data g_in.hex] $xsimdir

set fs [get_filesets sim_1]
set_property xsim.simulate.wdb none $fs
set_property xsim.simulate.runtime all $fs
launch_simulation
puts "SIM_STUB_DONE"
