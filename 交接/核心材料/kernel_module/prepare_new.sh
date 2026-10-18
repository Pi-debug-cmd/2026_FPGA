#!/bin/bash
export PATH=/usr/bin:/bin:/d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
KDIR=/d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
cd $KDIR
yes "" | make oldconfig > /tmp/oldcfg.log 2>&1
echo "oldconfig exit=$?"
make modules_prepare > /tmp/prep_new.log 2>&1
echo "modules_prepare exit=$?"
tail -10 /tmp/prep_new.log
