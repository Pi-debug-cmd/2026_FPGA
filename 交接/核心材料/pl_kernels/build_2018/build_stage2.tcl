# =====================================================================
# Stage 2: instantiate audio components (flat) and wire them.
# =====================================================================
open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]

# ---- audio components ----
set af [create_bd_cell -type ip -vlnv xilinx.com:ip:audio_formatter:1.0 audio_formatter]
set_property -dict [list CONFIG.C_MAX_NUM_CHANNELS_MM2S {2} CONFIG.C_MAX_NUM_CHANNELS_S2MM {2}] $af

set irx [create_bd_cell -type ip -vlnv xilinx.com:ip:i2s_receiver:1.0 i2s_receiver]
set_property CONFIG.C_32BIT_LR {0} $irx

set itx [create_bd_cell -type ip -vlnv xilinx.com:ip:i2s_transmitter:1.0 i2s_transmitter]

set dclk [create_bd_cell -type ip -vlnv digilentinc.com:ip:axi_dynclk:1.2 audio_dynclk]

set arst [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 audio_rst]
set vor [create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 bclk_or]
set_property -dict [list CONFIG.C_OPERATION {or} CONFIG.C_SIZE {1}] $vor

set aic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 audio_dma_ic]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $aic

save_bd_design
puts STAGE2_INST_DONE
exit
