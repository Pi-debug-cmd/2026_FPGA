#!/bin/bash
MINGW=/d/Vivado/Vivado/2018.3/msys64/mingw64/bin
export PATH=$MINGW:$PATH
mkdir -p /tmp/fdtest && cd /tmp/fdtest
cp /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src/scripts/basic/fixdep.c .
gcc -O2 -MD -o fixdep.exe fixdep.c 2>gcc_err.txt
echo "gcc exit=$?"
echo "=== depfile size ==="
ls -la fixdep.d
echo "=== fstat size vs actual bytes ==="
wc -c fixdep.d
echo "=== run fixdep on its own dep ==="
./fixdep.exe fixdep.d fixdep.exe "cmdline" 2>&1 | head -10
echo "exit=$?"
