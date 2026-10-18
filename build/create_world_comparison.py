"""Offline WORLD experiment; target Track 9 is never used to fit the mapping."""
import gzip
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'build/generated/world_deps'))
sys.path.insert(0, str(root))
import pyworld as world
from src.reference.audio_io import downsample_16k, read_pcm_wav, write_pcm16
from src.reference.timbre_envelope import normalized_log_shape, register_envelope, apply_envelope

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--variant', choices=['original', 'light'], default='original')
args = parser.parse_args()
experiment = 'world_experiment' if args.variant == 'original' else 'world_light_experiment'
base = root / 'data/registrations/source_20261011' / experiment
base.mkdir(exist_ok=True)
target_profile = json.loads((root / 'data/profiles/target.json').read_text())
ratio = 108722 / 65536
measurements = []


def analyze(path):
    started = time.perf_counter()
    rate, signal = read_pcm_wav(path)
    signal = np.ascontiguousarray(downsample_16k(rate, signal))
    f0, times = world.harvest(signal, 16000, f0_floor=75, f0_ceil=400, frame_period=5)
    f0 = world.stonemask(signal, f0, times, 16000)
    # Silence gate: 40 ms centered energy windows, including edge truncation.
    centers = np.rint(times * 16000).astype(int)
    left, right = np.maximum(0, centers - 320), np.minimum(len(signal), centers + 320)
    energy = np.concatenate(([0.], np.cumsum(signal * signal)))
    rms = np.sqrt((energy[right] - energy[left]) / np.maximum(1, right - left))
    f0[rms < 10 ** (-45 / 20)] = 0
    # Median within voiced runs only; never bridge silence/unvoiced boundaries.
    voiced = f0 > 0
    edges = np.diff(np.concatenate(([False], voiced, [False])).astype(int))
    for start, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        original = f0[start:stop].copy()
        for i in range(len(original)):
            f0[start + i] = np.median(original[max(0, i - 2):i + 3])
    spectrum = world.cheaptrick(signal, f0, times, 16000, fft_size=1024)
    aperiodicity = world.d4c(signal, f0, times, 16000, fft_size=1024)
    elapsed = time.perf_counter() - started
    measurements.append({'file': str(path.relative_to(root)), 'analysis_seconds_host': elapsed,
                         'audio_seconds': len(signal) / 16000, 'voiced_seconds': float(voiced.sum() * .005),
                         'f0_median_hz': float(np.median(f0[voiced]))})
    if not voiced.any():
        raise ValueError('No voiced speech: ' + str(path))
    print('ANALYZED', path.name, round(elapsed, 3), flush=True)
    return signal, f0, spectrum, aperiodicity, voiced


source_path = root / 'data/registrations/source_20261011/capture.wav'
source, f0, spectrum, ap, voiced = analyze(source_path)
source_shape = normalized_log_shape(spectrum, voiced)
weighted_shape = np.zeros(513)
weight = 0
for item in target_profile['source_files']:
    path = root / item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('Enrollment file changed')
    _, _, target_sp, _, target_voiced = analyze(path)
    count = int(target_voiced.sum())
    weighted_shape += normalized_log_shape(target_sp, target_voiced) * count
    weight += count
profile = register_envelope(source_shape, weighted_shape / weight, 16000)
(base / 'fitted_envelope_profile.json').write_text(json.dumps(profile, indent=2) + '\n')
if args.variant == 'light':
    # Isolate the broad mean-spectrum correction after the "too heavy" feedback.
    # Smoothly suppress its positive low-band gain; keep negative corrections.
    frequency = np.linspace(0, 8000, 513)
    delta = np.asarray(profile['log_power_delta'])
    ramp = np.clip((frequency - 800) / 400, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)
    delta = np.minimum(delta, 0) + np.maximum(delta, 0) * ramp
    profile = dict(profile, log_power_delta=np.clip(delta, -3 * np.log(10) / 10,
                                                    3 * np.log(10) / 10).tolist(),
                   gain_limit_db=3, low_positive_gain_taper_hz=[800, 1200])
(base / 'envelope_profile.json').write_text(json.dumps(profile, indent=2) + '\n')
outputs = {}
renders = [('identity', f0, 0), ('world_pitch', f0 * ratio, 0), ('world_timbre', f0 * ratio, .65)]
if args.variant == 'light':
    renders.append(('world_warp_only', f0 * ratio, .65))
for name, pitch, strength in renders:
    active_profile = (dict(profile, log_power_delta=[0.] * 513)
                      if name == 'world_warp_only' else profile)
    sp = apply_envelope(spectrum, voiced, active_profile, strength)
    started = time.perf_counter()
    result = world.synthesize(pitch, np.ascontiguousarray(sp), ap, 16000, frame_period=5)
    result = result[:len(source)]
    if len(result) != len(source) or not np.all(np.isfinite(result)):
        raise ValueError('Invalid synthesis')
    outputs[name] = result
    peak = float(np.max(np.abs(result)))
    # Archive unnormalized output statistics; WAV headroom gain is explicit.
    gain = min(1., .95 / max(peak, 1e-12))
    write_pcm16(base / (name + '.wav'), result * gain)
    measurements.append({'render': name, 'synthesis_seconds_host': time.perf_counter() - started,
                         'raw_peak': peak, 'raw_clip_fraction': float(np.mean(np.abs(result) >= 1)),
                         'archive_gain': gain, 'rms': float(np.sqrt(np.mean(result * result)))})

# Common 5-second crop and loudness handling across old and new processing.
parent = base.parent
old_record = json.loads((parent / 'comparison_manifest.json').read_text())
target_rate, target = read_pcm_wav(root / target_profile['held_out_file'])
target = downsample_16k(target_rate, target)
old_path = (parent / 'predicted_registered.wav' if args.variant == 'original'
            else parent / 'world_experiment/world_timbre.wav')
old_rate, old = read_pcm_wav(old_path)
old = downsample_16k(old_rate, old)
start = round(old_record['source_start_s'] * 16000)
target_start = round(old_record['target_start_s'] * 16000)
length = 80000
third = 'world_pitch' if args.variant == 'original' else 'world_warp_only'
segments = [target[target_start:target_start + length], old[start:start + length],
            outputs[third][start:start + length], outputs['world_timbre'][start:start + length]]
gains, rendered = [], []
offsets = np.arange(127) - 63
kernel = 2 * .225 * np.sinc(2 * .225 * offsets) * np.hamming(127)
kernel *= 2 / kernel.sum()
for segment in segments:
    if len(segment) != length:
        raise ValueError('Incomplete comparison crop')
    rms, peak = float(np.sqrt(np.mean(segment * segment))), float(np.max(np.abs(segment)))
    gain = min(.1 / max(rms, 1e-12), .95 / max(peak, 1e-12))
    expanded = np.zeros(length * 2)
    expanded[::2] = segment * gain
    rendered.append(np.convolve(expanded, kernel, mode='same'))
    gains.append(gain)
joined = np.concatenate([part for i, segment in enumerate(rendered)
                         for part in ([np.zeros(32000), segment] if i else [segment])])
write_pcm16(base / 'comparison.wav', joined, 32000)
raw = (base / 'comparison.wav').read_bytes()
packed = gzip.compress(raw, compresslevel=9, mtime=0)
(base / 'comparison.wav.gz').write_bytes(packed)
order = (['target', 'old_pitch', 'world_pitch', 'world_timbre'] if args.variant == 'original'
         else ['target', 'previous_world_timbre', 'world_warp_only', 'world_light_timbre'])
record = {'kind': 'offline_world_timbre_experiment', 'variant': args.variant, 'order': order,
          'segment_seconds': 5, 'gap_seconds': 1, 'duration_s': len(joined) / 32000, 'rate': 32000,
          'ratio_q16': 108722, 'formant_warp_fit': profile['formant_warp'], 'strength': .65,
          'gains': gains, 'peak': float(np.max(np.abs(joined))),
          'clip_fraction': float(np.mean(np.abs(joined) >= 1)),
          'wav_sha256': hashlib.sha256(raw).hexdigest(), 'gzip_sha256': hashlib.sha256(packed).hexdigest(),
          'enrollment': target_profile['source_files'], 'held_out': target_profile['held_out_file'],
          'measurements': measurements, 'versions': {'pyworld': world.__version__, 'numpy': np.__version__},
          'limitation': 'Offline host synthesis only; no timbre similarity, board performance or latency acceptance. Mean envelopes confound phonemes and microphones. Source aperiodicity retained.'}
(base / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
(root / ('report/' + experiment + '_20261011.json')).write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: record[key] for key in ['duration_s', 'formant_warp_fit', 'peak', 'clip_fraction']}, indent=2))
