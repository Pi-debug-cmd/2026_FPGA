"""Offline target/WORLD/Seed reference preview; never plays audio."""
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/generated/seed_cpu_deps'))
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.signal import resample_poly
import soundfile as sf
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16, file_sha256

base = ROOT / 'data/registrations/source_20261015/speaker01'
reference = json.loads((ROOT / 'report/seed_cpu_reference_steps30_20261015.json').read_text(encoding='utf-8'))
generated = Path(reference['output'])
if file_sha256(generated) != reference['output_sha256']:
    raise ValueError('Reference audio changed')
length = 76800  # 4.8 seconds; leaves a margin inside the 5.99075-second result.
rate, target = read_pcm_wav(ROOT / 'voice_src/src_1/Track 9(1).wav')
target = downsample_16k(rate, target)[176000:176000 + length]
_, old = read_pcm_wav(base / 'hybrid_comparison/old_fixed.wav')
old = old[42880:42880 + length]
neural, rate = sf.read(generated, dtype='float64')  # Reference writes IEEE-float WAV.
if rate != 22050:
    raise ValueError('Unexpected reference rate')
neural = resample_poly(neural, 320, 441)[16000:16000 + length]
segments = [target, old, neural]
if any(len(x) != length or not np.all(np.isfinite(x)) for x in segments):
    raise ValueError('Invalid listening segment')
rms = [float(np.sqrt(np.mean(x * x))) for x in segments]
if min(rms) <= 1e-10:
    raise ValueError('Silent segment')
common = min([.08] + [.85 * level / max(float(np.max(np.abs(x))), 1e-12) for x, level in zip(segments, rms)])
offset = np.arange(127) - 63
kernel = 2 * .225 * np.sinc(2 * .225 * offset) * np.hamming(127)
kernel *= 2 / kernel.sum()
parts, gains = [], []
for x, level in zip(segments, rms):
    gain = common / level
    expanded = np.zeros(length * 2)
    expanded[::2] = x * gain
    parts.append(np.convolve(expanded, kernel, mode='same'))
    gains.append(gain)
joined = np.concatenate([np.zeros(32000)] + [part for i, segment in enumerate(parts)
                         for part in ([np.zeros(32000), segment] if i else [segment])])
if np.max(np.abs(joined)) >= 1 or not np.all(np.isfinite(joined)):
    raise ValueError('Invalid comparison waveform')
out = base / 'seed_reference_comparison'
out.mkdir(exist_ok=True)
audio, packed = out / 'comparison.wav', out / 'comparison.wav.gz'
write_pcm16(audio, joined, 32000)
packed.write_bytes(gzip.compress(audio.read_bytes(), compresslevel=9, mtime=0))
record = {'kind': 'seed_tiny_cpu_quality_listening_gate', 'order': ['target', 'world_old_fixed', 'seed_tiny_steps30'],
          'duration_s': len(joined) / 32000, 'rate': 32000, 'segment_seconds': 4.8,
          'gap_seconds': 1, 'leading_silence_seconds': 1, 'source_crop_start_s': 2.68,
          'target_crop_start_s': 11., 'reference_output_sha256': reference['output_sha256'],
          'gains': gains, 'peak': float(np.max(np.abs(joined))), 'clip_fraction': 0.,
          'wav_sha256': file_sha256(audio), 'gzip_sha256': file_sha256(packed),
          'speaker_identity_accepted': False, 'board_realtime_accepted': False,
          'limitations': 'PC offline quality reference only. General pretrained weights plus Track8 target prompt; no source enrollment used. Not the historical LLVC model. Full-context reference vs WORLD have different analysis context and preprocessing; timing/level differ. Existing development utterance, not final blind evaluation. Not deployed or assumed deployable on Zynq.'}
(out / 'manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
(ROOT / 'report/seed_reference_listening_gate_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
