open_project D:/g_build/proj/voice7020.xpr
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
puts "SYNTH status: [get_property STATUS [get_runs synth_1]]"
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
puts "IMPL status: [get_property STATUS [get_runs impl_1]]"
puts BITSTREAM_FLOW_DONE
exit
