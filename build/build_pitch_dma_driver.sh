#!/bin/bash
set -eu
root=/mnt/c/Users/World/Desktop/2026_FPGA
abi="$root/build/generated/kernel_abi_v2"
out="$root/build/generated/pitch_dma_driver"
source_dir=$(cat "$abi/source_path.txt")
build_dir=$(cat "$abi/build_path.txt")
case "$source_dir:$build_dir" in /var/tmp/2026_fpga_kernel_20261010/source/*:/var/tmp/2026_fpga_kernel_20261010/build) ;; *) exit 2;; esac
[ -s "$build_dir/Module.symvers" ]
mkdir -p "$out"
cp "$root/src/kernel/pitch_dma_proxy.c" "$root/src/kernel/pitch_dma_ioctl.h" "$root/src/kernel/Kbuild" "$out/"
make -C "$source_dir" O="$build_dir" M="$out" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- LOCALVERSION= modules >"$root/report/pitch_dma_driver_build.log" 2>&1
arm-linux-gnueabihf-gcc -std=c11 -D_GNU_SOURCE -O2 -Wall -Wextra -Werror "$root/src/ps/pitch_dma_stream.c" -o "$out/pitch_dma_stream"
echo PITCH_DMA_DRIVER_COMPILED
