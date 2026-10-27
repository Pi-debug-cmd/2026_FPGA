"""Silent profiling-on/off regression of the temporary FFT DMA module."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--base', type=Path, required=True)
args = p.parse_args()
base = args.base
module = base/'world_fft_dma_profile_round12.ko'
binary = base/'adapter_round11'
output = base/'kernel_round12_result.json'
assert not output.exists(), 'Preserve existing evidence'
result = {'module_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
          'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
          'runs': [], 'probes': []}
stats_path = Path('/sys/module/world_fft_dma/parameters/stats')
try:
    for repeat in range(3):
        for profile in ([0, 1] if repeat % 2 == 0 else [1, 0]):
            subprocess.run(['rmmod', 'world_fft_dma'], check=True)
            subprocess.run(['insmod', str(module), 'profile='+str(profile)], check=True)
            if repeat == 0:
                probe = subprocess.run([str(base/'world_fft_dma_probe')], check=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                result['probes'].append(dict(profile=profile,
                                            stdout=probe.stdout.decode(), stderr=probe.stderr.decode()))
            for clip in ['male1', 'male4']:
                before = json.loads(stats_path.read_text())
                start = time.monotonic()
                run = subprocess.run([str(binary), '5', 'pcm16', '0', '39322'],
                                     input=(base/(clip+'.raw')).read_bytes(),
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
                                     env=dict(os.environ, WORLD_EXP='pl', WORLD_FFT='pl2048', WORLD_FFT_CACHE='1'))
                wall = time.monotonic()-start
                after = json.loads(stats_path.read_text())
                assert run.returncode == 0, run.stderr.decode(errors='replace')
                assert run.stdout == (base/(clip+'_combined.raw')).read_bytes(), 'PCM changed'
                result['runs'].append(dict(repeat=repeat, profile=profile, clip=clip, wall_s=wall,
                                          stages={k: after[k]-before[k] for k in after},
                                          output_sha256=hashlib.sha256(run.stdout).hexdigest(),
                                          telemetry=[json.loads(s) for s in run.stderr.decode().splitlines()
                                                     if s.startswith('{')]))
                output.write_text(json.dumps(result, indent=2)+'\n')
                print(repeat, profile, clip, wall, result['runs'][-1]['stages'], flush=True)
    result['passed'] = True
finally:
    subprocess.run(['rmmod', 'world_fft_dma'], check=True)
    subprocess.run(['insmod', str(module), 'profile=0'], check=True)
output.write_text(json.dumps(result, indent=2)+'\n')
