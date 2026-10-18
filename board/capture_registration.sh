#!/bin/sh
# Finite registration recording; fails before touching mixer if audio is busy.
set -eu
ROLE=${1:-source}
SECONDS_TO_RUN=${2:-12}
TAG=${3:-first}
case "$ROLE" in source|target) ;; *) exit 2;; esac
case "$SECONDS_TO_RUN" in ''|*[!0-9]*) exit 2;; esac
case "$TAG" in ''|*[!a-zA-Z0-9_]*) exit 2;; esac
[ "$SECONDS_TO_RUN" -ge 5 ] && [ "$SECONDS_TO_RUN" -le 30 ] || exit 2
for node in pcm1c pcm0p; do
    [ "$(cat /proc/asound/card0/$node/sub0/status)" = closed ] || {
        echo AUDIO_BUSY >&2; exit 3;
    }
done
RUN=/tmp/codex_registration_${ROLE}_${TAG}
mkdir "$RUN"
capture_pid=
cleanup() {
    if [ -n "$capture_pid" ]; then
        kill "$capture_pid" 2>/dev/null || true
        wait "$capture_pid" 2>/dev/null || true
    fi
    if [ -f "$RUN/mixer_before.state" ]; then
        alsactl -f "$RUN/mixer_before.state" restore 0 >"$RUN/mixer_restore.log" 2>&1 ||
            echo MIXER_RESTORE_FAILED >&2
    fi
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
alsactl -f "$RUN/mixer_before.state" store 0
amixer sset 'Left Input Mixer Boost' on >"$RUN/mixer_setup.log"
amixer sset 'Right Boost Mixer RINPUT1' on >>"$RUN/mixer_setup.log"
amixer sset 'Right Input Mixer Boost' on >>"$RUN/mixer_setup.log"
amixer cset name='ADC Data Output Select' 1 >>"$RUN/mixer_setup.log"
amixer sset 'Left Boost Mixer LINPUT1' on >>"$RUN/mixer_setup.log"
amixer sset 'Left Input Boost Mixer LINPUT1' 1 >>"$RUN/mixer_setup.log"
amixer sset 'Left Output Mixer PCM' off >>"$RUN/mixer_setup.log"
amixer sset 'Right Output Mixer PCM' off >>"$RUN/mixer_setup.log"
echo "REGISTRATION_CAPTURE_STARTED role=$ROLE seconds=$SECONDS_TO_RUN"
arecord -q -D hw:0,1 -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=4096 -d "$SECONDS_TO_RUN" "$RUN/capture.raw" \
    >"$RUN/capture.log" 2>&1 & capture_pid=$!
wait "$capture_pid"; capture_pid=
if grep -q overrun "$RUN/capture.log"; then echo CAPTURE_OVERRUN >&2; exit 4; fi
python3 /tmp/codex_pl_control_20261011/pack_registration_audio.py "$RUN"
echo "REGISTRATION_CAPTURE_COMPLETED directory=$RUN"
