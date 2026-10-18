"""Continuous fixed-ratio vectors for the first physical PCM32 DMA test."""
import hashlib
import json
from pathlib import Path
import numpy as np
from src.reference.pitch_shift_fixed import FixedPitchShifter


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / 'data/diagnostics/dma_vectors'
    out.mkdir(parents=True, exist_ok=True)
    samples = np.random.default_rng(20261010).integers(-32768, 32768, 8195, dtype=np.int32)
    samples[:12] = [-32768, -32767, -257, -256, -1, 0, 1, 255, 256, 32766, 32767, 0]
    shifter = FixedPitchShifter(86856)
    result = shifter.process(samples).astype('<i4')
    rng = np.random.default_rng(70202026)
    left = rng.integers(-8388608, 8388608, len(samples), dtype=np.int32)
    left[:12] = [-8388608, -8388607, -257, -256, -255, -1, 0, 1, 255, 256, 8388606, 8388607]
    right = -left.astype(np.int64)
    native = np.column_stack([left.astype(np.int64) & 0xffffff, right & 0xffffff]).astype(np.uint32)
    # Unspecified container high bytes and a different right channel must be ignored.
    native |= rng.integers(0, 256, native.shape, dtype=np.uint32) << 24
    native_result = shifter.process(left >> 8).astype(np.int32)
    packed = (native_result * 256).astype(np.uint32) & 0xffffff
    native_expected = np.column_stack([packed, packed]).astype('<u4')
    records = {}
    for name, values in [('pcm32_input.raw', samples.astype('<i4')), ('pcm32_expected.raw', result),
                         ('native_input.raw', native.astype('<u4')), ('native_expected.raw', native_expected)]:
        data = values.tobytes()
        (out / name).write_bytes(data)
        records[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    manifest = {'ratio_q16': 86856, 'samples': len(samples), 'pcm': 'signed PCM16 extended to LE int32',
                'suggested_chunk_frames': 257, 'initial_state': 'fresh PL reset, zero-filled RAM',
                'cross_block_state': 'preserved; do not reset on TLAST',
                'test_order': ['PCM32 first', 'native_s24 second, same core state'],
                'before_listening': 'discard output of 2048 zero samples to remove full-scale test history; this is not a phase reset',
                'files': records}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Prepared 8195 continuous PCM32 samples; hardware comparison pending')


if __name__ == '__main__':
    main()
