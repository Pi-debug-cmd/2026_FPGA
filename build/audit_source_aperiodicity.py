"""Compare preparation and target aperiodicity without altering conversion."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'build/generated/world_deps'))
import pyworld as world
from src.reference.audio_io import file_sha256
from src.reference.world_registration import analyze, load_enrollment


def measure(path):
    signal = load_enrollment(path)
    f0, times, spectrum = analyze(signal)
    ap = world.d4c(np.ascontiguousarray(signal), f0, times, 16000, fft_size=1024)
    voiced = f0 > 0
    if not voiced.any():
        raise ValueError('No voiced frames')
    frequency = np.linspace(0, 8000, 513)
    metrics = {}
    for name, low, high in [('below_1k', 0, 1000), ('1k_3k', 1000, 3000), ('3k_8k', 3000, 8001)]:
        bins = (frequency >= low) & (frequency < high)
        # WORLD's synthesis converts AP to an aperiodic power ratio by squaring.
        ratio = (np.sum(spectrum[voiced][:, bins] * ap[voiced][:, bins] ** 2, axis=1) /
                 np.sum(spectrum[voiced][:, bins], axis=1))
        metrics[name] = {'aperiodic_power_ratio_p10_p50_p90': np.percentile(ratio, [10, 50, 90]).tolist()}
    return {'sha256': file_sha256(path), 'voiced_frames': int(np.sum(voiced)),
            'unvoiced_frames': int(np.sum(~voiced)), 'bands': metrics}


def main():
    base = ROOT / 'data/registrations/source_20261015/speaker01'
    manifest = json.loads((ROOT / 'data/profiles/target.json').read_text(encoding='utf-8'))
    target = {}
    for entry in manifest['source_files']:
        path = ROOT / entry['path']
        if file_sha256(path) != entry['sha256']:
            raise ValueError('Enrollment changed')
        target[path.name] = measure(path)
    record = {'source_preparation': measure(base / 'preparation_cue_v2.wav'),
              'source_development_sentence': measure(base / 'holdout.wav'),
              'target_enrollment': target, 'target_holdout_used_to_fit': False,
              'configuration_changed': False, 'new_recording_or_playback': False,
              'limitations': 'AP is a vocoder parameter, not a standalone breath/hoarseness detector. Text, pitch, microphone and phonemes confound comparisons. Unvoiced breaths and consonants require a different distinction; suppressing all unvoiced material is not valid. No causal or identity acceptance from these metrics.'}
    (ROOT / 'report/source_aperiodicity_audit_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
