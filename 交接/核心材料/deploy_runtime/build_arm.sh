#!/bin/bash
export PATH=/usr/bin:/bin:/d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/deploy_runtime
CC=arm-linux-gnueabihf-gcc
FLAGS="-O2 -mcpu=cortex-a9 -mfpu=neon -mfloat-abi=hard"
$CC $FLAGS -o deploy_llvc_arm_hw deploy_llvc.c llvc_runtime.c gemm_hw.c -lm
echo "hw build exit=$?"
$CC $FLAGS -o deploy_llvc_arm_ref deploy_llvc.c llvc_runtime.c gemm_ref.c -lm
echo "ref build exit=$?"
ls -la deploy_llvc_arm_hw deploy_llvc_arm_ref
