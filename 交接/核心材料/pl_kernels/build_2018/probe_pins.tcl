open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "=== PS7 intf pins ==="
foreach p [get_bd_intf_pins -of_objects [get_bd_cells ps7]] { puts $p }
puts "=== PS7 scalar pins (clock/reset) ==="
foreach p [get_bd_pins -of_objects [get_bd_cells ps7]] { puts $p }
puts "=== audio_formatter intf pins ==="
foreach p [get_bd_intf_pins -of_objects [get_bd_cells audio_formatter]] { puts $p }
exit
