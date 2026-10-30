#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir=${1:?pass prepared Linux source directory}
build_dir=${2:?pass prepared matching kernel build directory}
out="$root/build/generated/world_minphase_driver"
mkdir -p "$out"
cp "$root/src/kernel/world_minphase_dma.c" "$root/src/kernel/world_minphase_ioctl.h" "$out/"
printf 'obj-m += world_minphase_dma.o\n' > "$out/Makefile"
make -C "$source_dir" O="$build_dir" M="$out" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- LOCALVERSION= modules
