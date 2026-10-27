# Audio wiring adapted from reviewed handoff; PS and pins audited against A disk.
set root [file normalize [file join [file dirname [info script]] ..]]
set tag world_exp_20261027
if {[llength $argv] > 1 || ![regexp {^world_exp_[0-9]+$} $tag]} {error "Invalid output tag"}
set out [file join $root build generated $tag]
if {[file exists [file join $out voice7020.xpr]]} {error "Output project exists; preserve it"}
create_project voice7020 $out -part xc7z020clg400-2
set_property ip_repo_paths [list [file join $root board vendor_inputs ip_repo]] [current_project]
update_ip_catalog
add_files [glob [file join $root src rtl synth_offload minphase*.v]]
add_files [file join $root src rtl synth_offload axis_world_exp.v]
update_compile_order -fileset sources_1
create_bd_design zynq
# ---------------- PS7 ----------------
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
source [file join $root board vendor_inputs ps7_config.tcl]
set_property -dict $ps_cfg $ps
set_property -dict [list CONFIG.PCW_USE_S_AXI_HP2 {0} CONFIG.PCW_USE_S_AXI_HP3 {0}] $ps
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
set iic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_iic:2.1 axi_iic]
set_property -dict [list CONFIG.C_SCL_INERTIAL_DELAY {50} CONFIG.C_SDA_INERTIAL_DELAY {50}] $iic
set dma [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 pitch_dma]
set_property -dict [list CONFIG.c_include_sg {0} CONFIG.c_m_axis_mm2s_tdata_width {64} CONFIG.c_s_axis_s2mm_tdata_width {64} CONFIG.c_sg_length_width {23}] $dma
create_bd_cell -type module -reference axis_world_exp pitch
set cic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 ctrl_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {6}] $cic
set pic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 pitch_dma_mem]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $pic

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
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M05_AXI] [get_bd_intf_pins pitch_dma/S_AXI_LITE]

# Independent WORLD complex-exp stream; audio routing stays on HP0.
connect_bd_intf_net [get_bd_intf_pins pitch_dma/M_AXI_MM2S] [get_bd_intf_pins pitch_dma_mem/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins pitch_dma/M_AXI_S2MM] [get_bd_intf_pins pitch_dma_mem/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins pitch_dma_mem/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP1]
connect_bd_intf_net [get_bd_intf_pins pitch_dma/M_AXIS_MM2S] [get_bd_intf_pins pitch/s_axis]
connect_bd_intf_net [get_bd_intf_pins pitch/m_axis] [get_bd_intf_pins pitch_dma/S_AXIS_S2MM]


# ---------------- clocks ----------------
# PS AXI ACLKs
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins ps7/M_AXI_GP0_ACLK] \
  [get_bd_pins ps7/S_AXI_HP0_ACLK] [get_bd_pins ps7/S_AXI_HP1_ACLK]
# control clocks
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] \
  [get_bd_pins audio_formatter/s_axi_lite_aclk] [get_bd_pins audio_formatter/m_axis_mm2s_aclk] [get_bd_pins audio_formatter/s_axis_s2mm_aclk] \
  [get_bd_pins i2s_receiver/s_axi_ctrl_aclk] [get_bd_pins i2s_receiver/m_axis_aud_aclk] \
  [get_bd_pins i2s_transmitter/s_axi_ctrl_aclk] [get_bd_pins i2s_transmitter/s_axis_aud_aclk] \
  [get_bd_pins audio_dynclk/REF_CLK_I] [get_bd_pins audio_dynclk/s_axi_lite_aclk] \
  [get_bd_pins audio_dma_ic/ACLK] [get_bd_pins audio_dma_ic/S00_ACLK] [get_bd_pins audio_dma_ic/S01_ACLK] [get_bd_pins audio_dma_ic/M00_ACLK] \
  [get_bd_pins ctrl_ic/ACLK] [get_bd_pins ctrl_ic/S00_ACLK] \
  [get_bd_pins pitch_dma_mem/ACLK] [get_bd_pins pitch_dma_mem/S01_ACLK] \
  [get_bd_pins pitch/aclk] [get_bd_pins pitch_dma/s_axi_lite_aclk] [get_bd_pins pitch_dma/m_axi_mm2s_aclk] [get_bd_pins pitch_dma/m_axi_s2mm_aclk] \
  [get_bd_pins axi_iic/s_axi_aclk]
foreach m {M00 M01 M02 M03 M04 M05} {
  connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins ctrl_ic/${m}_ACLK]
}
foreach ic {pitch_dma_mem} {
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
  [get_bd_pins pitch_dma_mem/ARESETN] [get_bd_pins pitch_dma_mem/S01_ARESETN] \
  [get_bd_pins pitch/aresetn] [get_bd_pins pitch_dma/axi_resetn] [get_bd_pins axi_iic/s_axi_aresetn]
foreach m {M00 M01 M02 M03 M04 M05} {
  connect_bd_net [get_bd_pins crst/peripheral_aresetn] [get_bd_pins ctrl_ic/${m}_ARESETN]
}
foreach ic {pitch_dma_mem} {
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
connect_bd_net [get_bd_pins pitch_dma/mm2s_introut] [get_bd_pins xlc/In12]
connect_bd_net [get_bd_pins pitch_dma/s2mm_introut] [get_bd_pins xlc/In13]
connect_bd_net [get_bd_pins axi_iic/iic2intc_irpt] [get_bd_pins xlc/In2]
foreach i {0 1 7 8 9 10 11 14 15} {
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
# Expose all A-disk I2C pins; codec is on PS I2C0 EMIO, not PL axi_iic.
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
add_files -norecurse [file join $root board vendor_inputs my_iobuf.v]
route_i2c I2C0 I2C1
route_i2c I2C1 I2C2
make_bd_intf_pins_external [get_bd_intf_pins axi_iic/IIC]
set_property name I2C3 [get_bd_intf_ports IIC_0]

# ---------------- addresses ----------------
assign_bd_address -offset 0x43C20000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs audio_dynclk/S_AXI_LITE/S_AXI_LITE_reg]
assign_bd_address -offset 0x43C40000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs audio_formatter/s_axi_lite/reg0]
assign_bd_address -offset 0x43C50000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs i2s_receiver/s_axi_ctrl/Reg]
assign_bd_address -offset 0x43C60000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs i2s_transmitter/s_axi_ctrl/Reg]
assign_bd_address -offset 0x41600000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs axi_iic/S_AXI/Reg]
assign_bd_address -offset 0x40400000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs pitch_dma/S_AXI_LITE/Reg]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces audio_formatter/m_axi_mm2s] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]
assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces audio_formatter/m_axi_s2mm] [get_bd_addr_segs ps7/S_AXI_HP0/HP0_DDR_LOWOCM]

foreach master {M_AXI_MM2S M_AXI_S2MM} {
  assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces pitch_dma/$master] [get_bd_addr_segs ps7/S_AXI_HP1/HP1_DDR_LOWOCM]
}
save_bd_design
validate_bd_design
save_bd_design
add_files -norecurse [make_wrapper -files [get_files zynq.bd] -top]
add_files -fileset constrs_1 [file join $root board vendor_inputs audio_i2c.xdc]
set_property top zynq_wrapper [current_fileset]
puts WORLD_EXP_VALIDATED
