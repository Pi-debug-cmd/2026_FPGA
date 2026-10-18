#!/bin/sh
# Same source/configuration at two rates. Offline interpolation is diagnostic only.
set -eu
RUN=/tmp/codex_factory_rate_probe_20261010
mkdir "$RUN"
alsactl -f "$RUN/before.state" store 0
trap 'alsactl -f "$RUN/before.state" restore 0 >"$RUN/restore.log" 2>&1' EXIT
trap 'exit 130' HUP INT TERM
python3 - "$RUN" <<'PY'
import struct, sys
with open('/opt/hardware_test/test.wav', 'rb') as f:
    assert f.read(12)[8:12] == b'WAVE'
    while True:
        tag, size = struct.unpack('<4sI', f.read(8))
        if tag == b'fmt ':
            fmt = f.read(size)
            encoding, channels, rate, byte_rate, alignment, bits = struct.unpack_from('<HHIIHH', fmt)
            assert channels == 2 and rate == 44100 and bits == 24 and alignment == 6
            assert encoding == 65534 and struct.unpack_from('<I', fmt, 24)[0] == 1
        elif tag == b'data':
            raw = f.read(44100 * 5 * 6)
            break
        else:
            f.seek(size, 1)
        if size & 1:
            f.seek(1, 1)
source = [int.from_bytes(raw[i:i+3], 'little', signed=True) for i in range(0, len(raw), 3)]
for out_rate in (44100, 32000):
    output = bytearray()
    for n in range(out_rate * 5):
        index, fraction = divmod(n * 44100, out_rate)
        for ch in range(2):
            a = source[index * 2 + ch]
            b = source[min(index + 1, len(source)//2 - 1) * 2 + ch]
            value = a + (b-a) * fraction // out_rate
            output.extend(struct.pack('<I', value & 0xffffff))
    open(sys.argv[1] + '/music_%d.raw' % out_rate, 'wb').write(output)
PY
amixer sset 'Headphone Playback ZC' on >"$RUN/setup.log"
amixer sset 'Left Output Mixer PCM' on >>"$RUN/setup.log"
amixer sset 'Right Output Mixer PCM' on >>"$RUN/setup.log"
amixer sset Headphone 105,105 >>"$RUN/setup.log"
amixer sset Playback 230,230 >>"$RUN/setup.log"
for rate in 44100 32000; do
    echo "MUSIC_START_RATE=$rate DURATION=5"
    aplay -v -D default -t raw -f S24_LE -c 2 -r "$rate" "$RUN/music_$rate.raw" >"$RUN/play_$rate.log" 2>&1 & player=$!
    sleep 1
    cat /sys/kernel/debug/regmap/0-001a/registers >"$RUN/registers_$rate.log"
    cat /proc/asound/card0/pcm0p/sub0/hw_params
    grep audio-clk /sys/kernel/debug/clk/clk_summary
    wait "$player"
    echo "MUSIC_END_RATE=$rate underruns=$(grep -c underrun "$RUN/play_$rate.log" || true)"
    sleep 2
done
