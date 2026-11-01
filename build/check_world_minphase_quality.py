"""Full-speech host check of the fused minimum-phase model against WORLD."""
import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--exe', type=Path, required=True)
p.add_argument('--input', type=Path, action='append', required=True)
p.add_argument('--out', type=Path, required=True)
args = p.parse_args()
assert not args.out.exists(), 'Preserve old evidence'
result = {'kind': 'world_minphase_fused_host',
          'exe_sha256': hashlib.sha256(args.exe.read_bytes()).hexdigest(), 'runs': []}
for source in args.input:
    data = source.read_bytes()
    assert len(data) == 160000, 'Expected 5 seconds mono PCM16 at 16kHz'
    reference = None
    for mode in ['cpu', 'fused']:
        run = subprocess.run([str(args.exe.resolve()), '5', 'pcm16', '0', '39322'],
                             input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=dict(os.environ, WORLD_MINPHASE_MODEL=mode, WORLD_EXP='cpu'),
                             timeout=90)
        assert run.returncode == 0, run.stderr.decode(errors='replace')
        assert len(run.stdout) == len(data)
        samples = array.array('h', run.stdout)
        if reference is None:
            reference = samples
        error = sum((a-b)**2 for a, b in zip(samples, reference))
        energy = sum(a*a for a in reference)
        maximum = max(abs(a-b) for a, b in zip(samples, reference))
        snr = 10*math.log10(energy/max(error, 1e-30))
        telemetry = [json.loads(s) for s in run.stderr.decode().splitlines() if s.startswith('{')]
        if mode == 'fused':
            assert next(t for t in telemetry if t.get('kind') == 'world_minphase_model')['calls'] > 0
        assert maximum <= 3 and snr >= 75, (source, mode, maximum, snr)
        result['runs'].append(dict(input_name=source.parent.name, mode=mode,
                                  input_sha256=hashlib.sha256(data).hexdigest(),
                                  output_sha256=hashlib.sha256(run.stdout).hexdigest(),
                                  max_pcm16_error=maximum, snr_db=snr, telemetry=telemetry))
result['passed'] = True
args.out.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps([(r['input_name'], r['mode'], r['max_pcm16_error'], r['snr_db'])
                  for r in result['runs']]))
