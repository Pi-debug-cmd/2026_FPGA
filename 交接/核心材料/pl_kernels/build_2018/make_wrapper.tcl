open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
validate_bd_design
puts VALIDATE_PASS
# -top generates, imports and sets the wrapper as the synthesis top.
make_wrapper -files [get_files zynq.bd] -top
puts "TOP_AFTER=[get_property top [current_fileset]]"
puts "WRAPPER_REG: [get_files *zynq_wrapper.v]"
puts WRAPPER_DONE
exit
