# =====================================================================
# Stage 4: gemm 1.1, ctrl_ic (1x5), 3 dedicated HP ICs.
# =====================================================================
open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]

# ---- gemm ----
set gemm [create_bd_cell -type ip -vlnv local.user:hls:gemm_s8:1.1 gemm]

# ---- control interconnect: GP0 -> 5 slaves ----
set cic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 ctrl_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {5}] $cic

# ---- 3 dedicated HP interconnects (1x1 each, no address overlap) ----
set wic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 w_hp_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $wic
set iicd [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 i_hp_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $iicd
set oic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 o_hp_ic]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $oic

save_bd_design
puts STAGE4_INST_DONE
exit
