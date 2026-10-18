"""Listening gate for faster estimators; all processing remains offline."""
import gzip
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16

parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--stream', action='store_true', help='Compare approved batch output against ARM persistent synthesis')
mode.add_argument('--sliding', action='store_true', help='Compare approved batch output against ARM sliding analysis variants')
args = parser.parse_args()
parent = root / 'data/registrations/source_20261011'
base = parent / ('world_sliding_comparison_20261012' if args.sliding else
                 'world_stream_comparison_20261012' if args.stream else 'world_budget_comparison')
base.mkdir(exist_ok=True)
record = json.loads((parent / 'comparison_manifest.json').read_text())
target_rate, target = read_pcm_wav(root / 'voice_src/src_1/Track 9(1).wav')
target = downsample_16k(target_rate, target)
_, approved = read_pcm_wav(parent / 'world_light_experiment/world_warp_only.wav')
_, dio = read_pcm_wav(root / 'build/generated/world_budget/dio_arm.wav')
_, fast = read_pcm_wav(root / 'build/generated/world_budget/dio_fast_v3_arm.wav')
source_start = round(record['source_start_s'] * 16000)
target_start = round(record['target_start_s'] * 16000)
if args.sliding:
    _, sliding30 = read_pcm_wav(base / 'sliding30_arm.wav')
    _, sliding40 = read_pcm_wav(base / 'sliding40_arm.wav')
    segments = [target[target_start:target_start + 80000], fast, sliding30, sliding40]
elif args.stream:
    _, streamed = read_pcm_wav(base / 'stream5_arm.wav')
    segments = [target[target_start:target_start + 80000], fast, streamed]
else:
    segments = [target[target_start:target_start + 80000], approved[source_start:source_start + 80000], dio, fast]
offsets = np.arange(127) - 63
kernel = 2 * .225 * np.sinc(2 * .225 * offsets) * np.hamming(127)
kernel *= 2 / kernel.sum()
rendered, gains = [], []
rms_values = [float(np.sqrt(np.mean(signal * signal))) for signal in segments]
peaks = [float(np.max(np.abs(signal))) for signal in segments]
# Choose one feasible RMS for every segment, avoiding separate peak-limit gains.
common_rms = min([.1] + [.9 * rms / max(peak, 1e-12)
                        for rms, peak in zip(rms_values, peaks)])
for signal, rms in zip(segments, rms_values):
    if len(signal) != 80000 or not np.all(np.isfinite(signal)):
        raise ValueError('Invalid comparison segment')
    gain = common_rms / max(rms, 1e-12)
    expanded = np.zeros(160000)
    expanded[::2] = signal * gain
    rendered.append(np.convolve(expanded, kernel, mode='same'))
    gains.append(gain)
joined = np.concatenate([part for i, segment in enumerate(rendered)
                         for part in ([np.zeros(32000), segment] if i else [segment])])
write_pcm16(base / 'comparison.wav', joined, 32000)
raw = (base / 'comparison.wav').read_bytes()
packed = gzip.compress(raw, mtime=0)
(base / 'comparison.wav.gz').write_bytes(packed)
manifest = {'kind': ('offline_world_sliding_listening_gate' if args.sliding else
                     'offline_world_stream_listening_gate' if args.stream else 'offline_world_arm_budget_listening_gate'),
            'order': (['target', 'approved_arm_batch', 'sliding_analysis_30ms', 'sliding_analysis_40ms'] if args.sliding else
                      ['target', 'approved_arm_batch', 'persistent_arm_synthesis'] if args.stream else
                      ['target', 'previous_approved_harvest_warp', 'arm_dio_5ms', 'arm_dio_10ms']),
            'rate': 32000, 'duration_s': len(joined) / 32000, 'segment_seconds': 5, 'gap_seconds': 1,
            'gains': gains, 'peak': float(np.max(np.abs(joined))),
            'common_rms_before_interpolation': common_rms,
            'clip_fraction': float(np.mean(np.abs(joined) >= 1)),
            'wav_sha256': hashlib.sha256(raw).hexdigest(), 'gzip_sha256': hashlib.sha256(packed).hexdigest(),
            'limitation': ('Offline WAV preview of causal-window analysis with 160ms history, 40ms analysis future and 32ms synthesis lookahead; stages still run serially. No live capture or latency acceptance.' if args.sliding else
                          'Offline only. ARM batch and persistent synthesis use the same complete five-second analysis. Persistent synthesis receives 5 frames per call, but there is no live capture or end-to-end latency measurement.' if args.stream else
                          'Offline only. Approved segment analyzed in full recording; ARM segments analyzed as 5-second crop, so context boundaries differ. Both ARM segments share crop. Timings are not streaming latency.')}
(base / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
