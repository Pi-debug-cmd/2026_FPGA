#!/bin/sh

LOG_FILE=/tmp/music-button.log

aplay_pids=$(pidof aplay)
if [ -n "$aplay_pids" ]; then
    for aplay_pid in $aplay_pids; do
        kill -9 "$aplay_pid" 2>/dev/null || true
    done
    echo "$(date '+%F %T') PL_KEY2 pressed: music stopped" >> "$LOG_FILE"
    exit 0
fi

amixer sset 'Headphone Playback ZC' on >/dev/null
amixer sset 'Speaker Playback ZC' on >/dev/null
amixer sset 'Right Output Mixer PCM' on >/dev/null
amixer sset 'Left Output Mixer PCM' on >/dev/null
amixer sset Headphone 105,105 >/dev/null
amixer sset Speaker 118,118 >/dev/null
amixer sset Playback 230,230 >/dev/null
amixer sset 'Speaker AC' 3 >/dev/null
amixer sset 'Speaker DC' 3 >/dev/null

echo "$(date '+%F %T') PL_KEY2 pressed: music started" >> "$LOG_FILE"
aplay /opt/hardware_test/test.wav >> "$LOG_FILE" 2>&1 &

