#!/bin/sh
set -eu
RUN=/tmp/codex_saved_audio_probe_gain_20261010
mkdir "$RUN"
alsactl -f "$RUN/mixer_before.state" store 0
cleanup() {
    alsactl -f "$RUN/mixer_before.state" restore 0 >"$RUN/restore.log" 2>&1 ||
        echo MIXER_RESTORE_FAILED >&2
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
amixer sset 'Left Output Mixer PCM' on >"$RUN/mixer_setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/mixer_setup.log"
amixer sset 'Headphone' 119,119 >>"$RUN/mixer_setup.log"
amixer sset 'Playback' 222,222 >>"$RUN/mixer_setup.log"
python3 - "$RUN" <<'PY'
from pathlib import Path
import sys
out=Path(sys.argv[1])
for name,path in [('original','/tmp/codex_audio_path_probe_20261010/capture.raw'),('pitch','/tmp/codex_pitch_saved_audio.raw')]:
    # Omit the first second containing capture startup transients.
    (out/(name+'.raw')).write_bytes(Path(path).read_bytes()[256000:])
PY
echo ORIGINAL_PLAYBACK_7_SECONDS
aplay -q -D hw:0,0 -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=4096 "$RUN/original.raw" >"$RUN/original.log" 2>&1
sleep 1
echo PITCH_PLAYBACK_7_SECONDS
aplay -q -D hw:0,0 -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=4096 "$RUN/pitch.raw" >"$RUN/pitch.log" 2>&1
echo "original_underruns=$(grep -c underrun "$RUN/original.log" || true)"
echo "pitch_underruns=$(grep -c underrun "$RUN/pitch.log" || true)"
