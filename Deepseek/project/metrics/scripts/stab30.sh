#!/bin/sh
# stab30.sh - 30 min continuous live run on the board.
#
# Chain: repeated 4 s input -> vc_live (300 ms blocks, --preset live) -> aplay.
# Records, in /tmp/vc/stab/:
#   blocks.jsonl  per-block JSON from vc_live stderr (+ the final summary line)
#   aplay.log     aplay stdout/stderr, "underrun" lines counted afterwards
#   mem.csv       RSS of vc_live + free memory, sampled every 30 s
#   env.txt       hardware / clock / version facts (one-shot)
#
# Nothing outside /tmp is written.  Run detached:  nohup sh stab30.sh &
set -u
SEC=${1:-1800}
B=${2:-300}
DIR=/tmp/vc/stab
VC=${VC:-/tmp/vc/vc_live}
IN=${IN:-/tmp/vc/in.raw}

mkdir -p "$DIR"
: > "$DIR/blocks.jsonl"
: > "$DIR/aplay.log"
echo "t_s,vc_rss_kb,mem_free_kb,mem_avail_kb,blocks" > "$DIR/mem.csv"

{
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "kernel=$(uname -r)"
  echo "machine=$(uname -m)"
  echo "vc_sha=$(sha256sum "$VC" | cut -d' ' -f1)"
  echo "vc_bytes=$(wc -c < "$VC")"
  echo "in_sha=$(sha256sum "$IN" | cut -d' ' -f1)"
  echo "block_ms=$B"
  echo "seconds=$SEC"
  echo "preset=live"
  echo "fpga_state=$(cat /sys/class/fpga_manager/fpga0/state 2>/dev/null)"
  echo "cpu0_khz=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null)"
} > "$DIR/env.txt"

HAVE=$(wc -c < "$IN")
REP=$(( (SEC * 256000 + HAVE - 1) / HAVE ))
[ "$REP" -lt 1 ] && REP=1
echo "input_copies=$REP" >> "$DIR/env.txt"

(
  i=0
  while [ "$i" -lt "$REP" ]; do cat "$IN"; i=$((i+1)); done
) | "$VC" "$SEC" native_s24 200 --stream "$B" --preset live 2> "$DIR/blocks.jsonl" \
  | aplay -D default -t raw -f S24_LE -r 32000 -c 2 --start-delay=64000 \
      > "$DIR/aplay.log" 2>&1 &
PIPE_PID=$!

T=0
while kill -0 "$PIPE_PID" 2>/dev/null; do
  VPID=$(pidof vc_live 2>/dev/null | cut -d' ' -f1)
  [ -z "$VPID" ] && VPID=$(pgrep -f 'vc_live' 2>/dev/null | head -1)
  RSS=0
  if [ -n "${VPID:-}" ] && [ -r "/proc/$VPID/status" ]; then
    RSS=$(awk '/^VmRSS:/{print $2}' "/proc/$VPID/status")
  fi
  MFREE=$(awk '/^MemFree:/{print $2}' /proc/meminfo)
  MAVAIL=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  NB=$(wc -l < "$DIR/blocks.jsonl")
  echo "$T,$RSS,$MFREE,$MAVAIL,$NB" >> "$DIR/mem.csv"
  sleep 30
  T=$((T + 30))
  echo "t=$T" >> "$DIR/progress.txt"
done
wait "$PIPE_PID"
RC=$?
echo "pipeline_done rc=$RC t=$T" >> "$DIR/env.txt"
echo "STAB_DONE" >> "$DIR/env.txt"
