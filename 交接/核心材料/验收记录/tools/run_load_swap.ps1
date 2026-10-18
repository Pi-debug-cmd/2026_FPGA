$cmd = 'cp /tmp/zynq_gemm_swap.bin /lib/firmware/zynq_gemm_swap.bin && echo 0 > /sys/class/fpga_manager/fpga0/flags && echo zynq_gemm_swap.bin > /sys/class/fpga_manager/fpga0/firmware && sleep 3 && echo STATE=$(cat /sys/class/fpga_manager/fpga0/state) && dmesg | tail -n 8'
& 'D:\总进度\7020验收记录\tools\serial_run.ps1' -Command $cmd -TimeoutSeconds 60 -LogPath 'D:\总进度\7020验收记录\B_PL音频\44_load_swap.log'
