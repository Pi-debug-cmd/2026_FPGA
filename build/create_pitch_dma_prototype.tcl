# Offline connectivity prototype only. PS defaults are not board DDR/MIO settings.
# Never load this design on the board; audio peripherals are intentionally absent.
set root [file normalize [file join [file dirname [info script]] ..]]
set tag pitch_dma_prototype
if {[llength $argv] > 1} {error "Expected at most one output tag"}
if {[llength $argv] == 1} {set tag [lindex $argv 0]}
if {![regexp {^pitch_dma_prototype(_[a-zA-Z0-9]+)?$} $tag]} {error "Invalid output tag"}
set out [file join $root build generated $tag]
if {[file exists [file join $out pitch_dma.xpr]]} {
    error "Prototype exists; preserve it and choose a new output directory"
}
create_project pitch_dma $out -part xc7z020clg400-1
add_files [list [file join $root src rtl pcm_delay_ram.v] [file join $root src rtl axis_pitch_shift.v]]
update_compile_order -fileset sources_1
create_bd_design pitch_dma_bd
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1} CONFIG.PCW_USE_S_AXI_HP0 {1} CONFIG.PCW_USE_FABRIC_INTERRUPT {1} CONFIG.PCW_IRQ_F2P_INTR {1} CONFIG.PCW_EN_CLK0_PORT {1} CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {100}] $ps
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_wrapper {0}} $ps
set dma [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 dma]
set_property -dict [list CONFIG.c_include_sg {0} CONFIG.c_m_axis_mm2s_tdata_width {32} CONFIG.c_sg_length_width {23}] $dma
set ctrl [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 ctrl]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $ctrl
set mem [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 mem]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $mem
create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 rst
create_bd_cell -type module -reference axis_pitch_shift pitch
set ratio [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 ratio]
set_property -dict [list CONFIG.CONST_WIDTH {18} CONFIG.CONST_VAL {86856}] $ratio
set irq [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 irq]
set_property CONFIG.NUM_PORTS {16} $irq
set zero [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 irqzero]
set_property -dict [list CONFIG.CONST_WIDTH {1} CONFIG.CONST_VAL {0}] $zero
save_bd_design
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins ctrl/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins ctrl/M00_AXI] [get_bd_intf_pins dma/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins dma/M_AXI_MM2S] [get_bd_intf_pins mem/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins dma/M_AXI_S2MM] [get_bd_intf_pins mem/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins mem/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP0]
connect_bd_intf_net [get_bd_intf_pins dma/M_AXIS_MM2S] [get_bd_intf_pins pitch/s_axis]
connect_bd_intf_net [get_bd_intf_pins pitch/m_axis] [get_bd_intf_pins dma/S_AXIS_S2MM]
connect_bd_net [get_bd_pins ratio/dout] [get_bd_pins pitch/ratio_q16]
connect_bd_net [get_bd_pins ps7/FCLK_RESET0_N] [get_bd_pins rst/ext_reset_in]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins rst/slowest_sync_clk] [get_bd_pins ps7/M_AXI_GP0_ACLK] [get_bd_pins ps7/S_AXI_HP0_ACLK] [get_bd_pins pitch/aclk] [get_bd_pins dma/s_axi_lite_aclk] [get_bd_pins dma/m_axi_mm2s_aclk] [get_bd_pins dma/m_axi_s2mm_aclk]
foreach ic {ctrl mem} {
    connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins $ic/ACLK] [get_bd_pins $ic/S00_ACLK] [get_bd_pins $ic/M00_ACLK]
    connect_bd_net [get_bd_pins rst/interconnect_aresetn] [get_bd_pins $ic/ARESETN]
    connect_bd_net [get_bd_pins rst/peripheral_aresetn] [get_bd_pins $ic/S00_ARESETN] [get_bd_pins $ic/M00_ARESETN]
}
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins mem/S01_ACLK]
connect_bd_net [get_bd_pins rst/peripheral_aresetn] [get_bd_pins mem/S01_ARESETN] [get_bd_pins pitch/aresetn] [get_bd_pins dma/axi_resetn]
connect_bd_net [get_bd_pins dma/mm2s_introut] [get_bd_pins irq/In0]
connect_bd_net [get_bd_pins dma/s2mm_introut] [get_bd_pins irq/In1]
for {set i 2} {$i < 16} {incr i} {connect_bd_net [get_bd_pins irqzero/dout] [get_bd_pins irq/In$i]}
connect_bd_net [get_bd_pins irq/dout] [get_bd_pins ps7/IRQ_F2P]
assign_bd_address
validate_bd_design
save_bd_design
set wrapper [make_wrapper -files [get_files pitch_dma_bd.bd] -top]
add_files -norecurse $wrapper
set_property top pitch_dma_bd_wrapper [current_fileset]
puts "PROTOTYPE_VALIDATED: connectivity only, not a board-loadable audio design"
exit
