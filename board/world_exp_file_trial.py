"""Silent comparisons: current v23, CPU reference, integer model, and real PL.

No ALSA devices are opened. The PL candidate must already have been loaded.
"""
import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess


def compare(a_path, b_path):
    a, b = array.array('h'), array.array('h')
    a.frombytes(a_path.read_bytes())
    b.frombytes(b_path.read_bytes())
    assert len(a) == len(b) and len(a) > 0
    error = sum((x-y)**2 for x, y in zip(a, b))
    energy = sum(x*x for x in a)
    return {'samples': len(a), 'exact': a == b,
            'snr_db': 10*math.log10(energy/max(1,error)),
            'max_pcm16_error': max(abs(x-y) for x, y in zip(a, b)),
            'rms_pcm16_error': math.sqrt(error/len(a))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--cpu-only', action='store_true')
    args = p.parse_args()
    base = args.base
    record = {'kind': 'world_exp_silent_file_trial', 'runs': {}}
    manifest = json.loads((base/'deploy_manifest.json').read_text())
    for name, spec in manifest.items():
        assert hashlib.sha256((base/name).read_bytes()).hexdigest() == spec['sha256'], name
    old = Path('/opt/world_voice/world_budget_v23')
    record['v23_sha256'] = hashlib.sha256(old.read_bytes()).hexdigest()
    assert record['v23_sha256'] == 'f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7'
    record['binary_sha256'] = manifest['world_exp_arm']['sha256']
    modes = ['v23', 'cpu', 'model'] + ([] if args.cpu_only else ['pl'])
    for mode in modes:
        exe = old if mode == 'v23' else base/'world_exp_arm'
        env = os.environ.copy()
        env['WORLD_EXP'] = 'cpu' if mode == 'v23' else mode
        with (base/'input.raw').open('rb') as src, (base/(mode+'.raw')).open('wb') as dst:
            r = subprocess.run([str(exe), '5', 'pcm16', '0', '39322'], stdin=src, stdout=dst,
                               stderr=subprocess.PIPE, env=env, timeout=45)
        (base/(mode+'.log')).write_bytes(r.stderr)
        record['runs'][mode] = {'exit': r.returncode,
            'logs': [json.loads(line) for line in r.stderr.decode().splitlines() if line.startswith('{')],
            'output_sha256': hashlib.sha256((base/(mode+'.raw')).read_bytes()).hexdigest()}
        print(json.dumps({mode:record['runs'][mode]}), flush=True)
        assert r.returncode == 0, '%s failed' % mode
    pairs = [('v23','cpu'), ('cpu','model')] + ([] if args.cpu_only else [('model','pl'),('cpu','pl')])
    record['comparisons'] = {a+'_vs_'+b:compare(base/(a+'.raw'),base/(b+'.raw')) for a,b in pairs}
    record['passed'] = all(q['snr_db'] >= 50 and q['max_pcm16_error'] <= 8 for q in record['comparisons'].values())
    if not args.cpu_only:
        record['passed'] &= record['comparisons']['model_vs_pl']['exact']
        pl_stats = record['runs']['pl']['logs'][-1]
        record['passed'] &= pl_stats['mode'] == 2 and pl_stats['calls'] > 0 and pl_stats['fallback'] == 0
    name = 'cpu_file_result.json' if args.cpu_only else 'pl_file_result.json'
    (base/name).write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record['comparisons']), flush=True)
    if not record['passed']:
        raise SystemExit('File regression failed')


if __name__ == '__main__':
    main()
