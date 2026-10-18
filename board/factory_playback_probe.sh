#!/bin/sh
# Finite playback using the board's supplied WAV and default/mmap path.
set -eu
RUN=/tmp/codex_factory_playback_probe_20261010
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
amixer sset 'Headphone Playback ZC' on >"$RUN/setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/setup.log"
amixer sset 'Left Output Mixer PCM' on >>"$RUN/setup.log"
amixer sset Headphone 105,105 >>"$RUN/setup.log"
amixer sset Playback 230,230 >>"$RUN/setup.log"
echo FACTORY_PLAYBACK_START_5_SECONDS
aplay -v -D default -d 5 /opt/hardware_test/test.wav >"$RUN/aplay.log" 2>&1 & player=$!
sleep 1
cat /sys/kernel/debug/regmap/0-001a/registers >"$RUN/registers.log"
cat /proc/asound/card0/pcm0p/sub0/hw_params >"$RUN/hw_params.log"
cat /sys/kernel/debug/clk/clk_summary | grep -E 'audio-clk' >"$RUN/clock.log"
for widget in HP_L HP_R 'Left DAC' 'Right DAC' 'LOUT1 PGA' 'ROUT1 PGA'; do
    echo "WIDGET=$widget"; cat "$BASE/$widget"
done >"$RUN/dapm.log"
wait "$player"; player=
echo FACTORY_PLAYBACK_COMPLETED
cat "$RUN/hw_params.log"
cat "$RUN/clock.log"
echo "underruns=$(grep -c underrun "$RUN/aplay.log" || true)"
