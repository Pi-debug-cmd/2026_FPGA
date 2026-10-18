#!/bin/bash
export PATH=/usr/bin:/bin:/d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin
echo "=== compiler default ==="
echo 'void f(){ __asm__ volatile("isb"); }' > /tmp/t.c
arm-linux-gnueabihf-gcc -c /tmp/t.c -o /tmp/t.o 2>&1 && echo DEFAULT_SUPPORTS_ISB
echo "=== with -march=armv7-a ==="
arm-linux-gnueabihf-gcc -march=armv7-a -c /tmp/t.c -o /tmp/t.o 2>&1 && echo ARMV7_SUPPORTS_ISB
echo "=== arch/arm/Makefile march ==="
grep -nE "march|CPU_32v7|LINUX_ARM_ARCH" /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src/arch/arm/Makefile | head -15
