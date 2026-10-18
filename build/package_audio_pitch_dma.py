"""Prepare a Linux Zynq FPGA Manager byte-swapped candidate and checksum manifest."""
import hashlib
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
out = root / 'build/generated/pl_bundle'
out.mkdir(parents=True, exist_ok=True)
raw_path = root / 'build/generated/audio_pitch_dma/voice7020.runs/impl_1/zynq_wrapper.bin'
raw = raw_path.read_bytes()
assert len(raw) % 4 == 0 and raw[:256].find(bytes.fromhex('aa995566')) % 4 == 0
swapped = bytearray(len(raw))
for lane in range(4):
    swapped[lane::4] = raw[3-lane::4]
target = out / 'audio_pitch_dma_swap.bin'
target.write_bytes(swapped)
assert target.read_bytes()[:256].find(bytes.fromhex('665599aa')) % 4 == 0
copies = {
    'audio_pitch_dma.bit': 'build/generated/audio_pitch_dma/voice7020.runs/impl_1/zynq_wrapper.bit',
    'audio_pitch_dma.hwh': 'build/generated/audio_pitch_dma/voice7020.srcs/sources_1/bd/zynq/hw_handoff/zynq.hwh',
    'pitch_dma_proxy.ko': 'build/generated/pitch_dma_driver/pitch_dma_proxy.ko',
    'pitch_dma_stream': 'build/generated/pitch_dma_driver/pitch_dma_stream',
    'pitch_dma_overlay.dts': 'board/pitch_dma_overlay.dts',
}
for name, path in copies.items():
    shutil.copyfile(root / path, out / name)
files = {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
         for p in out.iterdir() if p.is_file() and p.name != 'manifest.json'}
record = {'part': 'xc7z020clg400-2', 'authority': 'A disk per user instruction',
          'ratio_q16': 86856, 'dma_control_base': '0x40400000', 'dma_irq_f2p_bits': [12, 13],
          'fixed_ratio_only': True, 'hardware_test_passed': False,
          'external_audio_io_timing_fully_constrained': False, 'files': files}
(out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print('Candidate packaged; no board programming performed')
