# Independent precision/resource probe. Does not load PL or touch the audio project.
set root [file normalize [file join [file dirname [info script]] ..]]
set output [file join $root build generated world_fft_probe]
create_project world_fft_probe $output -part xc7z020clg400-2 -force
create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name world_fft_probe
set_property -dict [list CONFIG.transform_length {2048} \
  CONFIG.run_time_configurable_transform_length {true} \
  CONFIG.implementation_options {pipelined_streaming_io} \
  CONFIG.data_format {floating_point} CONFIG.phase_factor_width {25} \
  CONFIG.output_ordering {natural_order} CONFIG.aresetn {true} \
  CONFIG.target_clock_frequency {100}] [get_ips world_fft_probe]
generate_target all [get_ips world_fft_probe]
create_ip_run [get_ips world_fft_probe]
launch_runs world_fft_probe_synth_1 -jobs 4
