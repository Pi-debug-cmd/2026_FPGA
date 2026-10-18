#!/bin/bash
set -e
MINGW=/d/Vivado/Vivado/2018.3/msys64/mingw64/bin
export PATH=/d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_module/make_extract/usr/bin:$MINGW:$PATH:/d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
export HOSTCC=gcc
MAKE=make
KDIR=/d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src
cd $KDIR
yes "" | $MAKE ARCH=arm CROSS_COMPILE=$CROSS_COMPILE HOSTCC=$HOSTCC oldconfig
$MAKE ARCH=arm CROSS_COMPILE=$CROSS_COMPILE HOSTCC=$HOSTCC modules_prepare
echo "MODULES_PREPARE_DONE"
