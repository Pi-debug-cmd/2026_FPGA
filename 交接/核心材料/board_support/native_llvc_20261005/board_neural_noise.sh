#!/bin/sh
# Reversible live trial only. No boot changes, no files of user speech.
set -eu
DIR=/home/root/native_llvc_trial_20261005
export ALSA_CONFIG_PATH="$DIR/asound_neural.conf"
RUN=/run/voice-neural-live
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
    rm -f "$RUN/watchdog.pid" "$RUN/capture.pid" "$RUN/convert.pid" "$RUN/playback.pid" "$RUN/input.fifo" "$RUN/output.fifo"
}
if [ "$#" -ne 1 ]; then echo 'Usage: board_neural_live.sh start|stop|status' >&2; exit 2; fi
case "$1" in
    stop) stop_live; echo NEURAL_LIVE_STOPPED;;
    status)
        for role in capture convert playback; do
            if [ -f "$RUN/$role.pid" ]; then
                pid=$(cat "$RUN/$role.pid")
                if kill -0 "$pid" 2>/dev/null; then echo "$role running pid=$pid"; else echo "$role exited"; fi
            else echo "$role not started"; fi
        done
        [ ! -f "$RUN/status.json" ] || cat "$RUN/status.json"
        ;;
    start)
        [ -f "$DIR/small96_noise_step9200.f32" ]
        [ -x "$DIR/native_llvc_small96_meter_arm" ]
        mkdir -p "$RUN"
        stop_live
        rm -f "$RUN/status.json" "$RUN/watchdog_reason.json"
        /etc/init.d/music-button stop >/dev/null 2>&1 || true
        /usr/local/bin/voice-live.sh stop >/dev/null 2>&1 || true
        amixer sset 'Left Boost Mixer LINPUT1' on >/dev/null
        amixer sset 'Left Input Mixer Boost' on >/dev/null
        amixer sset 'Left Boost Mixer LINPUT2' off >/dev/null
        amixer sset 'Left Input Boost Mixer LINPUT2' 0 >/dev/null
        amixer sset 'Left Input Boost Mixer LINPUT1' 1 >/dev/null
        amixer sset 'Right Boost Mixer RINPUT1' on >/dev/null
        amixer sset 'Right Input Mixer Boost' on >/dev/null
        amixer sset Capture 35,35 cap >/dev/null
        amixer sset 'ADC PCM' 190,190 >/dev/null
        amixer cset name='ADC Data Output Select' 1 >/dev/null
        amixer sset 'Left Output Mixer PCM' on >/dev/null
        amixer sset 'Right Output Mixer PCM' on >/dev/null
        amixer sset Headphone 101,101 >/dev/null
        amixer sset Playback 222,222 >/dev/null
        mkfifo "$RUN/input.fifo" "$RUN/output.fifo"
        nohup arecord -q -D neural_capture -t raw -f S16_LE -r 16000 -c 1 --period-size=208 --buffer-size=832 "$RUN/input.fifo" > "$RUN/capture.log" 2>&1 &
        echo $! > "$RUN/capture.pid"
        nohup "$DIR/native_llvc_small96_meter_arm" --stream "$DIR/small96_noise_step9200.f32" "$RUN/status.json" < "$RUN/input.fifo" > "$RUN/output.fifo" 2> "$RUN/convert.log" &
        echo $! > "$RUN/convert.pid"
        nohup aplay -q -D neural_play -t raw -f S16_LE -r 16000 -c 1 --period-size=208 --buffer-size=832 --start-delay=39000 "$RUN/output.fifo" > "$RUN/playback.log" 2>&1 &
        echo $! > "$RUN/playback.pid"
        nohup python3 -u "$DIR/live_watchdog.py" > "$RUN/watchdog.log" 2>&1 &
        echo $! > "$RUN/watchdog.pid"
        echo NEURAL_LIVE_START_REQUESTED
        ;;
    *) exit 2;;
esac
