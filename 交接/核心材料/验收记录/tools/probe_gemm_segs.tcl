open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
foreach ic { weights_ic input_ic output_ic audio_dma_ic } {
  puts "==== $ic segments ===="
  foreach seg [get_bd_addr_segs -of_objects [get_bd_intf_pins $ic/*]] {
    puts "  [get_bd_intf_pins -of_objects $seg] range=[get_property RANGE $seg] offset=[get_property OFFSET $seg]"
  }
}
puts "==== HP port address spaces ===="
foreach p { S_AXI_HP0 S_AXI_HP1 S_AXI_HP2 S_AXI_HP3 } {
  puts "$p: [get_bd_addr_segs ps7/$p*]"
}
exit
