#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir=${1:?pass prepared Linux source directory}
build_dir=${2:?pass prepared matching kernel build directory}
out="$root/build/generated/world_exp_driver"
mkdir -p "$out"
cp "$root/src/kernel/world_exp_dma.c" "$root/src/kernel/world_exp_ioctl.h" "$out/"
printf 'obj-m += world_exp_dma.o\n' > "$out/Makefile"
make -C "$source_dir" O="$build_dir" M="$out" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- LOCALVERSION= modules
