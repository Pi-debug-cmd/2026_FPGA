#!/bin/bash
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_module
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- V=1 clean > /dev/null 2>&1
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- V=1 > /tmp/mod_v.log 2>&1
echo "exit=$?"
grep -E "gcc.*gemm_dma|march|isb" /tmp/mod_v.log | head -5
