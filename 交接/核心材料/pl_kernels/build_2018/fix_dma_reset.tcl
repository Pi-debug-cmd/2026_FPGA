open_project D:/g_build/proj/voice7020.xpr
open_bd_design [get_files zynq.bd]
connect_bd_net [get_bd_pins ctrl_rst/peripheral_aresetn] [get_bd_pins audio_dma_ic/ARESETN]
save_bd_design
validate_bd_design
puts DMA_RESET_FIXED
exit
