"""Convert a Vivado .bin bitstream into the Zynq fpga_manager image.

Vivado's .bin stores each 32-bit configuration word big-endian; the Zynq PCAP
path (zynq-fpga.c / fpgautil) needs little-endian words, i.e. every 4-byte word
reversed.  Verified against the same transform used by the repo's 2026-10-10
package script (raw aa995566 -> 665599aa at a 4-byte aligned offset).
"""
import gzip
import hashlib
import sys
from pathlib import Path

raw = Path(sys.argv[1]).read_bytes()
out = Path(sys.argv[2])
assert len(raw) % 4 == 0, len(raw)
sync = raw[:256].find(bytes.fromhex('aa995566'))
assert sync >= 0 and sync % 4 == 0, 'no big-endian sync word in the first 256 bytes'
swapped = bytearray(len(raw))
for lane in range(4):
    swapped[lane::4] = raw[3 - lane::4]
swapped = bytes(swapped)
assert swapped[:256].find(bytes.fromhex('665599aa')) % 4 == 0
out.write_bytes(swapped)
gz = out.with_suffix(out.suffix + '.gz')
gz.write_bytes(gzip.compress(swapped, compresslevel=9, mtime=0))
print('bin_bytes', len(raw))
print('swap_bytes', len(swapped), hashlib.sha256(swapped).hexdigest())
print('gz_bytes', gz.stat().st_size, hashlib.sha256(gz.read_bytes()).hexdigest())
