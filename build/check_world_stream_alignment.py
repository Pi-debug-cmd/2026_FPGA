"""Native regression: partition invariance, voiced transitions and batch fidelity."""
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.reference.audio_io import read_pcm_wav, write_pcm16

base = root / 'build/generated/world_budget/alignment_checks'
base.mkdir(exist_ok=True)
program = root / 'build/generated/world_budget/world_stream_native_v7.exe'
time = np.arange(32000) / 16000
fixtures = {'silence': np.zeros(8000)}
for name, center in [('low_voice_transitions', 110), ('high_voice_transitions', 250)]:
    f0 = center + 25 * np.sin(2 * np.pi * .8 * time)
    phase = 2 * np.pi * np.cumsum(f0) / 16000
    signal = .1 * np.sin(phase) + .03 * np.sin(2 * phase) + .01 * np.sin(3 * phase)
    signal[(time >= .75) & (time < 1.1)] = 0
    fixtures[name] = signal
results = []
for name, signal in fixtures.items():
    input_path = base / (name + '.wav')
    write_pcm16(input_path, signal)
    rendered = {}
    for mode in ['fast', 'stream5', 'stream25']:
        output = base / (name + '_' + mode + '.wav')
        completed = subprocess.run([str(program), str(input_path), str(output), 'dio', mode],
                                   check=True, capture_output=True, text=True, timeout=30)
        rate, values = read_pcm_wav(output)
        if rate != 16000 or len(values) != len(signal) or not np.all(np.isfinite(values)):
            raise ValueError('Invalid native output')
        rendered[mode] = values
    batch, stream = rendered['fast'], rendered['stream5']
    # Batch EOF uses a zero-length final noise interval; streaming drains padding.
    # Exclude its documented 80 ms tail, but include starts and internal transitions.
    error = batch[:-1280] - stream[:-1280]
    row = {'fixture': name, 'partition_identical_pcm': bool(np.array_equal(stream, rendered['stream25'])),
           'body_rmse': float(np.sqrt(np.mean(error ** 2))),
           'body_max_error': float(np.max(np.abs(error))),
           'clip_fraction': float(np.mean(np.abs(stream) >= 32760 / 32768))}
    results.append(row)
    if not row['partition_identical_pcm'] or row['body_rmse'] > 1e-5 or row['clip_fraction']:
        raise ValueError('Alignment regression failed: ' + json.dumps(row))
record = {'checks': results, 'excluded_tail_ms': 80,
          'limitation': 'Complete-input analysis, not live capture or latency acceptance'}
(root / 'report/world_stream_alignment_checks_20261012.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
