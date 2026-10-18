#!/bin/bash
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
rm -f arch/arm/include/generated/uapi/asm/unistd-eabi.h
sh ./scripts/syscallhdr.sh --abis common,eabi --offset __NR_SYSCALL_BASE arch/arm/tools/syscall.tbl arch/arm/include/generated/uapi/asm/unistd-eabi.h
echo "exit=$?"
echo "=== output size ==="
wc -l arch/arm/include/generated/uapi/asm/unistd-eabi.h
head -15 arch/arm/include/generated/uapi/asm/unistd-eabi.h
echo "=== syscallhdr.sh grep/awk ==="
grep -nE 'grep|awk|sed|while|read' scripts/syscallhdr.sh | head -15
