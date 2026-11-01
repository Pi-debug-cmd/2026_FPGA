"""Extract the left channel of an S24_LE stereo raw file as PCM16.

Same integer rule as src/ps/pitch_dma_stream.c and the board tool:
24-bit signed value truncated toward zero to 16 bit.
"""
import struct
import sys
from pathlib import Path

data = Path(sys.argv[1]).read_bytes()
out = bytearray()
for off in range(0, len(data) - 7, 8):
    w = data[off] | (data[off + 1] << 8) | (data[off + 2] << 16)
    v = (w ^ 0x800000) - 0x800000
    pcm = v // 256 if v >= 0 else -((-v + 255) // 256)
    out += struct.pack('<h', pcm)
Path(sys.argv[2]).write_bytes(out)
print('frames', len(out) // 2, 'bytes', len(out))
