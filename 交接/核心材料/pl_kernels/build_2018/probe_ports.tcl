open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "=== SCALAR PORTS ==="
foreach p [get_bd_ports] { puts $p }
puts "=== INTERFACE PORTS ==="
foreach p [get_bd_intf_ports] { puts $p }
puts "=== IIC external intf pins ==="
foreach p [get_bd_pins -of_objects [get_bd_intf_ports IIC]] { puts $p }
exit
