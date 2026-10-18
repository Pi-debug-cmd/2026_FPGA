"""Generate two low-volume 1 kHz native PCM tones for speaker-path diagnosis."""
import math
import struct

rate = 32000
count = rate * 2
for masked, name in ((False, "/tmp/tone32_signext.raw"), (True, "/tmp/tone32_masked.raw")):
    with open(name, "wb") as output:
        for i in range(count):
            value = round(0.18 * 8388607 * math.sin(2 * math.pi * 1000 * i / rate))
            if masked:
                value &= 0x00FFFFFF
            output.write(struct.pack("<ii", value, value))
    print(name)
