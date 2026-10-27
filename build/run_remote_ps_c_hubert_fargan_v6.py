import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

root = Path.cwd()
out = root / 'build/generated/remote_ps_c_hubert_fargan_v6'
if len(sys.argv) == 1:
    assert not out.exists(), 'Preserve existing round outputs'
    attempts = []
    for stage in ('infer', 'evaluate'):
        started = time.monotonic()
        log = root / f'build/generated/remote_ps_c_v6_{stage}.log'
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run([sys.executable, __file__, stage], stdout=stream, stderr=subprocess.STDOUT)
        attempts.append({'stage': stage, 'exit_code': result.returncode, 'wall_seconds': time.monotonic() - started,
                         'log': log.relative_to(root).as_posix()})
        (root / 'build/generated/remote_ps_c_v6_execution.json').write_text(json.dumps(attempts, indent=2) + '\n')
        print(json.dumps(attempts[-1]), flush=True)
        if result.returncode:
            sys.exit(result.returncode)
    sys.exit(0)

stage = sys.argv[1]
denied = []
def guard(event, args):
    if event != 'open' or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    path = os.fsdecode(args[0]).replace('\\', '/').casefold()
    forbidden = path.endswith('/track 9.wav') or path.endswith('/标准录音 5.wav')
    if stage == 'infer':
        forbidden |= '/人物音频资料/' in path and path.endswith('.wav') and not path.endswith('/标准录音 4.wav')
    if forbidden:
        denied.append(path)
        raise PermissionError('Audio outside this stage allowlist')
sys.addaudithook(guard)
sys.path.insert(0, str(root / 'build'))
if stage == 'infer':
    script = 'build/remote_ps_c_hubert_fargan_v6.py'
    sys.argv = [script, 'infer']
else:
    script = 'build/evaluate_seed_fixed_male_strict_20261024.py'
    sys.argv = [script, '--asset-root', '.', '--portable-assets', 'build/generated/remote_ps_c_assets',
                '--manifest', str(out / 'evaluation_manifest.json'), '--output', str(out / 'evaluation.json')]
runpy.run_path(script, run_name='__main__')
assert not denied
print('PYTHON_AUDIO_GUARD', json.dumps({'stage': stage, 'denied': denied}), flush=True)
