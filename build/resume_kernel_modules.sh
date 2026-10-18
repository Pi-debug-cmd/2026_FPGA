#!/bin/bash
# Finish module symbol tables after the initial vmlinux-only build.
set -eu
root=/mnt/c/Users/World/Desktop/2026_FPGA
abi="$root/build/generated/kernel_abi_v2"
source_dir=$(cat "$abi/source_path.txt")
build_dir=$(cat "$abi/build_path.txt")
case "$source_dir:$build_dir" in /var/tmp/2026_fpga_kernel_20261010/source/*:/var/tmp/2026_fpga_kernel_20261010/build) ;; *) exit 2;; esac
make -C "$source_dir" O="$build_dir" -j2 ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- LOCALVERSION= modules >"$abi/kernel_modules_build.log" 2>&1
[ -s "$build_dir/Module.symvers" ]
cp "$build_dir/Module.symvers" "$abi/Module.symvers"
echo KERNEL_SYMBOL_VERSIONS_BUILT
