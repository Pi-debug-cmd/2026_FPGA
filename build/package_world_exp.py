"""Package only the already routed WORLD accelerator for temporary Linux loading."""
import gzip
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
base = root/'build/generated/world_exp_20261027'
src = base/'voice7020.runs/impl_1/zynq_wrapper.bin'
data = src.read_bytes()
assert len(data) % 4 == 0
offset = data[:256].find(bytes.fromhex('aa995566'))
assert offset >= 0 and offset % 4 == 0
swapped = bytearray(len(data))
for lane in range(4):
    swapped[lane::4] = data[3-lane::4]
assert swapped[:256].find(bytes.fromhex('665599aa')) == offset
target = base/'world_exp_swap.bin'
target.write_bytes(swapped)
with gzip.open(str(target)+'.gz', 'wb') as f:
    f.write(swapped)
record = {'part': 'xc7z020clg400-2', 'raw_bytes': len(data),
          'raw_sha256': hashlib.sha256(data).hexdigest(),
          'swap_sha256': hashlib.sha256(swapped).hexdigest(),
          'compressed_bytes': Path(str(target)+'.gz').stat().st_size,
          'dma_base': '0x40400000', 'axis_bits': 64, 'bins': 513,
          'boot_partition_modified': False}
(base/'bit_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
