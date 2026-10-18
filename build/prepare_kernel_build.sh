#!/bin/bash
# Build symbol CRCs for the current ARM kernel. Never installs or flashes a kernel.
set -eu
archive=$1
config=$2
artifacts=$3
job=/var/tmp/2026_fpga_kernel_20261010
case "$artifacts" in /mnt/c/Users/World/Desktop/2026_FPGA/build/generated/*) ;; *) exit 2;; esac
[ ! -e "$job" ] || { echo 'Build workspace already exists; inspect before resuming' >&2; exit 2; }
mkdir "$job"
mkdir -p "$artifacts"
scripts=$(cd "$(dirname "$0")" && pwd)
source_dir=$(python3 "$scripts/prepare_kernel_sources.py" "$archive" "$job/source" "$config" "$artifacts/source_manifest.json")
mkdir "$job/build"
gzip -dc "$config" >"$job/build/.config"
make -C "$source_dir" O="$job/build" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- LOCALVERSION= olddefconfig >"$artifacts/kernel_prepare.log" 2>&1
release=$(make -s -C "$source_dir" O="$job/build" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- LOCALVERSION= kernelrelease)
[ "$release" = 5.15.0-xilinx ] || { echo "KERNEL_RELEASE_MISMATCH=$release" >&2; exit 3; }
cp "$job/build/.config" "$artifacts/effective.config"
printf '%s\n' "$source_dir" >"$artifacts/source_path.txt"
printf '%s\n' "$job/build" >"$artifacts/build_path.txt"
echo "KERNEL_BUILD_STARTED release=$release"
make -C "$source_dir" O="$job/build" -j2 ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- LOCALVERSION= vmlinux modules >"$artifacts/kernel_build.log" 2>&1
[ -s "$job/build/Module.symvers" ]
cp "$job/build/Module.symvers" "$artifacts/Module.symvers"
echo KERNEL_SYMBOL_VERSIONS_BUILT
