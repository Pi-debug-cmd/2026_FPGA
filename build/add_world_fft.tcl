# Called by create_world_exp_20261027.tcl only for the separate FFT candidate.
create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name world_fft_core
set_property -dict [list CONFIG.transform_length {2048} \
  CONFIG.run_time_configurable_transform_length {true} \
  CONFIG.implementation_options {pipelined_streaming_io} \
  CONFIG.data_format {floating_point} CONFIG.phase_factor_width {25} \
  CONFIG.output_ordering {natural_order} CONFIG.aresetn {true} \
  CONFIG.target_clock_frequency {100}] [get_ips world_fft_core]
generate_target all [get_ips world_fft_core]
add_files [file join $root src rtl synth_offload axis_world_fft.v]
update_compile_order -fileset sources_1
set fdma [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 fft_dma]
set_property -dict [list CONFIG.c_include_sg {0} CONFIG.c_m_axis_mm2s_tdata_width {64} \
  CONFIG.c_s_axis_s2mm_tdata_width {64} CONFIG.c_sg_length_width {23}] $fdma
create_bd_cell -type module -reference axis_world_fft fft
set fic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 fft_dma_mem]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $fic
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M06_AXI] [get_bd_intf_pins fft_dma/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins fft_dma/M_AXIS_MM2S] [get_bd_intf_pins fft/s_axis]
connect_bd_intf_net [get_bd_intf_pins fft/m_axis] [get_bd_intf_pins fft_dma/S_AXIS_S2MM]
connect_bd_intf_net [get_bd_intf_pins fft_dma/M_AXI_MM2S] [get_bd_intf_pins fft_dma_mem/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins fft_dma/M_AXI_S2MM] [get_bd_intf_pins fft_dma_mem/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins fft_dma_mem/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP2]
foreach pin {ps7/S_AXI_HP2_ACLK ctrl_ic/M06_ACLK fft/aclk fft_dma/s_axi_lite_aclk fft_dma/m_axi_mm2s_aclk fft_dma/m_axi_s2mm_aclk fft_dma_mem/ACLK fft_dma_mem/S00_ACLK fft_dma_mem/S01_ACLK fft_dma_mem/M00_ACLK} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $pin]
}
foreach pin {ctrl_ic/M06_ARESETN fft/aresetn fft_dma/axi_resetn fft_dma_mem/ARESETN fft_dma_mem/S00_ARESETN fft_dma_mem/S01_ARESETN fft_dma_mem/M00_ARESETN} {
  connect_bd_net [get_bd_pins crst/peripheral_aresetn] [get_bd_pins $pin]
}
assign_bd_address -offset 0x40410000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs fft_dma/S_AXI_LITE/Reg]
foreach master {M_AXI_MM2S M_AXI_S2MM} {
  assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces fft_dma/$master] [get_bd_addr_segs ps7/S_AXI_HP2/HP2_DDR_LOWOCM]
}
