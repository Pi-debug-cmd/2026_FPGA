#!/bin/bash
export PATH=/usr/bin:/bin:/d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_module
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- clean > /dev/null 2>&1
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- KCFLAGS="-march=armv7-a" V=1 > /tmp/mod_v2.log 2>&1
echo "exit=$?"
grep -E "gemm_dma.o" /tmp/mod_v2.log | head -3
echo "=== ko? ==="
ls -la *.ko 2>&1
