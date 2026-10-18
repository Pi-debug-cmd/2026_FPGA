#!/bin/bash
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
{
echo "=== grep common count ==="
grep -c "common" arch/arm/tools/syscall.tbl
echo "exit=$?"
echo "=== sed line 15 ==="
sed -n "15p" arch/arm/tools/syscall.tbl | cat -A
echo "=== grep restart ==="
grep restart arch/arm/tools/syscall.tbl | head -2
} > /tmp/g.txt 2>&1
echo DONE
