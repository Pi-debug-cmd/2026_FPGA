"""Register confirmed single-speaker clips; reserve the last clip for evaluation."""
import json
from pathlib import Path

import numpy as np

from src.reference.audio_io import downsample_16k, file_sha256, read_pcm_wav
from src.reference.voice_profile import build_profile

root = Path(__file__).resolve().parents[1]
files = sorted((root / 'voice_src/src_1').glob('*.wav'))
if len(files) < 2:
    raise ValueError('Need calibration clips and a separate held-out clip')
heldout = files[-1]
segments, rows = [], []
for path in files:
    rate, samples = read_pcm_wav(path, 0)
    native_clip = float(np.mean(abs(samples) >= 32760 / 32768))
    row = {'path': str(path.relative_to(root)), 'sha256': file_sha256(path),
           'input_rate': rate, 'channel': 0, 'duration_s': len(samples) / rate,
           'native_clip_fraction': native_clip, 'held_out': path == heldout}
    try:
        if native_clip > 0.01:
            raise ValueError('Original recording has more than 1% clipped samples')
        mono16 = downsample_16k(rate, samples)
        profile = build_profile(mono16)
        row.update({'accepted': True, 'profile': profile})
        if path != heldout:
            segments.append(mono16)
    except ValueError as exc:
        row.update({'accepted': False, 'reason': str(exc)})
    rows.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
(root / 'report/target_audio_quality_20261011.json').write_text(
    json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if not segments:
    raise ValueError('No usable target registration clip; previous target retained')
target = build_profile(np.concatenate(segments))
target['source_files'] = [{key: row[key] for key in ['path', 'sha256', 'channel']}
                          for row in rows if row['accepted'] and not row['held_out']]
target['held_out_file'] = str(heldout.relative_to(root))
target['speaker_consistency'] = 'same speaker, clean speech, confirmed by user'
output = root / 'data/profiles/target.json'
output.parent.mkdir(parents=True, exist_ok=True)
temporary = output.with_suffix('.json.tmp')
temporary.write_text(json.dumps(target, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(output)
print('TARGET_REGISTERED', target['f0_median_hz'], target['voiced_frame_coverage_s'])
