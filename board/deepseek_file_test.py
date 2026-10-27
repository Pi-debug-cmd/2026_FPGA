"""On-board Deepseek file test; no ALSA capture or playback."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time

ROOT = Path('/tmp/codex_deepseek_ds01')


def run(name, exe, extra):
    command = [str(ROOT / exe), '4', 'native_s24', '200', '--model', str(ROOT / 'model.blob'), '--in-f32-16k', '--out-f32-16k', '--preset', 'live', *extra]
    before = time.monotonic()
    with (ROOT / 'input.f32').open('rb') as inp, (ROOT / (name + '.f32')).open('wb') as out, (ROOT / (name + '.log')).open('wb') as log:
        p = subprocess.run(command, stdin=inp, stdout=out, stderr=log, env={**os.environ, 'VC_PL': '0'}, timeout=60)
    return {'command': command, 'exit': p.returncode, 'wall_s': time.monotonic() - before, 'bytes': (ROOT / (name + '.f32')).stat().st_size, 'telemetry': (ROOT / (name + '.log')).read_text()}


def main():
    report = {'kind': 'file_conversion_only', 'pl_enabled': False, 'runs': {}}
    for exe in ('vc_o64_pl', 'vc_s24fix_arm'):
        (ROOT / exe).chmod(0o755)
        report['runs'][exe] = run(exe, exe, [])
    report['hashes'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ('model.blob', 'vc_o64_pl', 'vc_s24fix_arm', 'input.f32')}
    report['output_peaks'] = {}
    for name in report['runs']:
        data = (ROOT / (name + '.f32')).read_bytes()
        vals = list(struct.unpack('<%df' % (len(data) // 4), data))
        report['output_peaks'][name] = max(map(abs, vals)) if vals else None
    (ROOT / 'file_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
