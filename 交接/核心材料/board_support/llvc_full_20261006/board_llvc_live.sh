#!/bin/sh
# Full LLVC target voice conversion live trial.
# Reversible: no boot changes, no SD changes, no recorded user speech kept.
# Usage: board_llvc_live.sh start-ref | start-hw | stop | status
set -eu
DIR=/home/root/llvc_full_20261006
export ALSA_CONFIG_PATH="$DIR/asound_neural.conf"
RUN=/run/llvc-full
BIT="$DIR/zynq_wrapper.bit"
MODEL="$DIR/llvc_deploy_model.bin"

stop_live() {
    for role in watchdog capture convert playback; do
        if [ -f "$RUN/$role.pid" ]; then
            pid=$(cat "$RUN/$role.pid")
            case "$pid" in ''|*[!0-9]*) continue;; esac
            if [ -r "/proc/$pid/cmdline" ]; then
                command=$(tr '\000' ' ' < "/proc/$pid/cmdline")
                case "$command" in *"$DIR/"*|*"$RUN/"*) kill "$pid" 2>/dev/null || true;; esac
            fi
        fi
    done
    sleep 1
    rm -f "$RUN"/*.pid "$RUN/input.fifo" "$RUN/output.fifo"
}

setup_mixer() {
    /etc/init.d/music-button stop >/dev/null 2>&1 || true
    /usr/local/bin/voice-live.sh stop >/dev/null 2>&1 || true
    amixer sset 'Left Boost Mixer LINPUT1' on >/dev/null
    amixer sset 'Left Input Mixer Boost' on >/dev/null
    amixer sset 'Left Boost Mixer LINPUT2' off >/dev/null
    amixer sset 'Left Input Boost Mixer LINPUT2' 0 >/dev/null
    amixer sset 'Left Input Boost Mixer LINPUT1' 1 >/dev/null
    amixer sset 'Right Boost Mixer RINPUT1' on >/dev/null
    amixer sset 'Right Input Mixer Boost' on >/dev/null
    amixer sset Capture 43,43 cap >/dev/null
    amixer sset 'ADC PCM' 190,190 >/dev/null
    amixer cset name='ADC Data Output Select' 1 >/dev/null
    amixer sset 'Left Output Mixer PCM' on >/dev/null
    amixer sset 'Right Output Mixer PCM' on >/dev/null
    amixer sset Headphone 119,119 >/dev/null
    amixer sset Playback 222,222 >/dev/null
}

start_chain() {
    BIN="$1"
    [ -x "$BIN" ]
    [ -f "$MODEL" ]
    mkdir -p "$RUN"
    stop_live
    setup_mixer
    mkfifo "$RUN/input.fifo" "$RUN/output.fifo"
    # raw float32 mono 16k; ALSA plug converts to/from the codec rate.
    nohup arecord -q -D neural_capture -t raw -f FLOAT_LE -r 16000 -c 1 \
        --period-size=208 --buffer-size=832 "$RUN/input.fifo" > "$RUN/capture.log" 2>&1 &
    echo $! > "$RUN/capture.pid"
    nohup "$BIN" "$MODEL" < "$RUN/input.fifo" > "$RUN/output.fifo" 2> "$RUN/convert.log" &
    echo $! > "$RUN/convert.pid"
    nohup aplay -q -D neural_play -t raw -f FLOAT_LE -r 16000 -c 1 \
        --period-size=208 --buffer-size=832 --start-delay=39000 "$RUN/output.fifo" > "$RUN/playback.log" 2>&1 &
    echo $! > "$RUN/playback.pid"
    echo LLVC_LIVE_STARTED
}

if [ "$#" -ne 1 ]; then echo 'Usage: board_llvc_live.sh start-ref|start-hw|stop|status' >&2; exit 2; fi
case "$1" in
    stop) stop_live; echo LLVC_LIVE_STOPPED;;
    status)
        for role in capture convert playback; do
            if [ -f "$RUN/$role.pid" ]; then
                pid=$(cat "$RUN/$role.pid")
                if kill -0 "$pid" 2>/dev/null; then echo "$role running pid=$pid"; else echo "$role exited"; fi
            else echo "$role not started"; fi
        done
        for log in capture convert playback; do
            echo "--- $log.log ---"; tail -n 5 "$RUN/$log.log" 2>/dev/null || true
        done
        ;;
    start-ref) start_chain "$DIR/deploy_llvc_arm_ref";;
    start-hw) start_chain "$DIR/deploy_neon";;
    *) echo 'Usage: board_llvc_live.sh start-ref|start-hw|stop|status' >&2; exit 2;;
esac
