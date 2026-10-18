# The dynamic audio clock's LOCKED_O feeds both dcm_locked and ext_reset_in.
# Both must release reset when LOCKED_O is high.  Make external reset active low.
open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
set_property CONFIG.C_EXT_RESET_HIGH {0} [get_bd_cells audio_rst]
save_bd_design
validate_bd_design
generate_target all [get_files zynq.bd]
export_ip_user_files -of_objects [get_files zynq.bd] -no_script -sync -force -quiet
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
puts "SYNTH status: [get_property STATUS [get_runs synth_1]]"
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
puts "IMPL status: [get_property STATUS [get_runs impl_1]]"
exit
