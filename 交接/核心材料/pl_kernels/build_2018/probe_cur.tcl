open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "=== CELLS ==="
foreach c [get_bd_cells] { puts $c }
puts "=== PS7 intf pins ==="
foreach p [get_bd_intf_pins ps7] { puts $p }
puts "=== PS7 scalar pins ==="
foreach p [get_bd_pins ps7] { puts $p }
exit
