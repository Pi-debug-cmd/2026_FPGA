"""Compare capture, identity resynthesis and old recipe; no new conversion tuning."""
import gzip
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16, file_sha256

base = ROOT / 'data/registrations/source_20261015/speaker01'
prior = json.loads((base / 'hybrid_comparison/manifest.json').read_text(encoding='utf-8'))
output = base / 'clarity_diagnostic'
output.mkdir(exist_ok=True)
paths = [base / 'holdout.wav', base / 'clarity_audit/identity.wav', base / 'hybrid_comparison/old_fixed.wav']
order = ['original_capture', 'world_identity_no_conversion', 'old_fixed_recipe']
start, length = round(prior['source_crop_start_s'] * 16000), 80000
segments = []
for path in paths:
    rate, signal = read_pcm_wav(path)
    segment = downsample_16k(rate, signal)[start:start + length]
    if len(segment) != length or not np.all(np.isfinite(segment)):
        raise ValueError('Invalid crop')
    segments.append(segment)
rms = [float(np.sqrt(np.mean(x * x))) for x in segments]
if min(rms) <= 1e-10:
    raise ValueError('Silent diagnostic segment')
common_rms = min([.08] + [.85 * level / max(float(np.max(np.abs(x))), 1e-12)
                         for x, level in zip(segments, rms)])
offsets = np.arange(127) - 63
kernel = 2 * .225 * np.sinc(2 * .225 * offsets) * np.hamming(127)
kernel *= 2 / kernel.sum()
parts, gains = [], []
for segment, level in zip(segments, rms):
    gain = common_rms / level
    expanded = np.zeros(length * 2)
    expanded[::2] = segment * gain
    parts.append(np.convolve(expanded, kernel, mode='same'))
    gains.append(gain)
joined = np.concatenate([np.zeros(32000)] + [part for i, segment in enumerate(parts)
                         for part in ([np.zeros(32000), segment] if i else [segment])])
if not np.all(np.isfinite(joined)) or np.max(np.abs(joined)) >= 1:
    raise ValueError('Invalid playback waveform')
audio = output / 'comparison.wav'
packed = output / 'comparison.wav.gz'
write_pcm16(audio, joined, 32000)
packed.write_bytes(gzip.compress(audio.read_bytes(), compresslevel=9, mtime=0))
record = {'kind': 'capture_vs_world_identity_diagnostic', 'order': order, 'duration_s': len(joined) / 32000,
          'segment_seconds': 5, 'gap_seconds': 1, 'leading_silence_seconds': 1,
          'source_crop_start_s': start / 16000, 'rate': 32000,
          'inputs': [{'path': str(path.relative_to(ROOT)), 'sha256': file_sha256(path)} for path in paths],
          'gains': gains, 'common_rms_before_interpolation': common_rms,
          'peak': float(np.max(np.abs(joined))), 'clip_fraction': float(np.mean(np.abs(joined) >= 1)),
          'wav_sha256': file_sha256(audio), 'gzip_sha256': file_sha256(packed),
          'configuration_changed': False, 'listening_completed': False,
          'limitations': 'Diagnostic only. RMS equalization is for this playback, not an input gain change. Identity resynthesis uses measured F0, original spectrum and AP, without voice mapping. It still runs WORLD analysis/synthesis and resampling. Not a target identity test or realtime measurement.'}
(output / 'manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
(ROOT / 'report/prepared_clarity_diagnostic_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
