# M1: forward-FFT-only behavioural simulation against the numpy stimulus.
set root [file normalize [file join [file dirname [info script]] ..]]

create_project -force simfwd [file join $root build simfwd] -part xc7z020clg400-2
create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name fft_fwd
set_property -dict [list \
    CONFIG.transform_length {1024} \
    CONFIG.implementation_options {pipelined_streaming_io} \
    CONFIG.data_format {fixed_point} \
    CONFIG.input_width {24} \
    CONFIG.phase_factor_width {24} \
    CONFIG.scaling_options {unscaled} \
    CONFIG.rounding_modes {convergent_rounding} \
    CONFIG.output_ordering {natural_order} \
    CONFIG.ovflo {false} \
    CONFIG.aclken {false} \
    CONFIG.aresetn {true} \
    CONFIG.xk_index {false} \
    CONFIG.target_clock_frequency {100} ] [get_ips fft_fwd]
generate_target {simulation synthesis} [get_ips fft_fwd]

add_files -norecurse [file join $root sim tb_fft_fwd.v]
set_property top tb_fft_fwd [get_filesets sources_1]
set_property top tb_fft_fwd [get_filesets sim_1]
update_compile_order -fileset sources_1

set xsimdir [file join $root build simfwd simfwd.sim sim_1 behav xsim]
file mkdir $xsimdir
file copy -force [file join $root data x_in.hex] $xsimdir

set fs [get_filesets sim_1]
set_property xsim.simulate.wdb none $fs
set_property xsim.simulate.runtime all $fs
launch_simulation
puts "SIM_FWD_DONE"
