"""Fresh-reset golden cases for both formats and all supported ratio boundaries."""
import hashlib
import json
from pathlib import Path
import struct

from src.reference.pitch_shift_fixed import FixedPitchShifter

root = Path(__file__).resolve().parents[1]
out = root / 'data/diagnostics/dma_control_vectors'
out.mkdir(parents=True, exist_ok=True)
source = root / 'data/diagnostics/dma_vectors'
pcm = (source / 'pcm32_input.raw').read_bytes()
native = (source / 'native_input.raw').read_bytes()
(out / 'pcm32_input.raw').write_bytes(pcm)
(out / 'native_input.raw').write_bytes(native)
samples = [x[0] for x in struct.iter_unpack('<i', pcm)]
left = [(((x[0] & 0xffffff) ^ 0x800000) - 0x800000) // 256
        for x in struct.iter_unpack('<II', native)]
cases = []
for ratio in [32768, 52429, 65536, 81920, 86856, 98304, 131072, 86856]:
    for mode, values in [('pcm32', samples), ('native_s24', left)]:
        result = FixedPitchShifter(ratio).process(values)
        if mode == 'pcm32':
            expected = b''.join(struct.pack('<i', int(x)) for x in result)
        else:
            expected = b''.join(struct.pack('<II', (int(x) * 256) & 0xffffff,
                                            (int(x) * 256) & 0xffffff) for x in result)
        cases.append({'ratio_q16': ratio, 'mode': mode, 'frames': len(values),
                      'bytes': len(expected), 'sha256': hashlib.sha256(expected).hexdigest()})
manifest = {'chunk_frames': 257, 'reset_before_every_case': True, 'cases': cases,
            'input_sha256': {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                             for name in ['pcm32_input.raw', 'native_input.raw']}}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(f'Generated {len(cases)} reset/configuration golden cases')
