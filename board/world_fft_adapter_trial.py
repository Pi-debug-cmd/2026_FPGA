"""Compare PS adapters on one resident FFT bitstream, silently (no ALSA)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--base', type=Path, required=True)
p.add_argument('--old', type=Path, required=True)
p.add_argument('--new', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
args = p.parse_args()
assert not args.output.exists(), 'Use a fresh evidence path'
assert Path('/sys/class/fpga_manager/fpga0/state').read_text().strip() == 'operating'
assert Path('/dev/world_fft').exists() and Path('/dev/world_exp').exists()
result = {'kind': 'world_fft_adapter_same_bitstream', 'repetitions': 3,
          'binaries': {k: hashlib.sha256(v.read_bytes()).hexdigest()
                       for k, v in [('old', args.old), ('new', args.new)]},
          'inputs': {}, 'runs': []}
for clip in ['male1', 'male4']:
    data = (args.base/(clip+'.raw')).read_bytes()
    result['inputs'][clip] = hashlib.sha256(data).hexdigest()
    for repeat in range(3):
        # Alternate order to reduce temperature/scheduling order bias.
        order = [('old', args.old), ('new', args.new)]
        if repeat % 2:
            order.reverse()
        for mode, exp, fft in [('cpu', 'cpu', 'cpu'),
                               ('exp_only', 'pl', 'cpu'),
                               ('combined', 'pl', 'pl2048')]:
            expected = (args.base/(clip+'_'+mode+'.raw')).read_bytes()
            for label, binary in order:
                env = dict(os.environ, WORLD_EXP=exp, WORLD_FFT=fft, WORLD_FFT_CACHE='1')
                start = time.monotonic()
                run = subprocess.run([str(binary), '5', 'pcm16', '0', '39322'],
                                     input=data, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, env=env, timeout=45)
                wall = time.monotonic()-start
                telemetry = [json.loads(s) for s in run.stderr.decode().splitlines()
                             if s.startswith('{')]
                assert run.returncode == 0, run.stderr.decode(errors='replace')
                assert run.stdout == expected, (clip, repeat, mode, label, 'output mismatch')
                if exp == 'pl':
                    backend = next(t for t in telemetry if t.get('kind') == 'world_exp_backend')
                    assert backend['calls'] > 0 and backend['fallback'] == 0
                result['runs'].append(dict(clip=clip, repeat=repeat, mode=mode,
                                          adapter=label, wall_s=wall,
                                          output_sha256=hashlib.sha256(run.stdout).hexdigest(),
                                          exact_round10_output=True, telemetry=telemetry))
                args.output.write_text(json.dumps(result, indent=2)+'\n')
                print(clip, repeat, mode, label, wall, flush=True)
result['passed'] = True
args.output.write_text(json.dumps(result, indent=2)+'\n')
