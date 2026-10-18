"""Finite playback of a checked offline comparison, restoring mixer afterwards."""
import gzip
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', default='/tmp/codex_pl_control_20261011')
parser.add_argument('--manifest', default='comparison_manifest.json')
parser.add_argument('--audio', default='voice_comparison.wav.gz')
args = parser.parse_args()
if not re.fullmatch(r'/tmp/codex_[a-zA-Z0-9_]+', args.base):
    raise ValueError('Use a project staging directory directly under /tmp')
base = Path(args.base)
for name in [args.manifest, args.audio]:
    if Path(name).name != name:
        raise ValueError('Use a filename within the staging directory')
record = json.loads((base / args.manifest).read_text())
packed = (base / args.audio).read_bytes()
assert hashlib.sha256(packed).hexdigest() == record['gzip_sha256']
raw = gzip.decompress(packed)
assert hashlib.sha256(raw).hexdigest() == record['wav_sha256']
for name in ['pcm1c', 'pcm0p']:
    assert Path('/proc/asound/card0', name, 'sub0/status').read_text().strip() == 'closed'
run = base / f'comparison_{time.monotonic_ns()}'
run.mkdir()
audio = run / 'comparison.wav'
audio.write_bytes(raw)
state = run / 'mixer_before.state'
subprocess.run(['alsactl', '-f', str(state), 'store', '0'], check=True)
try:
    for name, value in [('Headphone Playback ZC', 'on'), ('Left Output Mixer PCM', 'on'),
                        ('Right Output Mixer PCM', 'on'), ('Headphone', '105,105'),
                        ('Playback', '230,230')]:
        subprocess.run(['amixer', 'sset', name, value], stdout=subprocess.DEVNULL, check=True)
    print('COMPARISON_START', record['order'], flush=True)
    with (run / 'playback.log').open('wb') as log:
        subprocess.run(['aplay', '-v', '-D', 'default', str(audio)],
                       stdout=log, stderr=subprocess.STDOUT, check=True,
                       timeout=record['duration_s'] + 10)
    print('COMPARISON_COMPLETED', str(run), flush=True)
finally:
    subprocess.run(['alsactl', '-f', str(state), 'restore', '0'], check=True)
