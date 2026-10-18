#!/bin/sh
# Isolate physical playback and capture. Restore all controls after the probe.
set -eu
RUN=/tmp/codex_audio_path_probe_20261010
mkdir "$RUN"
cleanup() {
    if alsactl -f "$RUN/mixer_before.state" restore 0 >"$RUN/restore.log" 2>&1; then
        echo MIXER_RESTORED
    else
        echo MIXER_RESTORE_FAILED >&2
    fi
}
alsactl -f "$RUN/mixer_before.state" store 0
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
amixer sset 'Left Boost Mixer LINPUT1' on >"$RUN/mixer_setup.log"
amixer sset 'Left Input Mixer Boost' on >>"$RUN/mixer_setup.log"
amixer sset 'Right Boost Mixer RINPUT1' on >>"$RUN/mixer_setup.log"
amixer sset 'Right Input Mixer Boost' on >>"$RUN/mixer_setup.log"
amixer cset name='ADC Data Output Select' 1 >>"$RUN/mixer_setup.log"
amixer sset 'Left Output Mixer PCM' on >>"$RUN/mixer_setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/mixer_setup.log"
python3 - "$RUN/tone.raw" <<'PY'
import math,struct,sys
with open(sys.argv[1],'wb') as f:
    for i in range(32000*4):
        frequency=440 if i<64000 else 880
        # Smooth 10 ms fades on both tone segments, peak 0.2, original mixer gain.
        local=i%64000
        fade=min(1.0,local/320.0,(63999-local)/320.0)
        v=int(0.2*fade*math.sin(2*math.pi*frequency*i/32000)*8388607)&0xffffff
        f.write(struct.pack('<II',v,v))
PY
echo TONE_START_4_SECONDS
aplay -q -D hw:0,0 -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=4096 "$RUN/tone.raw" >"$RUN/playback.log" 2>&1
echo CAPTURE_START_SPEAK_8_SECONDS
arecord -q -D hw:0,1 -t raw -f S24_LE -r 32000 -c 2 \
    --period-size=512 --buffer-size=4096 -d 8 "$RUN/capture.raw" >"$RUN/capture.log" 2>&1
python3 - "$RUN/capture.raw" <<'PY'
import math,struct,sys
raw=open(sys.argv[1],'rb').read()
x=[(((a&0xffffff)^0x800000)-0x800000)/8388608.0 for a,b in struct.iter_unpack('<II',raw)]
print('capture_bytes=%d samples=%d nonzero=%d peak=%.7f rms=%.7f'%(len(raw),len(x),sum(v!=0 for v in x),max(map(abs,x),default=0),math.sqrt(sum(v*v for v in x)/max(1,len(x)))))
for i in range(8):
    y=x[i*32000:(i+1)*32000]
    print('second=%d peak=%.7f rms=%.7f'%(i,max(map(abs,y),default=0),math.sqrt(sum(v*v for v in y)/max(1,len(y)))))
PY
echo "capture_overruns=$(grep -c overrun "$RUN/capture.log" || true)"
echo "playback_underruns=$(grep -c underrun "$RUN/playback.log" || true)"
