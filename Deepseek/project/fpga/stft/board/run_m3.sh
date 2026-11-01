#!/bin/sh
# Board-side M3 run: all-ARM reference vs PL-STFT path, same input, same model.
# Run from /tmp/vc after the stft_dma bitstream is loaded.
set -e
cd /tmp/vc

echo "== fpga =="
cat /sys/class/fpga_manager/fpga0/state
cat /sys/class/fpga_manager/fpga0/flags

echo "== all-ARM reference (vc_o64) =="
./vc_o64 4 native_s24 0 < in.raw > out_arm.raw 2> tel_arm.json
echo "rc=$?"
tail -c 400 tel_arm.json
echo

echo "== PL STFT path (vc_o64_pl) =="
VC_PL=1 ./vc_o64_pl 4 native_s24 0 < in.raw > out_pl.raw 2> tel_pl.json
echo "rc=$?"
tail -c 400 tel_pl.json
echo

echo "== sizes =="
ls -l out_arm.raw out_pl.raw
sha256sum out_arm.raw out_pl.raw
echo "== PL status (0x41200000) =="
# bits[31:16]=frames, bit3=busy, bit2=saturation, bit1=tlast_missing, bit0=tlast_unexpected
devmem 0x41200000 32 || echo "devmem unavailable"