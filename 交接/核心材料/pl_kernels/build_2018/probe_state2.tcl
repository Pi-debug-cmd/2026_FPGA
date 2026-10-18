open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "=== CELLS ==="
foreach c [get_bd_cells] { puts $c }
puts "=== INTERFACE PORTS ==="
foreach p [get_bd_intf_ports] { puts $p }
puts "=== SCALAR PORTS (I2C/audio) ==="
foreach p [get_bd_ports] { if {$p =~ "I2C|IIC|scl|sda|MCLK|ADCLRC|DACLRC|BCLK|DACDAT|ADCDAT"} { puts $p } }
puts "=== VALIDATE ==="
validate_bd_design
puts PROBE_DONE
exit
