#!/bin/sh
set -eu
DIR=/home/root/native_llvc_trial_20261005
/etc/init.d/music-button stop
for p in $(pidof arecord aplay voice_stream 2>/dev/null); do kill -9 "$p" 2>/dev/null || true; done
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
if [ "$#" -eq 0 ]; then echo 'Need capture|original|converted' >&2; exit 2; fi
case "$1" in
    probe)
        arecord -q -D capture -t raw -f S16_LE -r 16000 -c 1 -d 1 "$DIR/capture_format_probe.raw"
        wc -c "$DIR/capture_format_probe.raw"
        ;;
    capture)
        echo BOARD_MIC_CAPTURE_START_5_SECONDS
        arecord -q -D capture -t raw -f S16_LE -r 16000 -c 1 -d 5 "$DIR/mic_16k_s16.raw"
        echo BOARD_MIC_CAPTURE_COMPLETE
        python3 -u "$DIR/run_board_checks.py" capture
        ;;
    original|converted)
        amixer sset 'Left Output Mixer PCM' on >/dev/null
        amixer sset 'Right Output Mixer PCM' on >/dev/null
        amixer sset Headphone 95,95 >/dev/null
        amixer sset Playback 210,210 >/dev/null
        aplay "$DIR/mic_$1.wav"
        ;;
    *)
        echo 'Usage: mic_trial.sh capture|original|converted' >&2
        exit 2
        ;;
esac