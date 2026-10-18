open_project D:/g_build/proj/voice7020.xpr
reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
puts "IMPL status: [get_property STATUS [get_runs impl_1]]"
puts IMPL_RERUN_DONE
exit
