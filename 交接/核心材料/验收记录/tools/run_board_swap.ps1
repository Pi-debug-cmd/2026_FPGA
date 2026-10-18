$pyCode = "t=bytes(int(format(i,'08b')[::-1],2) for i in range(256));d=open('/tmp/zynq_gemm_irq.bin','rb').read();open('/tmp/zynq_gemm_swap.bin','wb').write(bytes(map(t.__getitem__,d)))"
# Shell command: python3 -c "<code>" ; wrap in double quotes for the board shell
$cmd = 'python3 -c "' + $pyCode + '"; echo PY=$?; sha256sum /tmp/zynq_gemm_swap.bin; wc -c /tmp/zynq_gemm_swap.bin'
& 'D:\总进度\7020验收记录\tools\serial_run.ps1' -Command $cmd -TimeoutSeconds 60 -LogPath 'D:\总进度\7020验收记录\B_PL音频\43_board_swap.log'
