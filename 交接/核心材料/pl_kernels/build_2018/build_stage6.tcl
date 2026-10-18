# =====================================================================
# Stage 6: assign addresses (5 control + HP paths).
# =====================================================================
open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]

# ---- control register addresses (ps7/Data = M_AXI_GP0) ----
assign_bd_address -offset 0x43C20000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs audio_dynclk/S_AXI_LITE/S_AXI_LITE_reg]
assign_bd_address -offset 0x43C40000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs audio_formatter/s_axi_lite/reg0]
assign_bd_address -offset 0x43C50000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs i2s_receiver/s_axi_ctrl/Reg]
assign_bd_address -offset 0x43C60000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs i2s_transmitter/s_axi_ctrl/Reg]
assign_bd_address -offset 0x43D00000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs gemm/s_axi_control/reg0]

# ---- audio DMA -> HP0 DDR ----
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces audio_formatter/m_axi_mm2s] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces audio_formatter/m_axi_s2mm] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]

# ---- gemm dedicated paths -> HP1/HP2/HP3 DDR ----
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces gemm/m_axi_weights_bus] [get_bd_addr_segs ps7/S_AXI_HP1/HP1_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces gemm/m_axi_input_bus] [get_bd_addr_segs ps7/S_AXI_HP2/HP2_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces gemm/m_axi_output_bus] [get_bd_addr_segs ps7/S_AXI_HP3/HP3_DDR_LOWOCM]

save_bd_design
validate_bd_design
puts STAGE6_DONE
exit
