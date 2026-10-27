"""Silent, manifest-verified first FFT/exp integration regression; no ALSA."""
import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--base', type=Path, required=True)
base = p.parse_args().base
manifest = json.loads((base/'fft_manifest.json').read_text())
for name, spec in manifest.items():
    assert hashlib.sha256((base/name).read_bytes()).hexdigest() == spec['sha256'], name
assert Path('/sys/class/fpga_manager/fpga0/state').read_text().strip() == 'operating'
assert Path('/dev/world_fft').exists() and Path('/dev/world_exp').exists()
baseline = Path('/opt/world_voice/world_budget_v23')
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == 'f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7'
probe = subprocess.run([str(base/'world_fft_dma_probe')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
(base/'probe.log').write_bytes(probe.stdout+probe.stderr)
assert probe.returncode == 0, probe.stderr.decode(errors='replace')
result = {'kind':'world_fft_pl_first_trial','manifest':manifest,
          'probe':[json.loads(s) for s in probe.stdout.decode().splitlines() if s.startswith('{')], 'runs':[]}
cases = [('baseline','cpu','cpu'),('cpu','cpu','cpu'),('fft2048','cpu','pl2048'),
         ('fft1024','cpu','pl1024'),('fft_all','cpu','pl'),('exp_only','pl','cpu'),('combined','pl','pl2048')]
for clip in ['male1','male4']:
    expected = None
    for name, exp, fft in cases:
        exe = baseline if name == 'baseline' else base/'world_exp_arm_cache_fftpl'
        env = dict(os.environ,WORLD_EXP=exp,WORLD_FFT=fft,WORLD_FFT_CACHE='1')
        with (base/(clip+'.raw')).open('rb') as src:
            r = subprocess.run([str(exe),'5','pcm16','0','39322'],stdin=src,stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,env=env,timeout=45)
        stem = clip+'_'+name
        (base/(stem+'.raw')).write_bytes(r.stdout)
        (base/(stem+'.log')).write_bytes(r.stderr)
        assert r.returncode == 0, (stem,r.stderr.decode(errors='replace'))
        assert len(r.stdout) == 160000
        y = array.array('h',r.stdout)
        if expected is None:
            expected = y
        error = sum((a-b)**2 for a,b in zip(expected,y))
        energy = sum(a*a for a in expected)
        snr = 10*math.log10(energy/max(error,1e-30))
        peak = max(abs(a-b) for a,b in zip(expected,y))
        log = [json.loads(s) for s in r.stderr.decode().splitlines() if s.startswith('{')]
        assert snr >= 75 and peak <= 8, (stem,snr,peak)
        if name == 'cpu':
            assert y == expected, 'CPU FFT wrapper changed v23 output'
        if fft != 'cpu':
            assert next(t for t in log if t.get('kind')=='world_fft_pl')['calls'] > 0
        if exp != 'cpu':
            backend = next(t for t in log if t.get('kind')=='world_exp_backend')
            assert backend['calls'] > 0 and backend['fallback'] == 0
        result['runs'].append(dict(clip=clip,mode=name,snr_db=snr,max_pcm16_error=peak,
                                  output_sha256=hashlib.sha256(r.stdout).hexdigest(),telemetry=log))
        (base/'fft_result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(stem+' snr='+str(snr)+' max='+str(peak),flush=True)
result['passed'] = True
(base/'fft_result.json').write_text(json.dumps(result,indent=2)+'\n')
print('FFT_PL_FILE_PASS',flush=True)
