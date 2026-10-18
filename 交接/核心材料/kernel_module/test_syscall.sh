#!/bin/bash
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
echo "=== run syscallhdr manually ==="
sh ./scripts/syscallhdr.sh --abis common,eabi --offset __NR_SYSCALL_BASE arch/arm/tools/syscall.tbl 2>&1 | head -20
echo "=== exit: $? ==="
echo "=== syscall.tbl head ==="
head -10 arch/arm/tools/syscall.tbl
