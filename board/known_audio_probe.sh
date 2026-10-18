#!/bin/sh
# One stream with an independently heard source. Recording gain is diagnostic.
set -eu
RUN=/tmp/codex_known_audio_probe_20261010
mkdir "$RUN"
alsactl -f "$RUN/before.state" store 0
trap 'alsactl -f "$RUN/before.state" restore 0 >"$RUN/restore.log" 2>&1' EXIT
trap 'exit 130' HUP INT TERM
python3 - "$RUN/combined.raw" <<'PY'
import struct, sys
music = open('/tmp/codex_factory_rate_probe_20261010/music_32000.raw','rb').read()
def amplified(path):
    raw = open(path,'rb').read()[256000:]
    output = bytearray()
    clipped = 0
    for (word,) in struct.iter_unpack('<I',raw):
        value = (((word & 0xffffff) ^ 0x800000) - 0x800000) * 8
        clipped += not (-8388608 <= value <= 8388607)
        value = min(8388607,max(-8388608,value))
        output.extend(struct.pack('<I',value & 0xffffff))
    print('DIAGNOSTIC_GAIN=8 file=%s clipped_words=%d' % (path,clipped))
    return output
original = amplified('/tmp/codex_audio_path_probe_20261010/capture.raw')
pitch = amplified('/tmp/codex_pitch_saved_audio.raw')
open(sys.argv[1],'wb').write(music+original+music+pitch)
PY
amixer sset 'Headphone Playback ZC' on >"$RUN/setup.log"
amixer sset 'Left Output Mixer PCM' on >>"$RUN/setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/setup.log"
amixer sset Headphone 105,105 >>"$RUN/setup.log"
amixer sset Playback 230,230 >>"$RUN/setup.log"
echo PLAYBACK_MUSIC_5_ORIGINAL_7_MUSIC_5_PITCH_7
aplay -v -D default -t raw -f S24_LE -r 32000 -c 2 "$RUN/combined.raw" >"$RUN/playback.log" 2>&1
echo "COMPLETED underruns=$(grep -c underrun "$RUN/playback.log" || true)"
