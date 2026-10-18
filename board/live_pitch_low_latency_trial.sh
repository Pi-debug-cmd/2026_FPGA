#!/bin/sh
# Finite PS-only trial. Temporarily enable signal routes; restore mixer on exit.
set -eu
RATIO=${1:-65536}
SECONDS_TO_RUN=${2:-20}
BIN=/tmp/codex_pitch_fixed
case "$RATIO:$SECONDS_TO_RUN" in *[!0-9:]*|:*|*:) echo "integer arguments required" >&2; exit 2;; esac
[ "$RATIO" -ge 32768 ] && [ "$RATIO" -le 131072 ] || exit 2
[ "$SECONDS_TO_RUN" -ge 1 ] && [ "$SECONDS_TO_RUN" -le 60 ] || exit 2
[ -x "$BIN" ] || exit 3
RUN=/tmp/codex_pitch_trial_v5_${RATIO}
# mkdir is the ownership lock. A preexisting directory requires manual inspection.
mkdir "$RUN" || { echo "trial directory already exists; inspect before retry" >&2; exit 3; }
capture_pid= process_pid= playback_pid=
cleanup() {
    for pid in $capture_pid $process_pid $playback_pid; do
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    done
    rm -f "$RUN/input.fifo" "$RUN/output.fifo"
    if [ -f "$RUN/mixer_before.state" ]; then
        alsactl -f "$RUN/mixer_before.state" restore 0 >"$RUN/mixer_restore.log" 2>&1 ||
            echo "MIXER_RESTORE_FAILED: inspect $RUN/mixer_restore.log" >&2
    fi
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
alsactl -f "$RUN/mixer_before.state" store 0
amixer sset 'Left Input Mixer Boost' on >"$RUN/mixer_setup.log"
amixer sset 'Right Boost Mixer RINPUT1' on >>"$RUN/mixer_setup.log"
amixer sset 'Right Input Mixer Boost' on >>"$RUN/mixer_setup.log"
amixer cset name='ADC Data Output Select' 1 >>"$RUN/mixer_setup.log"
amixer sset 'Left Output Mixer PCM' on >>"$RUN/mixer_setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/mixer_setup.log"
# Keep the audible v4 routes/gain; reduce only playback buffering.
amixer sset 'Headphone Playback ZC' on >>"$RUN/mixer_setup.log"
amixer sset Headphone 105,105 >>"$RUN/mixer_setup.log"
amixer sset Playback 230,230 >>"$RUN/mixer_setup.log"
amixer sset 'Left Boost Mixer LINPUT1' on >>"$RUN/mixer_setup.log"
amixer sset 'Left Input Boost Mixer LINPUT1' 1 >>"$RUN/mixer_setup.log"
mkfifo "$RUN/input.fifo" "$RUN/output.fifo"
arecord -q -D hw:0,1 -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=4096 -d "$SECONDS_TO_RUN" "$RUN/input.fifo" \
    >"$RUN/capture.log" 2>&1 & capture_pid=$!
"$BIN" "$RATIO" native_s24 <"$RUN/input.fifo" >"$RUN/output.fifo" \
    2>"$RUN/process.log" & process_pid=$!
aplay -v -D default -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=3072 --start-delay=32000 "$RUN/output.fifo" \
    >"$RUN/playback.log" 2>&1 & playback_pid=$!
echo "TRIAL_STARTED ratio_q16=$RATIO seconds=$SECONDS_TO_RUN hardware_rate=32000"
sleep 1
cat /proc/asound/card0/pcm1c/sub0/hw_params >"$RUN/capture_hw_params.log"
cat /proc/asound/card0/pcm0p/sub0/hw_params >"$RUN/playback_hw_params.log"
wait "$capture_pid"; capture_pid=
wait "$process_pid"; process_pid=
wait "$playback_pid"; playback_pid=
echo "TRIAL_COMPLETED"
echo "capture_overruns=$(grep -c overrun "$RUN/capture.log" || true)"
echo "playback_underruns=$(grep -c underrun "$RUN/playback.log" || true)"
cat "$RUN/process.log"
# Logs intentionally preserved; do not remove this directory until reviewed.
