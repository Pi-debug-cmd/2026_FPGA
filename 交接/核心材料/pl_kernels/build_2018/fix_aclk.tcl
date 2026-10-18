open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] \
  [get_bd_pins ps7/M_AXI_GP0_ACLK] \
  [get_bd_pins ps7/S_AXI_HP0_ACLK] \
  [get_bd_pins ps7/S_AXI_HP1_ACLK] \
  [get_bd_pins ps7/S_AXI_HP2_ACLK] \
  [get_bd_pins ps7/S_AXI_HP3_ACLK]
save_bd_design
validate_bd_design
puts ACLK_FIXED
exit
