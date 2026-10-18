#!/bin/bash
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
U=arch/arm/include/generated/uapi/asm
rm -f $U/unistd-eabi.h $U/.unistd-eabi.h.cmd $U/unistd-oabi.h $U/.unistd-oabi.h.cmd
sh ./scripts/syscallhdr.sh --abis common,eabi --offset __NR_SYSCALL_BASE arch/arm/tools/syscall.tbl $U/unistd-eabi.h
echo "eabi exit=$?"
sh ./scripts/syscallhdr.sh --abis common,oabi --offset __NR_OABI_SYSCALL_BASE arch/arm/tools/syscall.tbl $U/unistd-oabi.h
echo "oabi exit=$?"
wc -l $U/unistd-eabi.h $U/unistd-oabi.h
grep -c clock_getres $U/unistd-eabi.h
