"""Silent v23 CPU/minphase/exp/combined file regression; never opens ALSA."""
import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

BASE = Path('/tmp/codex_world_minphase_20261029')
MANIFEST = json.loads((BASE / 'file_manifest.json').read_text())
for name, spec in MANIFEST.items():
    path = BASE / name
    assert path.stat().st_size == spec['bytes'], name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == spec['sha256'], name
assert Path('/sys/class/fpga_manager/fpga0/state').read_text().strip() == 'operating'
assert Path('/dev/world_minphase').exists() and Path('/dev/world_exp').exists()

baseline = Path('/opt/world_voice/world_budget_v23')
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == \
    'f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7'


def stats(module):
    path = Path('/sys/module') / module / 'parameters/stats'
    return json.loads(path.read_text()) if path.exists() else None


before = {'minphase': stats('world_minphase_dma'), 'exp': stats('world_exp_dma')}
result = {'kind': 'world_minphase_pl_file_trial', 'manifest': MANIFEST,
          'before': before, 'runs': []}
cases = [('baseline', baseline, 'cpu', 'cpu'),
         ('cpu', BASE / 'world_exp_arm_minphasepl', 'cpu', 'cpu'),
         ('minphase', BASE / 'world_exp_arm_minphasepl', 'pl', 'cpu'),
         ('exp', BASE / 'world_exp_arm_minphasepl', 'cpu', 'pl'),
         ('combined', BASE / 'world_exp_arm_minphasepl', 'pl', 'pl')]

for clip in ('male1', 'male4'):
    expected = None
    minphase_output = None
    for mode, executable, minphase, exp in cases:
        environment = dict(os.environ, WORLD_MINPHASE=minphase, WORLD_EXP=exp)
        started = time.monotonic()
        with (BASE / (clip + '.raw')).open('rb') as source:
            run = subprocess.run([str(executable), '5', 'pcm16', '0', '39322'],
                                 stdin=source, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=environment, timeout=45)
        elapsed = time.monotonic() - started
        stem = clip + '_' + mode
        (BASE / (stem + '.raw')).write_bytes(run.stdout)
        (BASE / (stem + '.log')).write_bytes(run.stderr)
        assert run.returncode == 0, (stem, run.stderr.decode(errors='replace'))
        assert len(run.stdout) == 160000, (stem, len(run.stdout))
        output = array.array('h', run.stdout)
        if expected is None:
            expected = output
        error = sum((a - b) ** 2 for a, b in zip(expected, output))
        energy = sum(a * a for a in expected)
        snr = 10 * math.log10(energy / max(error, 1e-30))
        peak = max(abs(a - b) for a, b in zip(expected, output))
        telemetry = [json.loads(line) for line in run.stderr.decode().splitlines()
                     if line.startswith('{')]
        assert snr >= 75 and peak <= 8, (stem, snr, peak)
        if mode == 'cpu':
            assert output == expected, 'CPU-selectable binary changed v23 output'
        if minphase == 'pl':
            item = next(row for row in telemetry
                        if row.get('kind') == 'world_minphase_pl')
            assert item['calls'] > 0 and item['fallback'] == 0
            if mode == 'minphase':
                minphase_output = output
        if exp == 'pl':
            item = next(row for row in telemetry
                        if row.get('kind') == 'world_exp_backend')
            assert item['fallback'] == 0
            if minphase == 'cpu':
                assert item['calls'] > 0
            else:
                # The fused minimum-phase kernel already includes exp/cos/sin.
                assert item['calls'] == 0 and output == minphase_output
        record = {'clip': clip, 'mode': mode, 'elapsed_s': elapsed,
                  'snr_db': snr, 'max_pcm16_error': peak,
                  'output_sha256': hashlib.sha256(run.stdout).hexdigest(),
                  'telemetry': telemetry}
        result['runs'].append(record)
        (BASE / 'file_result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('%s elapsed=%.6f snr=%.6f max=%d' %
              (stem, elapsed, snr, peak), flush=True)

after = {'minphase': stats('world_minphase_dma'), 'exp': stats('world_exp_dma')}
result['after'] = after
result['minphase_driver_calls_delta'] = after['minphase']['calls'] - before['minphase']['calls']
result['exp_driver_calls_delta'] = (after['exp']['calls'] - before['exp']['calls']
                                    if before['exp'] is not None else None)
assert result['minphase_driver_calls_delta'] > 0
result['passed'] = True
(BASE / 'file_result.json').write_text(json.dumps(result, indent=2) + '\n')
print('WORLD_MINPHASE_PL_FILE_PASS', flush=True)
