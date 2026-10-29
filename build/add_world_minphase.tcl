# Add the fused WORLD minimum-phase HLS kernel to the full audio design.
if {![info exists ::env(WORLD_MINPHASE_IP_REPO)]} {
  error "WORLD_MINPHASE_IP_REPO must point to the exported world_minphase IP directory"
}
set minphase_repo [file normalize $::env(WORLD_MINPHASE_IP_REPO)]
if {![file exists [file join $minphase_repo component.xml]]} {
  error "No component.xml in WORLD_MINPHASE_IP_REPO=$minphase_repo"
}

set mp [create_bd_cell -type ip -vlnv xilinx.com:hls:world_minphase:1.0 world_minphase]
set mic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 minphase_mem]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $mic

# The HLS export has separate AXI-Lite interfaces for ap_ctrl and pointer args.
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M06_AXI] [get_bd_intf_pins world_minphase/s_axi_control]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M07_AXI] [get_bd_intf_pins world_minphase/s_axi_control_r]
connect_bd_intf_net [get_bd_intf_pins world_minphase/m_axi_input_mem] [get_bd_intf_pins minphase_mem/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins world_minphase/m_axi_output_mem] [get_bd_intf_pins minphase_mem/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins minphase_mem/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP2]

foreach pin {ps7/S_AXI_HP2_ACLK ctrl_ic/M06_ACLK ctrl_ic/M07_ACLK world_minphase/ap_clk minphase_mem/ACLK minphase_mem/S00_ACLK minphase_mem/S01_ACLK minphase_mem/M00_ACLK} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $pin]
}
foreach pin {ctrl_ic/M06_ARESETN ctrl_ic/M07_ARESETN world_minphase/ap_rst_n minphase_mem/ARESETN minphase_mem/S00_ARESETN minphase_mem/S01_ARESETN minphase_mem/M00_ARESETN} {
  connect_bd_net [get_bd_pins crst/peripheral_aresetn] [get_bd_pins $pin]
}
connect_bd_net [get_bd_pins world_minphase/interrupt] [get_bd_pins xlc/In14]

assign_bd_address -offset 0x43C70000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs world_minphase/s_axi_control/Reg]
assign_bd_address -offset 0x43C80000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs world_minphase/s_axi_control_r/Reg]
foreach master {m_axi_input_mem m_axi_output_mem} {
  assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces world_minphase/$master] [get_bd_addr_segs ps7/S_AXI_HP2/HP2_DDR_LOWOCM]
}
