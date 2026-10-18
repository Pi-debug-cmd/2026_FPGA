"""Prepare a temporary factory recovery image without programming the FPGA."""
import array
import hashlib
import json
from pathlib import Path

source = Path('/boot/bit/zynq7020.bit')
raw = source.read_bytes()
expected = '16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61'
assert hashlib.sha256(raw).hexdigest() == expected, 'Boot bitstream changed; inspect first'
offset = 2 + int.from_bytes(raw[:2], 'big')
assert int.from_bytes(raw[offset:offset+2], 'big') == 1
offset += 2
fields = {}
while offset < len(raw):
    key = raw[offset:offset+1]
    offset += 1
    width = 4 if key == b'e' else 2
    assert key in (b'a', b'b', b'c', b'd', b'e')
    size = int.from_bytes(raw[offset:offset+width], 'big')
    offset += width
    value = raw[offset:offset+size]
    assert len(value) == size
    offset += size
    if key == b'e':
        payload = value
        break
    fields[key.decode()] = value.rstrip(b'\0').decode()
assert offset == len(raw) and len(payload) % 4 == 0
assert '7z020clg400' in fields['b']
words = array.array('I', payload)
assert words.itemsize == 4
words.byteswap()
swapped = words.tobytes()
assert swapped[:256].find(bytes.fromhex('665599aa')) % 4 == 0
run = Path('/tmp/codex_pl_trial_20261010')
run.mkdir()
(run / 'factory_restore_swap.bin').write_bytes(swapped)
record = {'boot_bit_sha256': expected, 'fields': fields, 'payload_bytes': len(payload),
          'factory_restore_sha256': hashlib.sha256(swapped).hexdigest(),
          'state': 'prepared only; FPGA unchanged'}
(run / 'recovery_manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
