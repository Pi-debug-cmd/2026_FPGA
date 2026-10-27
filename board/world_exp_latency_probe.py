"""Paced file-pipe latency diagnostic. No ALSA, microphone, or speaker use.

Measures PS pipeline delivery lag by source/output sample position, including
the algorithm's frame lookahead. This excludes ALSA/codec/acoustic latency and
must never be reported as physical end-to-end latency.
"""
import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
import subprocess
import threading
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--backend', choices=['v23', 'pl'], required=True)
    p.add_argument('--binary', type=Path)
    p.add_argument('--fft-mode', choices=['cpu','pl2048','pl1024','pl'], default='cpu')
    p.add_argument('--label', help='Unique result label when comparing candidate modes')
    args = p.parse_args()
    base = args.base
    data = (base/'input.raw').read_bytes()
    assert len(data) == 5*16000*2
    binary = args.binary or (Path('/opt/world_voice/world_budget_v23') if args.backend == 'v23' else base/'world_exp_arm')
    label = args.label or args.backend
    assert re.fullmatch('[a-zA-Z0-9_-]+',label)
    env = os.environ.copy()
    env['WORLD_EXP'] = 'pl' if args.backend == 'pl' else 'cpu'
    env['WORLD_FFT'] = args.fft_mode
    feed, arrivals, lateness, errors = [], [], [], []
    with (base/('latency_'+label+'.log')).open('wb') as log:
        child = subprocess.Popen([str(binary),'5','pcm16','0','39322'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=env, bufsize=0)
        start = time.monotonic()+0.1

        def writer():
            try:
                for offset in range(0,len(data),256):
                    chunk = data[offset:offset+256]
                    target = start+(offset+len(chunk))/32000.0
                    delay = target-time.monotonic()
                    if delay > 0:
                        time.sleep(delay)
                    stamp = time.monotonic()
                    feed.append(stamp)
                    lateness.append((stamp-target)*1000)
                    assert child.stdin.write(chunk) == len(chunk)
            except Exception as exc:
                errors.append(repr(exc))
            finally:
                child.stdin.close()

        worker = threading.Thread(target=writer)
        worker.start()
        count = 0
        while count < len(data):
            chunk = b''
            needed = min(256,len(data)-count)
            while len(chunk) < needed:
                part = child.stdout.read(needed-len(chunk))
                if not part:
                    raise RuntimeError('Premature output EOF')
                chunk += part
            arrivals.append(time.monotonic())
            count += len(chunk)
        worker.join(timeout=10)
        assert not worker.is_alive() and not errors, errors
        child.stdout.close()
        rc = child.wait(timeout=15)
        assert rc == 0, rc
    assert len(feed) == len(arrivals)
    lag = [(b-a)*1000 for a,b in zip(feed,arrivals)]
    # Ignore first/last 0.5 seconds for steady-state aggregate; retain every row.
    steady = sorted(lag[63:-63])
    record = {'kind':'world_exp_paced_file_delivery_lag','backend':args.backend,
        'label':label,'fft_mode':args.fft_mode,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'input_sha256':hashlib.sha256(data).hexdigest(),
        'physical_end_to_end':False,'excludes':['ALSA','codec','analog','acoustic propagation'],
        'method':'128-sample 16k blocks paced at 8ms; output arrival minus actual matching input block delivery',
        'prefill_ms':0,'blocks':len(lag),'steady_p50_ms':steady[len(steady)//2],
        'steady_p95_ms':steady[math.ceil(.95*len(steady))-1],'steady_max_ms':max(steady),
        'max_feeder_lateness_ms':max(lateness),'lag_ms':lag,'feeder_lateness_ms':lateness,
        'telemetry':[json.loads(x) for x in (base/('latency_'+label+'.log')).read_text().splitlines() if x.startswith('{')]}
    (base/('latency_'+label+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if not isinstance(v,list)}),flush=True)


if __name__ == '__main__':
    main()
