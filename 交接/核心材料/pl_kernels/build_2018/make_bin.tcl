open_project D:/g_build/proj/voice7020.xpr
set bit D:/g_build/proj/voice7020.runs/impl_1/zynq_wrapper.bit
set bin D:/g_build/proj/zynq_gemm_irq.bin
write_cfgmem -force -format BIN -interface SMAPx32 -loadbit "up 0x0 $bit" $bin
puts BIN_DONE
exit
