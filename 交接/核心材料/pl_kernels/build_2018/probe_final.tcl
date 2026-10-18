open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "=== CELLS ==="
foreach c [get_bd_cells] { puts $c }
puts "=== BD validation ==="
validate_bd_design
puts VALIDATE_DONE
exit
