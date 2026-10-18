"""Offline disjoint-segment gate, using existing recordings without audio I/O."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'build/generated/world_deps'))
import pyworld as world
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16, file_sha256
from src.reference.source_target_mapping import fit_pitch_mapping, map_pitch
from src.reference.timbre_envelope import normalized_log_shape, register_envelope, apply_envelope


def analyze(signal):
    signal = np.ascontiguousarray(signal, dtype=np.float64)
    f0, times = world.dio(signal, 16000, f0_floor=75, f0_ceil=400,
                         frame_period=10, speed=4)
    f0 = world.stonemask(signal, f0, times, 16000)
    centers = np.rint(times * 16000).astype(int)
    left, right = np.maximum(0, centers - 320), np.minimum(len(signal), centers + 320)
    energy = np.r_[0., np.cumsum(signal * signal)]
    f0[(energy[right] - energy[left]) / np.maximum(1, right - left) < 10 ** -4.5] = 0
    sp = world.cheaptrick(signal, f0, times, 16000, fft_size=1024)
    ap = world.d4c(signal, f0, times, 16000, fft_size=1024)
    return f0, sp, ap


def load(path):
    rate, signal = read_pcm_wav(path)
    return downsample_16k(rate, signal)


def main():
    output = ROOT / 'data/registrations/source_20261011/source_mapping_20261015'
    output.mkdir(parents=True, exist_ok=True)
    source_path = ROOT / 'data/registrations/source_20261011/capture.wav'
    source = load(source_path)
    # Split raw waveform before analysis: no frame, FIR or WORLD context crosses split.
    split = len(source) // 2
    train, test = source[:split].copy(), source[split:].copy()
    train_f0, train_sp, _ = analyze(train)
    target_record = json.loads((ROOT / 'data/profiles/target.json').read_text(encoding='utf-8'))
    target_f0, shapes, counts = [], [], []
    for entry in target_record['source_files']:
        path = ROOT / entry['path']
        if file_sha256(path) != entry['sha256']:
            raise ValueError('Target enrollment hash changed')
        f0, sp, _ = analyze(load(path))
        target_f0.extend(f0)
        shapes.append(normalized_log_shape(sp, f0 > 0))
        counts.append(int(np.sum(f0 > 0)))
        print('TARGET_ANALYZED', path.name, flush=True)
    pitch = fit_pitch_mapping(train_f0, target_f0)
    envelope = register_envelope(normalized_log_shape(train_sp, train_f0 > 0),
                                 np.average(shapes, axis=0, weights=counts), 16000)
    # Retain the earlier light correction ceiling; this remains a listening candidate.
    limit = 3 * np.log(10) / 10
    envelope['log_power_delta'] = np.clip(envelope['log_power_delta'], -limit, limit).tolist()
    envelope['gain_limit_db'] = 3
    (output / 'mapping.json').write_text(json.dumps({'pitch': pitch, 'envelope': envelope}, indent=2), encoding='utf-8')
    f0, sp, ap = analyze(test)
    fixed = dict(envelope, formant_warp=1.15, log_power_delta=[0.] * 513)
    variants = {
        'identity': (f0, sp),
        'fixed_pitch_only': (f0 * (108722 / 65536), sp),
        'fixed_recipe': (f0 * (108722 / 65536), apply_envelope(sp, f0 > 0, fixed, .65)),
        'calibrated_pitch_only': (map_pitch(f0, pitch), sp),
        'calibrated_timbre': (map_pitch(f0, pitch), apply_envelope(sp, f0 > 0, envelope, .65)),
    }
    rendered, metrics = {}, {}
    for name, (mapped_f0, mapped_sp) in variants.items():
        signal = world.synthesize(np.ascontiguousarray(mapped_f0), np.ascontiguousarray(mapped_sp),
                                  ap, 16000, frame_period=10)[:len(test)]
        if len(signal) != len(test) or not np.all(np.isfinite(signal)):
            raise ValueError('Invalid render: ' + name)
        rendered[name] = signal
        voiced = mapped_f0[mapped_f0 > 0]
        metrics[name] = {'parameter_f0_median_hz': float(np.median(voiced)),
                         'parameter_f0_p10_p90_hz': np.percentile(voiced, [10, 90]).tolist(),
                         'raw_peak': float(np.max(np.abs(signal))),
                         'raw_clip_samples': int(np.sum(np.abs(signal) >= 1))}
    # One common file gain preserves level differences and exposes raw clipping above.
    gain = min(1., .9 / max(np.max(np.abs(x)) for x in rendered.values()))
    for name, signal in rendered.items():
        path = output / (name + '.wav')
        write_pcm16(path, signal * gain)
        metrics[name]['wav_sha256'] = file_sha256(path)
    record = {'date': '2026-10-15', 'kind': 'offline_single_source_disjoint_segment_gate',
              'source': str(source_path.relative_to(ROOT)), 'source_sha256': file_sha256(source_path),
              'split_sample_16k': split, 'calibration_seconds': len(train) / 16000,
              'test_seconds': len(test) / 16000, 'calibration_voiced_frames': int(np.sum(train_f0 > 0)),
              'test_voiced_frames': int(np.sum(f0 > 0)), 'target_enrollment': target_record['source_files'],
              'target_holdout_not_loaded': target_record['held_out_file'], 'pitch_mapping': pitch,
              'common_archive_gain': float(gain), 'variants': metrics,
              'acceptance': {'numeric_render': True, 'cross_speaker': False, 'listening': False, 'realtime': False},
              'limitations': 'Only one known source speaker; halves of one session are not independent sessions. Whole-segment WORLD analysis, not causal runtime. F0 parameter agreement is not speaker identity. Mean envelope mixes phonemes and microphones; unchanged source AP. Raw clipping remains recorded; common archive attenuation is not a live limiter.'}
    (ROOT / 'report/source_mapping_offline_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2), flush=True)


if __name__ == '__main__':
    main()
