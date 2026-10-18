"""Offline diagnostics for dullness; metrics do not establish perceived clarity."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'build/generated/world_deps'))
import pyworld as world
from src.reference.audio_io import read_pcm_wav, downsample_16k, file_sha256, write_pcm16
from src.reference.world_registration import analyze


def load(path):
    rate, signal = read_pcm_wav(path)
    return np.ascontiguousarray(downsample_16k(rate, signal))


def pitch(signal, estimator='dio', speed=4):
    if estimator == 'harvest':
        f0, times = world.harvest(np.ascontiguousarray(signal), 16000,
                                 f0_floor=75, f0_ceil=400, frame_period=10)
    else:
        f0, times = world.dio(np.ascontiguousarray(signal), 16000,
                             f0_floor=75, f0_ceil=400, frame_period=10, speed=speed)
    return world.stonemask(np.ascontiguousarray(signal), f0, times, 16000)


def band_metrics(signal, centers):
    # Common input-voiced frame centers for source and its converted variants.
    power = np.zeros(513)
    window = np.hanning(1024)
    accepted = 0
    for center in centers:
        if center < 512 or center + 512 > len(signal):
            continue
        frame = signal[center - 512:center + 512].copy()
        frame -= frame.mean()
        bins = np.abs(np.fft.rfft(frame * window)) ** 2
        power += bins / max(float(np.sum(bins)), 1e-30)
        accepted += 1
    power /= max(1, accepted)
    frequency = np.linspace(0, 8000, 513)
    bands = {'80_500_hz': (80, 500), '500_1500_hz': (500, 1500),
             '1500_3000_hz': (1500, 3000), '3000_8000_hz': (3000, 8001)}
    return {'frames': accepted, 'centroid_hz': float(np.sum(frequency * power)),
            'normalized_band_power': {name: float(np.sum(power[(frequency >= low) & (frequency < high)]))
                                      for name, (low, high) in bands.items()}}


def main():
    base = ROOT / 'data/registrations/source_20261015/speaker01'
    listening = json.loads((base / 'hybrid_comparison/manifest.json').read_text(encoding='utf-8'))
    source_first = round(listening['source_crop_start_s'] * 100)
    source_path = base / 'holdout.wav'
    source = load(source_path)
    f0, times, sp = analyze(source)
    ap = world.d4c(source, f0, times, 16000, fft_size=1024)
    identity = world.synthesize(f0, sp, ap, 16000, frame_period=10)[:len(source)]
    if len(identity) != len(source) or not np.all(np.isfinite(identity)):
        raise ValueError('Invalid identity synthesis')
    output = base / 'clarity_audit'
    output.mkdir(exist_ok=True)
    write_pcm16(output / 'identity.wav', identity)
    centers = np.rint(times[f0 > 0] * 16000).astype(int)
    variants = {'source': source, 'world_identity': identity}
    for name in ['old_fixed', 'prepared_pitch', 'prepared_timbre', 'prepared_pitch_old_warp']:
        variants[name] = load(base / 'hybrid_comparison' / (name + '.wav'))
    results = {}
    for name, signal in variants.items():
        estimated = pitch(signal)
        active = estimated > 0
        excerpt = estimated[source_first:source_first + 500]
        excerpt = excerpt[excerpt > 0]
        results[name] = {'reestimated_voiced_frames': int(np.sum(active)),
                         'reestimated_f0_p10_p50_p90': np.percentile(estimated[active], [10, 50, 90]).tolist() if active.any() else None,
                         'played_excerpt_f0_p10_p50_p90': np.percentile(excerpt, [10, 50, 90]).tolist() if len(excerpt) else None,
                         'peak': float(np.max(np.abs(signal))),
                         'spectral_metrics': band_metrics(signal, centers)}
    slow = pitch(source, speed=1)
    harvest = pitch(source, estimator='harvest')
    common = (f0 > 0) & (slow > 0)
    common_h = (f0 > 0) & (harvest > 0)
    target = load(ROOT / 'voice_src/src_1/Track 9(1).wav')
    target_pitch, target_times, _ = analyze(target)
    target_voiced = target_pitch > 0
    target_first = round(listening['target_crop_start_s'] * 100)
    target_excerpt = target_pitch[target_first:target_first + 500]
    target_excerpt = target_excerpt[target_excerpt > 0]
    record = {'source_sha256': file_sha256(source_path), 'variants': results,
              'identity_raw_clip_samples': int(np.sum(np.abs(identity) >= 1)),
              'dio_speed1_vs_speed4': {'common_voiced_frames': int(np.sum(common)),
                  'over_20_percent_relative_difference_frames': int(np.sum(np.abs(slow[common] / f0[common] - 1) > .2))},
              'harvest_vs_dio': {'harvest_voiced_frames': int(np.sum(harvest > 0)), 'common_voiced_frames': int(np.sum(common_h)),
                  'over_20_percent_relative_difference_frames': int(np.sum(np.abs(harvest[common_h] / f0[common_h] - 1) > .2))},
              'target_reference': {'f0_p10_p50_p90': np.percentile(target_pitch[target_voiced], [10, 50, 90]).tolist(),
                  'played_excerpt_f0_p10_p50_p90': np.percentile(target_excerpt, [10, 50, 90]).tolist(),
                  'spectral_metrics': band_metrics(target, np.rint(target_times[target_voiced] * 16000).astype(int))},
              'limitations': 'Same-estimator output pitch is not ground truth. Source/target differ in text, microphone and phonemes; spectral bands diagnose but cannot establish timbre identity or a cause of dullness. Offline whole-recording only; no new playback or configuration fitting.'}
    (ROOT / 'report/prepared_clarity_audit_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
