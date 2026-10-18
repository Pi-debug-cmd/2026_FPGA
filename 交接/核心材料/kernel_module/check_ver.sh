#!/bin/bash
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
echo "=== source version ==="
head -5 Makefile
echo "=== clock_getres_time64 definition ==="
grep -rln "clock_getres_time64" arch/arm/include include 2>/dev/null | head
echo "=== generated unistd present? ==="
ls -la include/generated/uapi/asm-generic/unistd.h 2>&1
ls -la arch/arm/include/generated/ 2>&1 | head
