# =====================================================================
# Master build: minimal audio + gemm accelerator on ZYNQ7020 (2018.3)
# =====================================================================
set proj_dir D:/g_build/proj
file delete -force $proj_dir
file mkdir $proj_dir
create_project voice7020 $proj_dir -part xc7z020clg400-2
set_property ip_repo_paths [list D:/Tools_FPGA/workspace/voice_conversion_zynq7020/vendor_base_2022_2/ip_repo D:/g_ip] [current_project]
update_ip_catalog
create_bd_design zynq

# ---------------- PS7 ----------------
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
source D:/Tools_FPGA/workspace/voice_conversion_zynq7020/pl_kernels/build_2018/ps7_config.tcl
set_property -dict $ps_cfg $ps
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_wrapper {0}} $ps

# ---------------- audio components ----------------
set af [create_bd_cell -type ip -vlnv xilinx.com:ip:audio_formatter:1.0 audio_formatter]
set_property -dict [list CONFIG.C_MAX_NUM_CHANNELS_MM2S {2} CONFIG.C_MAX_NUM_CHANNELS_S2MM {2}] $af
set irx [create_bd_cell -type ip -vlnv xilinx.com:ip:i2s_receiver:1.0 i2s_receiver]
set itx [create_bd_cell -type ip -vlnv xilinx.com:ip:i2s_transmitter:1.0 i2s_transmitter]
set dclk [create_bd_cell -type ip -vlnv digilentinc.com:ip:axi_dynclk:1.2 audio_dynclk]
set arst [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 audio_rst]
set vor [create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 bclk_or]
set_property -dict [list CONFIG.C_OPERATION {or} CONFIG.C_SIZE {1}] $vor
set aic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 audio_dma_ic]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $aic

# control reset
set crst [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 crst]

# axi_iic + gemm
set iic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_iic:2.0 axi_iic]
set_property -dict [list CONFIG.C_SCL_INERTIAL_DELAY {50} CONFIG.C_SDA_INERTIAL_DELAY {50}] $iic
set gemm [create_bd_cell -type ip -vlnv local.user:hls:gemm_s8:1.1 gemm]
set cic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 ctrl_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {6}] $cic
# Three independent 1x1 interconnects (one GEMM master per HP port).
# A shared 3x3 crossbar makes all three MI base addresses equal 0x0 and
# fails validation; separate interconnects avoid the overlap.
set wic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 weights_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $wic
set i2ic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 input_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $i2ic
set oic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 output_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $oic

# interrupt concat (must match F2P bit positions expected by device tree)
set xlc [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlc]
set_property -dict [list CONFIG.NUM_PORTS {16}] $xlc
set irqzero [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 irqzero]
set_property -dict [list CONFIG.CONST_WIDTH {1} CONFIG.CONST_VAL {0}] $irqzero

# force all cell pins to be generated before wiring
save_bd_design

connect_bd_net [get_bd_pins ps7/FCLK_CLK0]     [get_bd_pins crst/slowest_sync_clk]
connect_bd_net [get_bd_pins ps7/FCLK_RESET0_N] [get_bd_pins crst/ext_reset_in]

# ---------------- AXI data flow ----------------
connect_bd_intf_net [get_bd_intf_pins i2s_receiver/m_axis_aud] [get_bd_intf_pins audio_formatter/s_axis_s2mm]
connect_bd_intf_net [get_bd_intf_pins audio_formatter/m_axis_mm2s] [get_bd_intf_pins i2s_transmitter/s_axis_aud]
connect_bd_intf_net [get_bd_intf_pins audio_formatter/m_axi_mm2s] [get_bd_intf_pins audio_dma_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins audio_formatter/m_axi_s2mm] [get_bd_intf_pins audio_dma_ic/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins audio_dma_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP0]

# control interconnect
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins ctrl_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M00_AXI] [get_bd_intf_pins audio_formatter/s_axi_lite]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M01_AXI] [get_bd_intf_pins i2s_receiver/s_axi_ctrl]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M02_AXI] [get_bd_intf_pins i2s_transmitter/s_axi_ctrl]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M03_AXI] [get_bd_intf_pins audio_dynclk/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M04_AXI] [get_bd_intf_pins axi_iic/S_AXI]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M05_AXI] [get_bd_intf_pins gemm/s_axi_control]

# gemm HP interconnects: weights->HP1, input->HP2, output->HP3
connect_bd_intf_net [get_bd_intf_pins gemm/m_axi_weights_bus] [get_bd_intf_pins weights_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins weights_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP1]
connect_bd_intf_net [get_bd_intf_pins gemm/m_axi_input_bus] [get_bd_intf_pins input_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins input_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP2]
connect_bd_intf_net [get_bd_intf_pins gemm/m_axi_output_bus] [get_bd_intf_pins output_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins output_ic/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP3]

# ---------------- clocks ----------------
# PS AXI ACLKs
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins ps7/M_AXI_GP0_ACLK] \
  [get_bd_pins ps7/S_AXI_HP0_ACLK] [get_bd_pins ps7/S_AXI_HP1_ACLK] \
  [get_bd_pins ps7/S_AXI_HP2_ACLK] [get_bd_pins ps7/S_AXI_HP3_ACLK]
# control clocks
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] \
  [get_bd_pins audio_formatter/s_axi_lite_aclk] [get_bd_pins audio_formatter/m_axis_mm2s_aclk] [get_bd_pins audio_formatter/s_axis_s2mm_aclk] \
  [get_bd_pins i2s_receiver/s_axi_ctrl_aclk] [get_bd_pins i2s_receiver/m_axis_aud_aclk] \
  [get_bd_pins i2s_transmitter/s_axi_ctrl_aclk] [get_bd_pins i2s_transmitter/s_axis_aud_aclk] \
  [get_bd_pins audio_dynclk/REF_CLK_I] [get_bd_pins audio_dynclk/s_axi_lite_aclk] \
  [get_bd_pins audio_dma_ic/ACLK] [get_bd_pins audio_dma_ic/S00_ACLK] [get_bd_pins audio_dma_ic/S01_ACLK] [get_bd_pins audio_dma_ic/M00_ACLK] \
  [get_bd_pins ctrl_ic/ACLK] [get_bd_pins ctrl_ic/S00_ACLK] \
  [get_bd_pins weights_ic/ACLK] [get_bd_pins input_ic/ACLK] [get_bd_pins output_ic/ACLK] \
  [get_bd_pins gemm/ap_clk] \
  [get_bd_pins axi_iic/s_axi_aclk]
foreach m {M00 M01 M02 M03 M04 M05} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins ctrl_ic/${m}_ACLK]
}
foreach ic {weights_ic input_ic output_ic} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $ic/S00_ACLK] [get_bd_pins $ic/M00_ACLK]
}
# MCLK
connect_bd_net [get_bd_pins audio_dynclk/PXL_CLK_O] \
  [get_bd_pins audio_formatter/aud_mclk] [get_bd_pins i2s_receiver/aud_mclk] [get_bd_pins i2s_transmitter/aud_mclk]

# ---------------- resets ----------------
connect_bd_net [get_bd_pins audio_dynclk/PXL_CLK_O] [get_bd_pins audio_rst/slowest_sync_clk]
connect_bd_net [get_bd_pins audio_dynclk/LOCKED_O] [get_bd_pins audio_rst/ext_reset_in] [get_bd_pins audio_rst/dcm_locked]
connect_bd_net [get_bd_pins audio_rst/peripheral_reset] \
  [get_bd_pins audio_formatter/aud_mreset] [get_bd_pins i2s_receiver/aud_mrst] [get_bd_pins i2s_transmitter/aud_mrst]
# active-low control resets
connect_bd_net [get_bd_pins crst/peripheral_aresetn] \
  [get_bd_pins audio_formatter/s_axi_lite_aresetn] [get_bd_pins audio_formatter/m_axis_mm2s_aresetn] [get_bd_pins audio_formatter/s_axis_s2mm_aresetn] \
  [get_bd_pins i2s_receiver/s_axi_ctrl_aresetn] [get_bd_pins i2s_receiver/m_axis_aud_aresetn] \
  [get_bd_pins i2s_transmitter/s_axi_ctrl_aresetn] [get_bd_pins i2s_transmitter/s_axis_aud_aresetn] \
  [get_bd_pins audio_dynclk/s_axi_lite_aresetn] \
  [get_bd_pins audio_dma_ic/ARESETN] [get_bd_pins audio_dma_ic/S00_ARESETN] [get_bd_pins audio_dma_ic/S01_ARESETN] [get_bd_pins audio_dma_ic/M00_ARESETN] \
  [get_bd_pins ctrl_ic/ARESETN] [get_bd_pins ctrl_ic/S00_ARESETN] \
  [get_bd_pins weights_ic/ARESETN] [get_bd_pins input_ic/ARESETN] [get_bd_pins output_ic/ARESETN] \
  [get_bd_pins gemm/ap_rst_n] [get_bd_pins axi_iic/s_axi_aresetn]
foreach m {M00 M01 M02 M03 M04 M05} {
  connect_bd_net [get_bd_pins crst/peripheral_aresetn] [get_bd_pins ctrl_ic/${m}_ARESETN]
}
foreach ic {weights_ic input_ic output_ic} {
  connect_bd_net [get_bd_pins crst/peripheral_aresetn] [get_bd_pins $ic/S00_ARESETN] [get_bd_pins $ic/M00_ARESETN]
}

# ---------------- interrupts ----------------
# Device tree F2P mapping (GIC SPI number = 61 + bit for bits 0..7):
#   In3 i2s_transmitter irq -> SPI64
#   In4 formatter irq_mm2s  -> SPI65
#   In5 formatter irq_s2mm  -> SPI66
#   In6 i2s_receiver irq    -> SPI67
connect_bd_net [get_bd_pins i2s_transmitter/irq] [get_bd_pins xlc/In3]
connect_bd_net [get_bd_pins audio_formatter/irq_mm2s] [get_bd_pins xlc/In4]
connect_bd_net [get_bd_pins audio_formatter/irq_s2mm] [get_bd_pins xlc/In5]
connect_bd_net [get_bd_pins i2s_receiver/irq] [get_bd_pins xlc/In6]
foreach i {0 1 2 7 8 9 10 11 12 13 14 15} {
  connect_bd_net [get_bd_pins irqzero/dout] [get_bd_pins xlc/In$i]
}
connect_bd_net [get_bd_pins xlc/dout] [get_bd_pins ps7/IRQ_F2P]

# ---------------- external ports ----------------
create_bd_port -dir O MCLK
connect_bd_net [get_bd_pins audio_dynclk/PXL_CLK_O] [get_bd_ports MCLK]
create_bd_port -dir O ADCLRC
connect_bd_net [get_bd_pins i2s_receiver/lrclk_out] [get_bd_ports ADCLRC]
create_bd_port -dir O DACLRC
connect_bd_net [get_bd_pins i2s_transmitter/lrclk_out] [get_bd_ports DACLRC]
create_bd_port -dir O BCLK
connect_bd_net [get_bd_pins i2s_receiver/sclk_out] [get_bd_pins bclk_or/Op1]
connect_bd_net [get_bd_pins i2s_transmitter/sclk_out] [get_bd_pins bclk_or/Op2]
connect_bd_net [get_bd_pins bclk_or/Res] [get_bd_ports BCLK]
create_bd_port -dir O DACDAT
connect_bd_net [get_bd_pins i2s_transmitter/sdata_0_out] [get_bd_ports DACDAT]
create_bd_port -dir I ADCDAT
connect_bd_net [get_bd_ports ADCDAT] [get_bd_pins i2s_receiver/sdata_0_in]
# Leave the PL axi_iic IIC interface unconnected (codec is on PS IIC0 EMIO).
# Route PS EMIO I2C member pins through IOBUF wrappers to physical inout pins.
proc route_i2c { prefix baseport } {
  foreach { sig lsig } { SCL scl SDA sda } {
    set ob [create_bd_cell -type module -reference my_iobuf ${baseport}_${lsig}_iobuf]
    connect_bd_net [get_bd_pins ps7/${prefix}_${sig}_O] [get_bd_pins $ob/I]
    connect_bd_net [get_bd_pins ps7/${prefix}_${sig}_T] [get_bd_pins $ob/T]
    connect_bd_net [get_bd_pins $ob/O] [get_bd_pins ps7/${prefix}_${sig}_I]
    create_bd_port -dir IO ${baseport}_${lsig}_io
    connect_bd_net [get_bd_pins $ob/IO] [get_bd_ports ${baseport}_${lsig}_io]
  }
}
add_files -norecurse D:/Tools_FPGA/workspace/voice_conversion_zynq7020/pl_kernels/build_2018/my_iobuf.v
route_i2c I2C0 IIC_0_0
route_i2c I2C1 IIC_1_0
puts "EXT_IIC_PORTS: [get_bd_ports IIC_*_io]"

# ---------------- addresses ----------------
assign_bd_address -offset 0x43C20000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs audio_dynclk/S_AXI_LITE/S_AXI_LITE_reg]
assign_bd_address -offset 0x43C40000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs audio_formatter/s_axi_lite/reg0]
assign_bd_address -offset 0x43C50000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs i2s_receiver/s_axi_ctrl/Reg]
assign_bd_address -offset 0x43C60000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs i2s_transmitter/s_axi_ctrl/Reg]
assign_bd_address -offset 0x41600000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs axi_iic/S_AXI/Reg]
assign_bd_address -offset 0x43D00000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs gemm/s_axi_control/reg0]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces audio_formatter/m_axi_mm2s] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces audio_formatter/m_axi_s2mm] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces gemm/m_axi_weights_bus] [get_bd_addr_segs ps7/S_AXI_HP1/HP1_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces gemm/m_axi_input_bus] [get_bd_addr_segs ps7/S_AXI_HP2/HP2_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces gemm/m_axi_output_bus] [get_bd_addr_segs ps7/S_AXI_HP3/HP3_DDR_LOWOCM]

save_bd_design
validate_bd_design
puts BUILD_ALL_DONE
exit
