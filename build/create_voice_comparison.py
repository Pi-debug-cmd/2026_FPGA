"""Offline listening comparison: held-out target, source, fixed-reference output."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from src.reference.audio_io import downsample_16k, read_pcm_wav, write_pcm16

root = Path(__file__).resolve().parents[1]
base = root / 'data/registrations/source_20261011'
target_rate, target = read_pcm_wav(root / 'voice_src/src_1/Track 9(1).wav')
rate, source = read_pcm_wav(base / 'capture.wav')
output_rate, output = read_pcm_wav(base / 'predicted_registered.wav')
assert rate == output_rate == 32000
target = downsample_16k(target_rate, target)
source16 = downsample_16k(rate, source)
output16 = downsample_16k(output_rate, output)
length = 5 * 16000
def choose_start(values):
    starts = range(16000, len(values) - length + 1, 8000)
    return max(starts, key=lambda start: float(np.mean(values[start:start + length] ** 2)))
source_start, target_start = choose_start(source16), choose_start(target)
segments = [target[target_start:target_start + length],
            source16[source_start:source_start + length],
            output16[source_start:source_start + length]]
def to32(values):
    # Common offline interpolation/level handling for all three segments.
    rms, peak = float(np.sqrt(np.mean(values * values))), float(np.max(abs(values)))
    gain = min(0.1 / max(rms, 1e-12), 0.95 / max(peak, 1e-12))
    expanded = np.zeros(len(values) * 2)
    expanded[::2] = values * gain
    offsets = np.arange(127) - 63
    kernel = 2 * 0.225 * np.sinc(2 * 0.225 * offsets) * np.hamming(127)
    kernel *= 2 / kernel.sum()
    return np.convolve(expanded, kernel, mode='same'), gain
rendered = [to32(segment) for segment in segments]
silence = np.zeros(32000)
joined = np.concatenate([rendered[0][0], silence, rendered[1][0], silence, rendered[2][0]])
wav_path = base / 'target_source_calibrated_comparison.wav'
write_pcm16(wav_path, joined, 32000)
raw = wav_path.read_bytes()
packed = gzip.compress(raw, compresslevel=9, mtime=0)
(base / 'target_source_calibrated_comparison.wav.gz').write_bytes(packed)
record = {'kind': 'offline_reference_listening_comparison',
          'order': ['held_out_target_5s', 'source_5s', 'reference_pitch_mapped_source_5s'],
          'gap_seconds': 1, 'rate': 32000, 'duration_s': len(joined) / 32000,
          'source_start_s': source_start / 16000, 'target_start_s': target_start / 16000,
          'gains': [item[1] for item in rendered],
          'wav_sha256': hashlib.sha256(raw).hexdigest(),
          'gzip_sha256': hashlib.sha256(packed).hexdigest(),
          'limitation': 'Processed segment is offline fixed-reference prediction, not recorded physical PL output; utterance differs from target'}
(base / 'comparison_manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
