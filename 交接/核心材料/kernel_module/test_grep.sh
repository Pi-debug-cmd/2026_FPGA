#!/bin/bash
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
echo "=== abis var ==="
abis=$(echo "(common,eabi)" | tr ',' '|')
echo "abis=[$abis]"
echo "=== direct grep ==="
grep -E "^[0-9A-Fa-fXx]+[[:space:]]+$abis" arch/arm/tools/syscall.tbl | head -5
echo "grep exit=$?"
echo "=== simpler grep ==="
grep -cE "common|eabi" arch/arm/tools/syscall.tbl
echo "=== show a syscall line with cat -A ==="
grep -E "restart_syscall" arch/arm/tools/syscall.tbl | head -2 | cat -A
