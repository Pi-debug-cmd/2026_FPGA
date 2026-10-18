#!/bin/sh
# Silent playback only: inspect powered DAC/HP paths and direct-vs-vendor access.
set -eu
RUN=/tmp/codex_playback_state_probe_20261010
BASE=/sys/kernel/debug/asoc/xlnx-i2s-snd-card-0/wm8960.0-001a/dapm
mkdir "$RUN"
alsactl -f "$RUN/mixer_before.state" store 0
player=
cleanup() {
    if [ -n "$player" ]; then kill "$player" 2>/dev/null || true; wait "$player" 2>/dev/null || true; fi
    alsactl -f "$RUN/mixer_before.state" restore 0 >"$RUN/restore.log" 2>&1 || echo MIXER_RESTORE_FAILED >&2
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
amixer sset 'Left Output Mixer PCM' on >"$RUN/setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/setup.log"
python3 - "$RUN/zero.raw" <<'PY'
import sys
open(sys.argv[1],'wb').write(bytes(32000*8*8))
PY
for device in hw:0,0 default; do
    case "$device" in hw:0,0) mode=direct;; *) mode=vendor;; esac
    echo "SILENT_PROBE_MODE=$mode"
    aplay -v -D "$device" -t raw -f S24_LE -r 32000 -c 2 \
        --period-size=512 --buffer-size=4096 "$RUN/zero.raw" >"$RUN/$mode-aplay.log" 2>&1 & player=$!
    sleep 1
    cat /sys/kernel/debug/regmap/0-001a/registers >"$RUN/$mode-registers.log"
    for widget in Playback 'Left DAC' 'Right DAC' 'Left Output Mixer' 'Right Output Mixer' 'LOUT1 PGA' 'ROUT1 PGA' HP_L HP_R bias_level; do
        echo "WIDGET=$widget"
        cat "$BASE/$widget"
    done >"$RUN/$mode-dapm.log"
    cat /proc/asound/card0/pcm0p/sub0/hw_params >"$RUN/$mode-hw.log"
    cat /proc/asound/card0/pcm0p/sub0/status >"$RUN/$mode-status.log"
    wait "$player"; player=
    echo "REGISTERS=$mode"; cat "$RUN/$mode-registers.log"
    echo "DAPM=$mode"; cat "$RUN/$mode-dapm.log"
    echo "STATUS=$mode"; cat "$RUN/$mode-status.log"
done
