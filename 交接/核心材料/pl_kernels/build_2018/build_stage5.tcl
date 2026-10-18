# =====================================================================
# Stage 5: wire ctrl_ic (1x5), 3 HP ICs, externalize PS I2C0/I2C1.
# =====================================================================
open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]

# ---- control interconnect: GP0 -> 5 slaves ----
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins ctrl_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M00_AXI] [get_bd_intf_pins audio_formatter/s_axi_lite]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M01_AXI] [get_bd_intf_pins i2s_receiver/s_axi_ctrl]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M02_AXI] [get_bd_intf_pins i2s_transmitter/s_axi_ctrl]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M03_AXI] [get_bd_intf_pins audio_dynclk/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M04_AXI] [get_bd_intf_pins gemm/s_axi_control]

# ---- 3 dedicated HP interconnects ----
connect_bd_intf_net [get_bd_intf_pins gemm/m_axi_weights_bus] [get_bd_intf_pins w_hp_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins w_hp_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP1]
connect_bd_intf_net [get_bd_intf_pins gemm/m_axi_input_bus] [get_bd_intf_pins i_hp_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins i_hp_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP2]
connect_bd_intf_net [get_bd_intf_pins gemm/m_axi_output_bus] [get_bd_intf_pins o_hp_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins o_hp_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP3]

# ---- externalize PS I2C0/I2C1 (EMIO) ----
make_bd_intf_pins_external [get_bd_intf_pins ps7/IIC_0]
make_bd_intf_pins_external [get_bd_intf_pins ps7/IIC_1]

# ---- clocks for new interconnects ----
foreach ic {ctrl_ic w_hp_ic i_hp_ic o_hp_ic} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $ic/ACLK]
}
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins ctrl_ic/S00_ACLK]
foreach m {M00 M01 M02 M03 M04} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins ctrl_ic/${m}_ACLK]
}
foreach ic {w_hp_ic i_hp_ic o_hp_ic} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $ic/S00_ACLK]
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $ic/M00_ACLK]
}

# ---- resets for new interconnects ----
foreach ic {ctrl_ic w_hp_ic i_hp_ic o_hp_ic} {
  connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins $ic/ARESETN]
}
connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins ctrl_ic/S00_ARESETN]
foreach m {M00 M01 M02 M03 M04} {
  connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins ctrl_ic/${m}_ARESETN]
}
foreach ic {w_hp_ic i_hp_ic o_hp_ic} {
  connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins $ic/S00_ARESETN]
  connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins $ic/M00_ARESETN]
}

# ---- gemm clock/reset ----
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins gemm/ap_clk]
connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins gemm/ap_rst_n]

# audio DMA top-level reset
connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins audio_dma_ic/ARESETN]

save_bd_design
validate_bd_design
puts STAGE5_DONE
exit
