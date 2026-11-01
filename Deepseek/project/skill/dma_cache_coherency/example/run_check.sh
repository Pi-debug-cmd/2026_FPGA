#!/bin/sh
# Board-side one-shot coherency check. Exit 0 = the DMA path is coherent.
#   sh run_check.sh [dma_base] [ratio_addr]
set -e
DMA="${1:-0x40400000}"
RATIO="${2:-0x41200000}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$HERE/bin/dma_roundtrip"
[ -x "$BIN" ] || { echo "missing $BIN (cross-compile it, see README)"; exit 2; }

echo "== fpga_manager state =="
cat /sys/class/fpga_manager/fpga0/state

echo "== single first-transfer check (the one that fails if L2 is dirty) =="
"$BIN" --dma "$DMA" --ratio-addr "$RATIO" --ratio 65536 \
       --words 128000 --chunk 4096 --pattern ramp || true

echo "== repeated, fresh buffers each time (bug must NOT come back) =="
"$BIN" --dma "$DMA" --words 65536 --chunk 4096 --pattern prbs --repeat 10 --realloc
RC=$?
echo "rc=$RC"
if [ "$RC" -eq 0 ]; then
  echo "VERDICT: coherent"
else
  echo "VERDICT: not coherent -- open diag_checklist.md section 1"
fi
exit "$RC"
