"""Run on the board only after the v2 PL/overlay have been installed."""
import errno
from array import array
import fcntl
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

base = Path(sys.argv[1])
binary = sys.argv[2]
manifest_name = sys.argv[3] if len(sys.argv) > 3 else 'vectors_manifest.json'
manifest = json.loads((base / manifest_name).read_text())
for name, sha in manifest['input_sha256'].items():
    assert hashlib.sha256((base / name).read_bytes()).hexdigest() == sha, name
# ARM32 _IOW('P', 2, 8). Validate error contracts without DMA traffic.
configure = 0x40085002
process = 0xc0085001
with open('/dev/pitch_dma', 'r+b', buffering=0) as device:
    for ratio, reserved in [(32767, 0), (131073, 0), (86856, 1)]:
        try:
            fcntl.ioctl(device, configure, struct.pack('<II', ratio, reserved))
        except OSError as exc:
            assert exc.errno == errno.EINVAL, exc
        else:
            raise AssertionError('Invalid configuration accepted')
    try:
        other = os.open('/dev/pitch_dma', os.O_RDWR)
    except OSError as exc:
        assert exc.errno == errno.EBUSY, exc
    else:
        os.close(other)
        raise AssertionError('Concurrent stream accepted')
    try:
        fcntl.ioctl(device, 0x5003, 0)
    except OSError as exc:
        assert exc.errno == errno.ENOTTY, exc
    else:
        raise AssertionError('Unknown ioctl accepted')
    for frames in [0, 4097]:
        try:
            fcntl.ioctl(device, process, struct.pack('<II', frames, 0))
        except OSError as exc:
            assert exc.errno == errno.EINVAL, exc
        else:
            raise AssertionError('Invalid DMA length accepted')
for index, case in enumerate(manifest['cases']):
    name = 'native_input.raw' if case['mode'] == 'native_s24' else 'pcm32_input.raw'
    with (base / name).open('rb') as source:
        run = subprocess.run([binary, str(manifest['chunk_frames']), case['mode'],
                              str(case['ratio_q16'])], stdin=source,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    assert run.returncode == 0, run.stderr.decode(errors='replace')
    assert len(run.stdout) == case['bytes'], index
    assert hashlib.sha256(run.stdout).hexdigest() == case['sha256'], index
    print('PASS_CASE', index, case['ratio_q16'], case['mode'], flush=True)
# Reject an invalid ratio midstream without disturbing the continuous state.
data = (base / 'pcm32_input.raw').read_bytes()
output = bytearray()
with open('/dev/pitch_dma', 'r+b', buffering=0) as device:
    continuous_ratio = manifest.get('continuous_ratio_q16', 86856)
    fcntl.ioctl(device, configure, struct.pack('<II', continuous_ratio, 0))
    for offset in range(0, len(data), 257 * 4):
        block = data[offset:offset + 257 * 4]
        buffer = array('i')
        buffer.frombytes(block)
        assert buffer.itemsize == 4 and sys.byteorder == 'little'
        fcntl.ioctl(device, process, struct.pack('<II', len(block) // 4, buffer.buffer_info()[0]))
        output.extend(buffer.tobytes())
        if offset == 257 * 4 * 4:
            try:
                fcntl.ioctl(device, configure, struct.pack('<II', 131073, 0))
            except OSError as exc:
                assert exc.errno == errno.EINVAL, exc
            else:
                raise AssertionError('Invalid midstream ratio accepted')
expected = next(c for c in manifest['cases'] if c['ratio_q16'] == continuous_ratio and c['mode'] == 'pcm32')
assert hashlib.sha256(output).hexdigest() == expected['sha256']
print(f"PASS: {len(manifest['cases'])} reset cases, continuous state after rejected ratio, limits, exclusive open, unknown ioctl")
