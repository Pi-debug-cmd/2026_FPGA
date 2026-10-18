open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "=== ADDR SPACES ==="
foreach s [get_bd_addr_spaces] { puts $s }
puts "=== ADDR SEGMENTS (control targets) ==="
foreach s [get_bd_addr_segs] { puts $s }
exit
