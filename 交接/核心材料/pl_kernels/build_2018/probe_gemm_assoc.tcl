open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
puts "=== gemm cell properties ==="
foreach p {ASSOCIATED_BUSIF} {
  puts "$p = [get_property $p [get_bd_cells gemm]]"
}
puts "=== gemm m_axi intf pin CLK assoc ==="
foreach pin {m_axi_weights_bus m_axi_input_bus m_axi_output_bus s_axi_control} {
  puts "$pin -> [get_property CONFIG.ASSOCIATED_CLK [get_bd_intf_pins gemm/$pin]]"
}
puts "=== gemm_hp_ic xbar master addr config ==="
foreach m {M00 M01 M02} {
  puts "$m base=[get_property ${m}_A00_BASE_ADDR [get_bd_cells gemm_hp_ic/xbar]] range=[get_property ${m}_A00_ADDR_WIDTH [get_bd_cells gemm_hp_ic/xbar]]"
}
exit
