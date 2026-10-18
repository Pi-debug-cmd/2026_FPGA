#!/bin/bash
export PATH=/usr/bin:/bin:/d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin
cd /d/Tools_FPGA/workspace/voice_conversion_zynq7020/deploy_runtime || exit 9
FLAGS="-O3 -ffast-math -mcpu=cortex-a9 -mfpu=neon -mfloat-abi=hard"
arm-linux-gnueabihf-gcc $FLAGS deploy_llvc.c llvc_runtime_neon.c gemm_hw.c -o deploy_neon_red -lm
echo "GCC_EXIT=$?"
ls -la deploy_neon_red
