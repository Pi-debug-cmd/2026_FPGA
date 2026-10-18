"""Golden results for the actual registered ratio, before any subjective trial."""
import hashlib
import json
from pathlib import Path
import struct

from src.ps.profile_recipe import load_recipe
from src.reference.pitch_shift_fixed import FixedPitchShifter

root = Path(__file__).resolve().parents[1]
recipe = load_recipe(root / 'data/profiles/current_recipe.json')
q16 = recipe['ratio_q16']
base = root / 'data/diagnostics/dma_control_vectors'
pcm = (base / 'pcm32_input.raw').read_bytes()
native = (base / 'native_input.raw').read_bytes()
values = {'pcm32': [x[0] for x in struct.iter_unpack('<i', pcm)],
          'native_s24': [(((x[0] & 0xffffff) ^ 0x800000) - 0x800000) // 256
                         for x in struct.iter_unpack('<II', native)]}
cases = []
for mode, samples in values.items():
    result = FixedPitchShifter(q16).process(samples)
    if mode == 'pcm32':
        expected = b''.join(struct.pack('<i', int(x)) for x in result)
    else:
        expected = b''.join(struct.pack('<II', (int(x) * 256) & 0xffffff,
                                       (int(x) * 256) & 0xffffff) for x in result)
    cases.append({'ratio_q16': q16, 'mode': mode, 'frames': len(samples),
                  'bytes': len(expected), 'sha256': hashlib.sha256(expected).hexdigest()})
manifest = {'chunk_frames': 257, 'reset_before_every_case': True,
            'continuous_ratio_q16': q16, 'cases': cases,
            'input_sha256': {name: hashlib.sha256((base / name).read_bytes()).hexdigest()
                             for name in ['pcm32_input.raw', 'native_input.raw']}}
(base / 'registered_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('REGISTERED_GOLDEN_PREPARED', q16)
