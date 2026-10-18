#!/bin/sh
MODE=/run/voice-mode
STATUS=/tmp/voice-status.json
LOG=/tmp/voice-live.log

stop_audio() {
    for p in $(pidof arecord aplay voice_stream 2>/dev/null); do
        kill -9 "$p" 2>/dev/null || true
    done
}

case "$1" in
    start)
        [ -x /usr/local/bin/voice_stream ] || exit 1
        /etc/init.d/music-button stop
        stop_audio
        amixer sset 'Left Boost Mixer LINPUT1' on >/dev/null
        amixer sset 'Left Input Mixer Boost' on >/dev/null
        amixer sset 'Left Boost Mixer LINPUT2' off >/dev/null
        amixer sset 'Left Input Boost Mixer LINPUT2' 0 >/dev/null
        amixer sset 'Left Input Boost Mixer LINPUT1' 1 >/dev/null
        amixer sset 'Right Boost Mixer RINPUT1' on >/dev/null
        amixer sset 'Right Input Mixer Boost' on >/dev/null
        amixer sset 'Capture' 35,35 cap >/dev/null
        amixer sset 'ADC PCM' 190,190 >/dev/null
        amixer cset name='ADC Data Output Select' 1 >/dev/null
        case "${2:-up}" in
            bypass) printf 'bypass\n' > "$MODE" ;;
            target) printf 'target 193.07\n' > "$MODE" ;;
            *) printf 'shift 4\n' > "$MODE" ;;
        esac
        rm -f "$STATUS"
        sh -c 'arecord -q -D capture -t raw -f S24_LE -r 44100 -c 2 --period-size=256 --buffer-size=1024 | /usr/local/bin/voice_stream --semitones 0 --control /run/voice-mode --status /tmp/voice-status.json | aplay -q -D default -t raw -f S24_LE -r 44100 -c 2 --period-size=256 --buffer-size=1024' > "$LOG" 2>&1 &
        echo $! > /run/voice-live.pid
        ;;
    bypass) printf 'bypass\n' > "$MODE" ;;
    up) printf 'shift 4\n' > "$MODE" ;;
    down) printf 'shift -4\n' > "$MODE" ;;
    target) printf 'target 193.07\n' > "$MODE" ;;
    mute) printf 'mute\n' > "$MODE" ;;
    stop) stop_audio; rm -f /run/voice-live.pid ;;
    status) cat "$STATUS"; cat "$LOG"; pidof arecord voice_stream aplay ;;
    *) echo 'Usage: voice-live.sh start [up|bypass|target] | bypass|up|down|target|mute|stop|status'; exit 1 ;;
esac
