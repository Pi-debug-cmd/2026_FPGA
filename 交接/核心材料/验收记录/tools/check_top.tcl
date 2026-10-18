open_project D:/g_build/proj/voice7020.xpr
puts "TOP=[get_property top [current_fileset]]"
puts "WRAPPER_FILES: [get_files *zynq_wrapper*]"
foreach f [get_files *zynq_wrapper*] {
  puts "  $f  USE_IN_SYNTH=[get_property USE_IN_SYNTH $f]  EXISTS=[file exists $f]"
}
puts "MYIOBUF: [get_files *my_iobuf*]"
exit
