#!/bin/sh
# Ten-second interface test: silent playback; mic conversion is discarded.
set -eu
DIR=/home/root/native_llvc_trial_20261005
export ALSA_CONFIG_PATH="$DIR/asound_neural.conf"
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
aplay -q -D neural_play -t raw -f S16_LE -r 16000 -c 1 -d 10 --period-size=208 --buffer-size=832 /dev/zero > "$DIR/duplex_silent_playback.log" 2>&1 &
play_pid=$!
trap 'kill "$play_pid" 2>/dev/null || true' EXIT
arecord -q -D neural_capture -t raw -f S16_LE -r 16000 -c 1 -d 10 --period-size=208 --buffer-size=832 2> "$DIR/duplex_capture.log" |
    "$DIR/native_llvc_small96_stream_arm" --stream "$DIR/small96_step2400.f32" "$DIR/duplex_mic_compute_status.json" > /dev/null 2> "$DIR/duplex_native.log"
wait "$play_pid"
cat "$DIR/duplex_mic_compute_status.json"
echo DUPLEX_INTERFACE_TEST_FINISHED
