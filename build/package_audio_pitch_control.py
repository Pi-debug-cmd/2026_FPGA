"""Package the configurable design only after its separate implementation succeeds."""
import hashlib
import gzip
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
project = root / 'build/generated/audio_pitch_dma_control'
out = root / 'build/generated/pl_control_bundle'
out.mkdir(parents=True, exist_ok=True)
raw = (project / 'voice7020.runs/impl_1/zynq_wrapper.bin').read_bytes()
sync = raw[:256].find(bytes.fromhex('aa995566'))
assert len(raw) % 4 == 0 and sync >= 0 and sync % 4 == 0
swapped = bytearray(len(raw))
for lane in range(4):
    swapped[lane::4] = raw[3-lane::4]
(out / 'audio_pitch_dma_swap.bin').write_bytes(swapped)
(out / 'audio_pitch_dma_swap.bin.gz').write_bytes(gzip.compress(swapped, compresslevel=9, mtime=0))
copies = {
    'audio_pitch_dma.bit': project / 'voice7020.runs/impl_1/zynq_wrapper.bit',
    'audio_pitch_dma.hwh': project / 'voice7020.srcs/sources_1/bd/zynq/hw_handoff/zynq.hwh',
    'pitch_dma_proxy.ko': root / 'build/generated/pitch_dma_driver/pitch_dma_proxy.ko',
    'pitch_dma_stream': root / 'build/generated/pitch_dma_driver/pitch_dma_stream',
    'pitch_dma_control_overlay.dtbo': root / 'build/generated/pitch_dma_control_overlay.dtbo',
    'pitch_dma_control_overlay.dts': root / 'board/pitch_dma_control_overlay.dts',
}
for name, source in copies.items():
    shutil.copyfile(source, out / name)
names = ['audio_pitch_dma_swap.bin', 'audio_pitch_dma_swap.bin.gz', *copies]
record = {'part': 'xc7z020clg400-2', 'authority': 'A disk',
          'control_base': '0x41200000', 'dma_control_base': '0x40400000',
          'ratio_limits_q16': [32768, 131072], 'initial_dsp_reset_asserted': True,
          'hardware_test_passed': False, 'external_audio_io_timing_fully_constrained': False,
          'files': {name: {'bytes': (out / name).stat().st_size,
                           'sha256': hashlib.sha256((out / name).read_bytes()).hexdigest()}
                    for name in names}}
(out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print('Configurable candidate packaged; hardware validation pending')
