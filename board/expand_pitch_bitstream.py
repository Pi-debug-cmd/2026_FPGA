"""Verify compressed transfer and original bitstream before any PL mutation."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

argument = Path(sys.argv[1])
assert argument.parent == Path('/tmp') and argument.name.startswith('codex_')
run = argument.resolve()
assert run.parent == Path('/tmp').resolve() and run.is_dir()
record = json.loads((run / 'manifest.json').read_text())
name = 'audio_pitch_dma_swap.bin'
packed = (run / (name + '.gz')).read_bytes()
info = record['files'][name + '.gz']
assert len(packed) == info['bytes'] and hashlib.sha256(packed).hexdigest() == info['sha256']
raw = gzip.decompress(packed)
info = record['files'][name]
assert len(raw) == info['bytes'] and hashlib.sha256(raw).hexdigest() == info['sha256']
incoming = run / (name + '.incoming')
incoming.write_bytes(raw)
os.replace(incoming, run / name)
print('EXPANDED_BITSTREAM_VERIFIED', len(raw), info['sha256'])
