#!/bin/bash
export PATH=/usr/bin:/bin:/d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_module
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- > /tmp/mod_build.log 2>&1
echo "build exit=$?"
tail -20 /tmp/mod_build.log
echo "=== artifacts ==="
ls -la *.ko 2>&1
