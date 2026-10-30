# Open the separate FFT integration project first; generate vectors with the checker.
set root [file normalize [file join [file dirname [info script]] ..]]
add_files -fileset sim_1 [file join $root sim tb_axis_world_fft.sv]
set_property top tb_axis_world_fft [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set simdir [file join $root build generated world_fft_20261027 voice7020.sim sim_1 behav xsim]
file mkdir $simdir
foreach name {input.mem output.mem compact_input.mem compact_output.mem} {
  file copy -force [file join $root build generated world_fft_rtl_vectors $name] [file join $simdir $name]
}
launch_simulation
