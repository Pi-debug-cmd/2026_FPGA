#!/bin/sh
# One playback stream: marker/original/marker/pitch. Isolate data from PCM reopen.
set -eu
RUN=/tmp/codex_combined_audio_probe_20261010
mkdir "$RUN"
alsactl -f "$RUN/mixer_before.state" store 0
cleanup() {
    alsactl -f "$RUN/mixer_before.state" restore 0 >"$RUN/restore.log" 2>&1 || echo MIXER_RESTORE_FAILED >&2
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
amixer sset 'Left Input Mixer Boost' on >"$RUN/mixer_setup.log"
amixer sset 'Right Input Mixer Boost' on >>"$RUN/mixer_setup.log"
amixer cset name='ADC Data Output Select' 1 >>"$RUN/mixer_setup.log"
amixer sset 'Left Output Mixer PCM' on >>"$RUN/mixer_setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/mixer_setup.log"
amixer sset 'Headphone' 119,119 >>"$RUN/mixer_setup.log"
amixer sset 'Playback' 222,222 >>"$RUN/mixer_setup.log"
python3 - "$RUN/combined.raw" <<'PY'
import math,struct,sys
tone=b''.join(struct.pack('<II',v,v) for i in range(32000) for v in [int(0.02*min(1,i/320,(31999-i)/320)*math.sin(2*math.pi*440*i/32000)*8388607)&0xffffff])
original=open('/tmp/codex_audio_path_probe_20261010/capture.raw','rb').read()[256000:]
pitch=open('/tmp/codex_pitch_saved_audio.raw','rb').read()[256000:]
open(sys.argv[1],'wb').write(tone+original+tone+pitch)
print('combined_bytes=%d'%(len(tone+original+tone+pitch)))
PY
echo COMBINED_PLAYBACK_MARKER_ORIGINAL_MARKER_PITCH
aplay -q -D hw:0,0 -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=4096 "$RUN/combined.raw" >"$RUN/playback.log" 2>&1
echo "underruns=$(grep -c underrun "$RUN/playback.log" || true)"
