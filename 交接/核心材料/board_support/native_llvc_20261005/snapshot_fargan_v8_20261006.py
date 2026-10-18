import json, os, time, hashlib
from pathlib import Path

ROOT = Path('/home/root/native_llvc_trial_20261005')
RUN = Path('/run/voice-neural-live')
result = dict(snapshot_monotonic=time.monotonic(), board_wall_time=time.time(),
              project_completed=False, quality_accepted=False,
              acoustic_latency_measured=False, inference_location='7020 PS CPU0/CPU1',
              pl_acceleration_implemented=False)
result['processes'] = {}
for role in ('capture', 'convert', 'playback', 'watchdog'):
    try:
        pid = int((RUN / (role + '.pid')).read_text())
        cmd = Path('/proc/%d/cmdline' % pid).read_bytes().replace(b'\0', b' ').decode()
        result['processes'][role] = dict(pid=pid, cmdline=cmd)
    except (OSError, ValueError) as exc:
        result['processes'][role] = dict(error=str(exc))
try:
    result['status'] = json.loads((RUN / 'status.json').read_text())
except (OSError, ValueError) as exc:
    result['status_error'] = str(exc)
result['logs'] = {}
for name in ('capture.log', 'convert.log', 'playback.log', 'watchdog.log', 'affinity.log'):
    try:
        result['logs'][name] = (RUN / name).read_text()[-8192:]
    except OSError:
        pass
try:
    t = Path('/sys/bus/iio/devices/iio:device0')
    result['temperature_c'] = (float((t/'in_temp0_raw').read_text()) + float((t/'in_temp0_offset').read_text())) * float((t/'in_temp0_scale').read_text()) / 1000
except OSError:
    pass
for name in ('native_fargan_v8_arm', 'fargan_mapper_v8_selected.f32', 'board_neural_fargan.sh', 'fargan_live_watchdog.py', 'audio_affinity.py'):
    result.setdefault('sha256', {})[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
cmd = result['processes']['convert'].get('cmdline', '')
result['v8_live_deployed'] = 'native_fargan_v8_arm ' in cmd
result['live_verified_short_observation'] = (result['v8_live_deployed'] and
    result.get('status', {}).get('frames', 0) >= 6000 and
    not any(result['logs'].get(k, '').strip() for k in ('capture.log','convert.log','playback.log','watchdog.log')))
(ROOT / 'fargan_v8_live_evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False))
