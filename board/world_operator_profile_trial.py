"""Silent v23 operator profile with exact-output and binary manifest checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--base', type=Path, required=True)
args = p.parse_args()
base = args.base
manifest = json.loads((base/'profile_manifest.json').read_text())
for name, spec in manifest.items():
    assert hashlib.sha256((base/name).read_bytes()).hexdigest() == spec['sha256']
old = Path('/opt/world_voice/world_budget_v23')
old_sha = hashlib.sha256(old.read_bytes()).hexdigest()
assert old_sha == 'f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7'
result = {'kind':'world_arm_operator_profile','baseline_sha256':old_sha,
          'manifest':manifest,'stages':{'0':'render/other','1':'dio','2':'refine','3':'spectrum','4':'aperiodic'},
          'types':{'0':'r2c','1':'c2r','2':'c2c'},'ops':{'0':'plan','1':'execute'},'runs':[]}
env = os.environ.copy()
env['WORLD_EXP'] = 'cpu'
expected = None
for name in ['baseline','profile1','profile2','profile3']:
    exe = old if name == 'baseline' else base/'world_exp_arm_profile'
    with (base/'input.raw').open('rb') as src, (base/(name+'.raw')).open('wb') as dst:
        r = subprocess.run([str(exe),'5','pcm16','0','39322'],stdin=src,stdout=dst,
                           stderr=subprocess.PIPE,env=env,timeout=45)
    (base/(name+'.log')).write_bytes(r.stderr)
    assert r.returncode == 0, r.stderr.decode(errors='replace')
    output = (base/(name+'.raw')).read_bytes()
    if expected is None:
        expected = output
    assert output == expected, 'Diagnostic changed output: '+name
    log = [json.loads(s) for s in r.stderr.decode().splitlines() if s.startswith('{')]
    result['runs'].append({'name':name,'exit':r.returncode,'output_sha256':hashlib.sha256(output).hexdigest(),'telemetry':log})
result['output_exact'] = True
sample = result['runs'][1]['telemetry']
rows = []
for row in sample:
    if row.get('kind') != 'world_fft_profile':
        continue
    key = tuple(row[k] for k in ['stage','size','type','op'])
    times = []
    for run in result['runs'][1:]:
        matched = next(x for x in run['telemetry'] if x.get('kind') == 'world_fft_profile' and
                       tuple(x[k] for k in ['stage','size','type','op']) == key)
        assert matched['calls'] == row['calls']
        times.append(matched['seconds'])
    rows.append(dict(row,seconds_median=sorted(times)[1],samples_seconds=times))
result['fft_summary'] = rows
result['fft_plan_seconds_median_sum'] = sum(r['seconds_median'] for r in rows if r['op'] == 0)
result['fft_execute_seconds_median_sum'] = sum(r['seconds_median'] for r in rows if r['op'] == 1)
(base/'profile_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))}),flush=True)
