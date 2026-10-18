"""Independent YIN checks on archived synthesis; no speaker similarity claim."""
import json
import argparse
from pathlib import Path
import sys
import numpy as np
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.reference.audio_io import read_pcm_wav
from src.reference.voice_profile import estimate_f0
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--light', action='store_true')
args = parser.parse_args()
base = root / 'data/registrations/source_20261011' / ('world_light_experiment' if args.light else 'world_experiment')
checks = []
names = ['identity', 'world_pitch', 'world_timbre'] + (['world_warp_only'] if args.light else [])
for name in names:
    rate, signal = read_pcm_wav(base / (name + '.wav'))
    f0, total = estimate_f0(signal)
    if rate != 16000 or len(signal) != 240000 or len(f0) < 300:
        raise ValueError('Invalid duration or insufficient voiced content')
    checks.append({'name': name, 'f0_median_hz_yin': float(np.median(f0)),
                   'voiced_coverage_seconds_yin': len(f0) * .01,
                   'clip_fraction_pcm16': float(np.mean(np.abs(signal) >= 32760 / 32768))})
record = {'checks': checks, 'limitation': 'F0 checks do not measure timbre identity or audible flutter'}
(root / ('report/world_light_quality_20261011.json' if args.light else
         'report/world_quality_20261011.json')).write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
