#!/bin/bash
MINGW=/d/Vivado/Vivado/2018.3/msys64/mingw64/bin
export PATH=$MINGW:$PATH
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src/scripts/basic
gcc -O2 -o /tmp/fixdep.exe fixdep.c 2>/tmp/gcc_err.txt
echo "compile exit: $?"
cat /tmp/gcc_err.txt
ls -la /tmp/fixdep.exe 2>&1
echo "=== run ==="
/tmp/fixdep.exe /tmp/t.d out.o "cmdline" 2>&1
echo "=== run exit: $? ==="
