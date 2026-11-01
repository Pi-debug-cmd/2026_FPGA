#!/bin/sh
# One-shot load + acceptance check on the board (root). Exit 0 = overlay is live
# and every register read back exactly what was written.
#
#   sh run_on_board.sh /tmp/pl_x audio_pitch_dma_2018_swap.bin
#
# Layout expected in $RUN:
#   $1/audio_pitch_dma_2018_swap.bin   byte-swapped image (make_swap.py output)
#   $1/factory_restore_swap.bin        rollback image (prepare_recovery.py output)
#   $1/overlay.py  $1/regtool.py  $1/regtool  $1/regmap.json
set -e

RUN="${1:-/tmp/pl_x}"
IMG="${2:-audio_pitch_dma_2018_swap.bin}"

cd "$RUN"

echo "== 0. preconditions =="
[ -f "$IMG" ] || { echo "missing $IMG"; exit 2; }
[ -f factory_restore_swap.bin ] || echo "WARN: no rollback image; cold reboot is the only way back"
cat /sys/class/fpga_manager/fpga0/state

echo "== 1. load =="
python3 overlay.py --image "$RUN/$IMG" --run-dir "$RUN" \
  --consumers consumers.txt \
  --rebind "41600000.i2c 43c20000.axi_dynclk 43c50000.i2s_receiver 43c60000.i2s_transmitter 43c40000.audio_formatter xlnx_snd_card.0.auto" \
  --pause music-button-listener

echo "== 2. register acceptance =="
if python3 -c 'import mmap' 2>/dev/null; then
  python3 regtool.py regmap.json --json "$RUN/reg_check.json"
else
  echo "python3 has no mmap -> static C tool"
  ./regtool --base 0x41200000 \
            --check 0x00:18:86856,65536,131072,32768,86856 \
            --check 0x08:1:0,1
fi

echo "== 3. evidence =="
dmesg | tail -20
ls -l "$RUN"/switch_state.json "$RUN"/reg_check.json 2>/dev/null || true
