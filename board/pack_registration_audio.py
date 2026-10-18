"""Decode native S24_LE slots explicitly; emit compressed mono PCM16 WAV."""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys


def pack_native(raw, rate=32000):
    if not raw or len(raw) % 8:
        raise ValueError('Expected complete S24_LE stereo frames')
    pcm = bytearray()
    clipped = 0
    for left, _ in struct.iter_unpack('<II', raw):
        value = (((left & 0xffffff) ^ 0x800000) - 0x800000)
        clipped += abs(value) >= 32760 * 256
        pcm.extend(struct.pack('<h', value // 256))
    header = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36 + len(pcm), b'WAVE',
                         b'fmt ', 16, 1, 1, rate, rate * 2, 2, 16, b'data', len(pcm))
    return header + pcm, clipped / (len(raw) // 8)


def main():
    run = Path(sys.argv[1])
    raw = (run / 'capture.raw').read_bytes()
    wav, clip = pack_native(raw)
    packed = gzip.compress(wav, compresslevel=9, mtime=0)
    (run / 'capture.wav.gz').write_bytes(packed)
    record = {'kind': 'registration_capture', 'sample_rate': 32000, 'channels': 1,
              'sample_bits': 16, 'frames': len(raw) // 8,
              'duration_s': len(raw) / 8 / 32000, 'native_clip_fraction': clip,
              'raw_sha256': hashlib.sha256(raw).hexdigest(),
              'wav_sha256': hashlib.sha256(wav).hexdigest(),
              'gzip_sha256': hashlib.sha256(packed).hexdigest()}
    (run / 'capture_manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
