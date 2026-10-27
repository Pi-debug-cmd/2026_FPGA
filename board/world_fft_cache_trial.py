"""Silent, interleaved baseline/cache regression on controlled PCM16 files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--base', type=Path, required=True)
base = p.parse_args().base
manifest = json.loads((base/'cache_manifest.json').read_text())
for name, spec in manifest.items():
    assert hashlib.sha256((base/name).read_bytes()).hexdigest() == spec['sha256'], name
baseline = Path('/opt/world_voice/world_budget_v23')
baseline_sha = hashlib.sha256(baseline.read_bytes()).hexdigest()
assert baseline_sha == 'f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7'
result = {'kind':'world_fft_cache_trial', 'baseline_sha256':baseline_sha,
          'manifest':manifest, 'runs':[], 'output_exact':True}
for clip in ['male1', 'male4']:
    expected = None
    for iteration in range(3):
        for mode in ['baseline', 'cache_off', 'cache_on']:
            exe = baseline if mode == 'baseline' else base/'world_exp_arm_cache'
            env = dict(os.environ, WORLD_EXP='cpu', WORLD_FFT_CACHE='1' if mode == 'cache_on' else '0')
            with (base/(clip+'.raw')).open('rb') as src:
                r = subprocess.run([str(exe),'5','pcm16','0','39322'],stdin=src,
                                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=45)
            stem = clip+'_'+mode+'_'+str(iteration)
            (base/(stem+'.log')).write_bytes(r.stderr)
            assert r.returncode == 0, (stem, r.stderr.decode(errors='replace'))
            assert len(r.stdout) == 160000
            if expected is None:
                expected = r.stdout
            assert r.stdout == expected, stem+' changed v23 output'
            telemetry = [json.loads(s) for s in r.stderr.decode().splitlines() if s.startswith('{')]
            result['runs'].append({'clip':clip,'iteration':iteration,'mode':mode,
                                   'output_sha256':hashlib.sha256(r.stdout).hexdigest(),'telemetry':telemetry})
            print(stem+' exact',flush=True)
(base/'cache_result.json').write_text(json.dumps(result,indent=2)+'\n')
print('CACHE_REGRESSION_PASS',flush=True)
