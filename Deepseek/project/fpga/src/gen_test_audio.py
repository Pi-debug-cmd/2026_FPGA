"""Generate a deterministic 4 s S24_LE / 32 kHz / stereo test file.

Signal: three gliding partials with an amplitude envelope plus two silent gaps,
so the 1024-sample delay sweep is exercised on tonal and transient material.
Also writes the PCM16 mono derivative that the PL tool feeds to the DMA
(same conversion as src/ps/pitch_dma_stream.c: 24-bit value truncated to 16 bit).
"""
import math
import struct
import sys
from pathlib import Path

FS = 32000
SECONDS = 4
N = FS * SECONDS
outdir = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
outdir.mkdir(parents=True, exist_ok=True)


def s24(sample_index):
    t = sample_index / FS
    # gliding fundamental 180 -> 1800 Hz plus vibrato
    f0 = 180.0 + (1800.0 - 180.0) * (t / SECONDS)
    vib = 1.0 + 0.01 * math.sin(2 * math.pi * 5.5 * t)
    phase = 2 * math.pi * (180.0 * t + 0.5 * (1800.0 - 180.0) * t * t / SECONDS)
    v = (0.55 * math.sin(phase * vib)
         + 0.28 * math.sin(2 * phase + 0.4)
         + 0.12 * math.sin(3.02 * phase + 1.1))
    # envelope: fade in/out and two gaps
    env = min(1.0, t / 0.15) * min(1.0, (SECONDS - t) / 0.15)
    if 1.4 <= t < 1.55 or 2.7 <= t < 2.78:
        env = 0.0
    v = max(-1.0, min(1.0, v * env * 0.7))
    return int(round(v * 8388607.0))


stereo = bytearray()
mono16 = bytearray()
for i in range(N):
    s = s24(i)
    left = s
    right = s * 3 // 4 if (i // 16000) % 2 else s  # alternate right channel level
    for v in (left, right):
        stereo += struct.pack('<i', v & 0xffffff)[:3] + b'\x00'  # S24_LE in 4-byte slot
    pcm16 = s // 256 if s >= 0 else -((-s + 255) // 256)     # floor, same as pitch_dma_stream.c
    mono16 += struct.pack('<h', pcm16)

(outdir / 'input_s24_stereo.raw').write_bytes(stereo)
(outdir / 'input16_mono.raw').write_bytes(mono16)
if len(stereo) != N * 8 or len(mono16) != N * 2:
    raise SystemExit('size mismatch')
print('frames', N, 'stereo_bytes', len(stereo), 'mono16_bytes', len(mono16))
