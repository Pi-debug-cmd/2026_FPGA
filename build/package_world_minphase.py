"""Package an already routed fused-minphase candidate for Linux FPGA Manager."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--project', type=Path, required=True)
args = p.parse_args()
src = args.project/'voice7020.runs/impl_1/zynq_wrapper.bin'
data = src.read_bytes()
assert len(data) % 4 == 0
offset = data[:256].find(bytes.fromhex('aa995566'))
assert offset >= 0 and offset % 4 == 0
swapped = bytearray(len(data))
for lane in range(4):
    swapped[lane::4] = data[3-lane::4]
assert swapped[:256].find(bytes.fromhex('665599aa')) == offset
target = args.project/'world_minphase_swap.bin'
target.write_bytes(swapped)
compressed_path = Path(str(target)+'.gz')
with compressed_path.open('wb') as raw_compressed:
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw_compressed,
                       mtime=0) as compressed:
        compressed.write(swapped)
record = {
    'part': 'xc7z020clg400-2',
    'raw_bytes': len(data),
    'raw_sha256': hashlib.sha256(data).hexdigest(),
    'swap_sha256': hashlib.sha256(swapped).hexdigest(),
    'compressed_bytes': compressed_path.stat().st_size,
    'compressed_sha256': hashlib.sha256(compressed_path.read_bytes()).hexdigest(),
    'ap_ctrl_base': '0x43c70000',
    'pointer_args_base': '0x43c80000',
    'ddr_port': 'S_AXI_HP2',
    'bins': 513,
    'format': 'float32 log spectrum -> float32 complex filter',
    'boot_partition_modified': False,
}
(args.project/'world_minphase_bit_manifest.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2))
