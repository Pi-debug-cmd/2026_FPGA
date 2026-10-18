open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
foreach p [get_bd_ports] {
  set d [get_bd_ports $p]
  puts "PORT $p DIR=[get_property DIR $d]"
}
exit
