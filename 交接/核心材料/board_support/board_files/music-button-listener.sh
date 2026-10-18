#!/bin/sh

LOG_FILE=/tmp/music-button-listener.log

echo "$(date '+%F %T') listener started for PL_KEY2/KEY_ENTER" >> "$LOG_FILE"

while true; do
    EVENT_DEVICE=""
    for name_file in /sys/class/input/event*/device/name; do
        if [ -f "$name_file" ] && [ "$(cat "$name_file")" = "gpio-keys" ]; then
            event_name=$(basename "$(dirname "$(dirname "$name_file")")")
            EVENT_DEVICE="/dev/input/$event_name"
            break
        fi
    done

    if [ -c "$EVENT_DEVICE" ]; then
        key_was_down=0
        while [ -c "$EVENT_DEVICE" ]; do
            evtest --query "$EVENT_DEVICE" EV_KEY KEY_ENTER >/dev/null 2>&1
            query_result=$?
            if [ "$query_result" -eq 10 ]; then
                if [ "$key_was_down" -eq 0 ]; then
                    /usr/local/bin/play-official-music.sh
                    key_was_down=1
                fi
            else
                key_was_down=0
            fi
            sleep 0.05
        done
    else
        sleep 1
    fi
done

