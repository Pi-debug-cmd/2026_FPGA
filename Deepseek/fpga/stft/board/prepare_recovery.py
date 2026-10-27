#!/usr/bin/env python3
"""Prepare a volatile factory rollback image from /boot/bit/zynq7020.bit.

Read-only on the boot partition; writes only into the /tmp staging directory.
"""
import array
import hashlib
import json
import sys
from pathlib import Path

RUN = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/pl_2018')
RUN.mkdir(parents=True, exist_ok=True)
source = Path('/boot/bit/zynq7020.bit')
raw = source.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
expected = '16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61'
assert raw[:2] == b'\x00\x09' or raw[:2] == b'\x00\x0b', raw[:2]
offset = 2 + int.from_bytes(raw[:2], 'big')
assert int.from_bytes(raw[offset:offset + 2], 'big') == 1
offset += 2
fields = {}
while offset < len(raw):
    key = raw[offset:offset + 1]
    offset += 1
    width = 4 if key == b'e' else 2
    assert key in (b'a', b'b', b'c', b'd', b'e'), key
    size = int.from_bytes(raw[offset:offset + width], 'big')
    offset += width
    value = raw[offset:offset + size]
    assert len(value) == size
    offset += size
    if key == b'e':
        payload = value
        break
    fields[key.decode()] = value.rstrip(b'\0').decode()
assert offset == len(raw) and len(payload) % 4 == 0
words = array.array('I', payload)
assert words.itemsize == 4
words.byteswap()
swapped = words.tobytes()
assert swapped[:256].find(bytes.fromhex('665599aa')) % 4 == 0
target = RUN / 'factory_restore_swap.bin'
target.write_bytes(swapped)
record = {'boot_bit_path': str(source), 'boot_bit_sha256': sha,
          'boot_bit_sha256_matches_20261010': sha == expected,
          'fields': fields, 'payload_bytes': len(payload),
          'factory_restore_sha256': hashlib.sha256(swapped).hexdigest(),
          'state': 'prepared only; FPGA unchanged'}
(RUN / 'recovery_manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
