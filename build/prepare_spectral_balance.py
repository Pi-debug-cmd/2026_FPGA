"""Fit broad tilt from preparation/target enrollment; never use test utterances."""
import json
import argparse
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'build/generated/world_deps'))
from src.reference.world_registration import analyze, load_enrollment, save_configuration
from src.reference.audio_io import file_sha256
from src.reference.timbre_envelope import normalized_log_shape, apply_envelope
from src.reference.spectral_balance import fit_balance, fit_low_shelf

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--low-shelf', action='store_true')
args = parser.parse_args()

base = ROOT / 'data/registrations/source_20261015/speaker01'
source_path = base / 'preparation_cue_v2.wav'
f0, _, sp = analyze(load_enrollment(source_path))
old = apply_envelope(sp, f0 > 0, {'formant_warp': 1.15, 'log_power_delta': [0.] * 513}, .65)
source_shape = normalized_log_shape(old, f0 > 0)
manifest_path = ROOT / 'data/profiles/target.json'
target_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
shapes, counts = [], []
for entry in target_manifest['source_files']:
    path = ROOT / entry['path']
    if file_sha256(path) != entry['sha256']:
        raise ValueError('Target enrollment changed')
    pitch, _, spectrum = analyze(load_enrollment(path))
    shapes.append(normalized_log_shape(spectrum, pitch > 0))
    counts.append(int(np.sum(pitch > 0)))
profile = (fit_low_shelf(source_shape, shapes) if args.low_shelf else
           fit_balance(source_shape, np.average(shapes, axis=0, weights=counts)))
profile.update({'source_sha256': file_sha256(source_path), 'source_voiced_frames': int(np.sum(f0 > 0)),
                'target_manifest_sha256': file_sha256(manifest_path), 'target_enrollment': target_manifest['source_files'],
                'target_holdout_used': False, 'evaluation_utterance_used': False,
                'baseline_spectrum_warp': 1.0975, 'baseline_pitch_ratio_q16': 108722,
                'limitations': 'Global spectral tilt confounds phonemes and microphones; not identity or hoarseness detection. Only voiced frames mapped; source AP preserved. Not accepted for realtime.'})
save_configuration(base / ('low_shelf_profile.json' if args.low_shelf else 'spectral_balance_profile.json'), profile)
print(json.dumps({key: value for key, value in profile.items() if key != 'power_tilt_db'}, indent=2))
