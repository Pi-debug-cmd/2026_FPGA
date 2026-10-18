#!/bin/sh
# Temporary live diagnostic for the verified K/V-fused model. No boot changes.
set -eu
BASE=/home/root/llvc_reduced_20261008
DIR=$BASE/experimental_20261009
RUN=/run/kvf-live
MODEL=$BASE/model.bin
BIN=${KVF_BIN:-$DIR/deploy_kv_fused}
export ALSA_CONFIG_PATH=${KVF_ALSA_CONFIG:-/home/root/native_llvc_trial_20261005/asound_neural.conf}

stop_chain() {
    for role in capture convert playback; do
        [ -f "$RUN/$role.pid" ] || continue
        pid=$(cat "$RUN/$role.pid")
        case "$pid" in ''|*[!0-9]*) continue;; esac
        [ -r "/proc/$pid/cmdline" ] || continue
        command=$(tr '\000' ' ' < "/proc/$pid/cmdline")
        case "$role:$command" in
            capture:*arecord*|convert:*deploy_kv_fused*|playback:*aplay*)
                kill "$pid" 2>/dev/null || true;;
        esac
    done
    sleep 1
    rm -f "$RUN"/*.pid "$RUN"/*.fifo
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
    amixer sset Capture 43,43 cap >/dev/null
    amixer sset 'ADC PCM' 190,190 >/dev/null
    amixer cset name='ADC Data Output Select' 1 >/dev/null
    amixer sset 'Left Output Mixer PCM' on >/dev/null
    amixer sset 'Right Output Mixer PCM' on >/dev/null
    amixer sset Headphone 119,119 >/dev/null
    amixer sset Playback 222,222 >/dev/null
}

status_chain() {
    for role in capture convert playback; do
        if [ -f "$RUN/$role.pid" ] && kill -0 "$(cat "$RUN/$role.pid")" 2>/dev/null; then
            echo "$role running pid=$(cat "$RUN/$role.pid")"
        else
            echo "$role stopped"
        fi
        tail -n 3 "$RUN/$role.log" 2>/dev/null || true
    done
}

case "${1:-}" in
    start)
        [ -x "$BIN" ] && [ -f "$MODEL" ] || exit 3
        mkdir -p "$RUN"
        stop_chain
        setup_mixer
        mkfifo "$RUN/input.fifo" "$RUN/output.fifo"
        nohup arecord -q -D neural_capture -t raw -f FLOAT_LE -r 16000 -c 1 \
            --period-size=1024 --buffer-size=4096 "$RUN/input.fifo" \
            >"$RUN/capture.log" 2>&1 & echo $! >"$RUN/capture.pid"
        nohup env LLVC_PIN=1 "$BIN" "$MODEL" <"$RUN/input.fifo" \
            >"$RUN/output.fifo" 2>"$RUN/convert.log" & echo $! >"$RUN/convert.pid"
        nohup aplay -q -D neural_play -t raw -f FLOAT_LE -r 16000 -c 1 \
            --period-size=1024 --buffer-size=16384 --start-delay=500000 \
            "$RUN/output.fifo" >"$RUN/playback.log" 2>&1 & echo $! >"$RUN/playback.pid"
        echo KVF_LIVE_STARTED
        ;;
    stop) stop_chain; echo KVF_LIVE_STOPPED;;
    status) status_chain;;
    *) echo 'usage: board_kvf_live.sh start|stop|status' >&2; exit 2;;
esac
