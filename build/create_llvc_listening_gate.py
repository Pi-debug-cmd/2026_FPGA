"""Target / WORLD / original-checkpoint LLVC preview, file-only."""
import gzip
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16, file_sha256

base = ROOT / 'data/registrations/source_20261015/speaker01'
audit = ROOT / 'build/generated/llvc_host_audit_20261015'
parity = json.loads((ROOT / 'report/llvc_checkpoint_parity_20261015.json').read_text(encoding='utf-8'))
if not parity['all_bytes_outside_computed_label_constant_identical']:
    raise ValueError('Checkpoint/export verification incomplete')
length = 80000
rate, target = read_pcm_wav(ROOT / 'voice_src/src_1/Track 9(1).wav')
target = downsample_16k(rate, target)[11 * 16000:16 * 16000]
_, old = read_pcm_wav(base / 'hybrid_comparison/old_fixed.wav')
old = old[round(2.68 * 16000):round(7.68 * 16000)]
neural_path = audit / 'python_output.f32'
if file_sha256(neural_path) != parity['python_output_sha256']:
    raise ValueError('Python output changed')
neural = np.fromfile(neural_path, dtype='<f4')[16000:96000].astype(np.float64)
segments = [target, old, neural]
if any(len(x) != length or not np.all(np.isfinite(x)) for x in segments):
    raise ValueError('Invalid crop')
rms = [float(np.sqrt(np.mean(x * x))) for x in segments]
if min(rms) <= 1e-10:
    raise ValueError('Silent crop')
common = min([.08] + [.85 * level / max(float(np.max(np.abs(x))), 1e-12)
                       for x, level in zip(segments, rms)])
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
peak = float(np.max(np.abs(joined)))
if peak >= 1 or not np.all(np.isfinite(joined)):
    raise ValueError('Invalid comparison')
out = base / 'llvc_reference_comparison'
out.mkdir(exist_ok=True)
audio, packed = out / 'comparison.wav', out / 'comparison.wav.gz'
write_pcm16(audio, joined, 32000)
packed.write_bytes(gzip.compress(audio.read_bytes(), compresslevel=9, mtime=0))
record = {'kind': 'llvc_original_checkpoint_listening_gate', 'order': ['target', 'world_old_fixed', 'llvc_python_fp32'],
          'duration_s': len(joined) / 32000, 'rate': 32000, 'segment_seconds': 5,
          'gap_seconds': 1, 'leading_silence_seconds': 1, 'gains': gains,
          'source_crop_start_s': 2.68, 'target_crop_start_s': 11., 'neural_input_start_s': 1.68,
          'neural_warmup_discarded_s': 1., 'checkpoint_sha256': parity['checkpoint_sha256'],
          'neural_output_sha256': file_sha256(neural_path), 'peak': peak,
          'clip_fraction': float(np.mean(np.abs(joined) >= 1)),
          'wav_sha256': file_sha256(audio), 'gzip_sha256': file_sha256(packed),
          'speaker_identity_accepted': False, 'realtime_accepted': False,
          'limitations': 'Historical fixed-target original checkpoint, not generated from this source preparation. No new target registration interface. Same development utterance; not blind or independent identity evaluation. Python streaming state warmed with one second, WORLD analyzed the full recording; context differs. Shared loudness target does not guarantee perceived loudness equality. Host output preview, not board computation.'}
(out / 'manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
(ROOT / 'report/llvc_listening_gate_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
