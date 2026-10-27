"""Silent CPU vs integer-model regression using controlled repository WAVs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import wave
import numpy as np
from scipy.signal import resample_poly
from math import gcd


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--exe', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seconds', type=int, default=5)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with wave.open(str(args.source), 'rb') as f:
        sr, ch, width = f.getframerate(), f.getnchannels(), f.getsampwidth()
        raw = f.readframes(sr*args.seconds)
    if width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        q = b[:, 0] | b[:, 1] << 8 | b[:, 2] << 16
        x = ((q ^ 0x800000)-0x800000).astype(float)/8388608
    elif width == 2:
        x = np.frombuffer(raw, dtype='<i2').astype(float)/32768
    else:
        raise ValueError('Require PCM16/24')
    x = x.reshape(-1, ch).mean(axis=1)
    g = gcd(sr, 16000)
    x = resample_poly(x, 16000//g, sr//g)[:args.seconds*16000]
    assert len(x) == args.seconds*16000
    pcm = np.clip(np.rint(x*32768), -32768, 32767).astype('<i2').tobytes()
    (args.out/'input.raw').write_bytes(pcm)
    result = {'source': str(args.source), 'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'input_sha256': hashlib.sha256(pcm).hexdigest(), 'rate': sr, 'channels': ch, 'sample_width': width,
              'preprocessing': 'first N seconds, channel mean, scipy resample_poly to 16k, round/clip PCM16',
              'seconds': args.seconds, 'exe_sha256': hashlib.sha256(args.exe.read_bytes()).hexdigest(), 'runs': {}}
    waves = {}
    for mode in ('cpu', 'model'):
        env = os.environ.copy()
        env['WORLD_EXP'] = mode
        r = subprocess.run([str(args.exe.resolve()), str(args.seconds), 'pcm16', '0', '39322'],
                           input=pcm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=90)
        (args.out/(mode+'.raw')).write_bytes(r.stdout)
        (args.out/(mode+'.log')).write_bytes(r.stderr)
        assert r.returncode == 0, r.stderr.decode(errors='replace')
        waves[mode] = np.frombuffer(r.stdout, dtype='<i2').astype(float)
        result['runs'][mode] = {'exit': r.returncode, 'sha256': hashlib.sha256(r.stdout).hexdigest(),
                               'logs': [json.loads(line) for line in r.stderr.decode().splitlines() if line.startswith('{')]}
    a, b = waves['cpu'], waves['model']
    assert len(a) == len(b) == args.seconds*16000
    error = np.dot(a-b, a-b)
    result['comparison'] = {'snr_db': float(10*np.log10(np.dot(a,a)/max(1,error))),
                            'max_pcm16_error': float(abs(a-b).max()), 'rms_pcm16_error': float(np.sqrt(np.mean((a-b)**2)))}
    result['passed'] = result['comparison']['snr_db'] >= 50 and result['comparison']['max_pcm16_error'] <= 8
    (args.out/'quality.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result['comparison']))
    if not result['passed']:
        raise SystemExit('Numerical regression failed; do not request listening')


if __name__ == '__main__':
    main()
