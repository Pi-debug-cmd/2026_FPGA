open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "IIC_PINS: [get_bd_pins *IIC*]"
puts "IIC_INTF: [get_bd_intf_pins *IIC*]"
exit
