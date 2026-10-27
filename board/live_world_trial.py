"""Finite WM8960/WORLD trial; --check is read-only, --run opens audio."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

BASE = Path('/tmp/codex_world_20261013')


def pcm_idle():
    states = {node: Path('/proc/asound/card0/' + node + '/sub0/status').read_text().strip()
              for node in ['pcm0p', 'pcm1c']}
    if any(value != 'closed' for value in states.values()):
        raise RuntimeError('AUDIO_BUSY: ' + json.dumps(states))
    return states


def preflight(base):
    for command in ['arecord', 'aplay', 'amixer', 'alsactl']:
        if not shutil.which(command):
            raise RuntimeError('Missing command: ' + command)
    manifest = json.loads((base / 'world_live_manifest_v21.json').read_text())
    binary_name = manifest.get('binary_name', 'world_budget_v12')
    if not re.fullmatch(r'world_budget_v[0-9]+', binary_name):
        raise RuntimeError('Invalid runtime name')
    binary = base / binary_name
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    if manifest['binary_sha256'] != actual or not os.access(binary, os.X_OK):
        raise RuntimeError('Runtime binary is missing, not executable, or has wrong SHA')
    record = {'kind': 'world_live_preflight', 'binary_sha256': actual, 'pcm': pcm_idle(),
              'cpu_online': Path('/sys/devices/system/cpu/online').read_text().strip()}
    print(json.dumps(record), flush=True)
    return binary


def codec_snapshot(run, label):
    """Best-effort read-only diagnostics; never write codec registers."""
    paths = [Path('/sys/kernel/debug/regmap/0-001a/registers'),
             Path('/sys/kernel/debug/clk/clk_summary')]
    dapm = Path('/sys/kernel/debug/asoc/xlnx-i2s-snd-card-0/wm8960.0-001a/dapm')
    paths.extend(dapm / name for name in ['MICB', 'Left ADC', 'Right ADC',
                 'Left Input Mixer', 'Right Input Mixer', 'Left DAC', 'Right DAC',
                 'LOUT1 PGA', 'ROUT1 PGA', 'HP_L', 'HP_R'])
    snapshot = {}
    for path in paths:
        try:
            snapshot[str(path)] = path.read_text()
        except OSError as exc:
            snapshot[str(path)] = {'read_error': str(exc)}
    (run / ('codec_' + label + '.json')).write_text(json.dumps(snapshot, indent=2) + '\n')


def run_trial(base, seconds, prefill, gain=49152, input_gain=262144, fifo=False, fifo_io=False, require_voiced=False,
              period=512, capture_buffer=4096, playback_buffer=3072, start_delay=32000):
    binary = preflight(base)
    run = base / ('live_' + str(time.monotonic_ns()))
    run.mkdir()  # Unique run directory also owns logs and mixer snapshot.
    processes, logs = [], []
    mixer_saved = False
    record = {'kind': 'world_live_trial', 'directory': str(run), 'seconds': seconds,
              'prefill_ms': prefill, 'output_gain_q16': gain, 'input_gain_q16': input_gain,
              'requested_fifo': fifo, 'requested_fifo_io': fifo_io, 'require_voiced': require_voiced, 'exit_code': 1,
              'world_exp_requested': os.environ.get('WORLD_EXP', 'cpu'), 'alsa_period': period,
              'capture_buffer': capture_buffer, 'playback_buffer': playback_buffer, 'start_delay_us': start_delay}
    error = None
    try:
        with (run / 'mixer_store.log').open('wb') as log:
            subprocess.run(['alsactl', '-f', str(run / 'mixer_before.state'), 'store', '0'],
                           stdout=log, stderr=log, check=True, timeout=10)
        mixer_saved = True
        codec_snapshot(run, 'before')
        controls = [
            ['sset', 'Left Input Mixer Boost', 'on'],
            ['sset', 'Right Boost Mixer RINPUT1', 'on'],
            ['sset', 'Right Input Mixer Boost', 'on'],
            ['cset', "name=ADC Data Output Select", '1'],
            ['sset', 'Left Output Mixer PCM', 'on'],
            ['sset', 'Right Output Mixer PCM', 'on'],
            ['sset', 'Headphone Playback ZC', 'on'],
            ['sset', 'Headphone', '105,105'],
            ['sset', 'Playback', '230,230'],
            ['sset', 'Left Boost Mixer LINPUT1', 'on'],
            ['sset', 'Left Input Boost Mixer LINPUT1', '0'],
            ['sset', 'Capture', '31,31', 'cap'],
        ]
        with (run / 'mixer_setup.log').open('wb') as log:
            for control in controls:
                subprocess.run(['amixer'] + control, stdout=log, stderr=log, check=True, timeout=5)
        codec_snapshot(run, 'configured')
        for name in ['capture', 'process', 'playback']:
            logs.append((run / (name + '.log')).open('wb'))
        capture = subprocess.Popen(['arecord', '-v', '-D', 'hw:0,1', '-t', 'raw', '-f', 'S24_LE',
            '-r', '32000', '-c', '2', '--period-size='+str(period), '--buffer-size='+str(capture_buffer), '-d', str(seconds), '-'],
            stdout=subprocess.PIPE, stderr=logs[0])
        processes.append(capture)
        runtime_args = [str(binary), str(seconds), 'native_s24', str(prefill), str(gain), str(input_gain)]
        if fifo:
            runtime_args.append('fifo')
        elif fifo_io:
            runtime_args.append('fifo_io')
        process = subprocess.Popen(runtime_args,
            stdin=capture.stdout, stdout=subprocess.PIPE, stderr=logs[1])
        processes.append(process)
        capture.stdout.close()
        playback = subprocess.Popen(['aplay', '-v', '-D', 'default', '-t', 'raw', '-f', 'S24_LE',
            '-r', '32000', '-c', '2', '--period-size='+str(period), '--buffer-size='+str(playback_buffer), '--start-delay='+str(start_delay), '-'],
            stdin=process.stdout, stdout=logs[2], stderr=logs[2])
        processes.append(playback)
        process.stdout.close()
        print('WORLD_LIVE_STARTED seconds=%d prefill_ms=%d directory=%s' % (seconds, prefill, run), flush=True)
        started = time.monotonic()
        sampled_params = False
        while any(child.poll() is None for child in processes):
            for child in processes:
                # Clipping is reported after a complete runtime output; allow
                # aplay to drain its remaining audio before rejecting the trial.
                if child is process and child.poll() == 6:
                    continue
                if child.poll() not in (None, 0):
                    raise RuntimeError('Child failed: pid=%d exit=%s' % (child.pid, child.returncode))
            elapsed = time.monotonic() - started
            if elapsed > seconds + 15:
                raise RuntimeError('Trial watchdog expired')
            if elapsed >= 1 and not sampled_params:
                codec_snapshot(run, 'active')
                for node in ['pcm0p', 'pcm1c']:
                    (run / (node + '_hw_params.log')).write_text(
                        Path('/proc/asound/card0/' + node + '/sub0/hw_params').read_text())
                sampled_params = True
            time.sleep(.1)
        record['child_exits'] = [child.returncode for child in processes]
        if record['child_exits'] != [0, 0, 0]:
            raise RuntimeError('Nonzero child exit: ' + str(record['child_exits']))
        for log in logs:
            log.flush()
        capture_text = (run / 'capture.log').read_text(errors='replace')
        playback_text = (run / 'playback.log').read_text(errors='replace')
        record['capture_overruns'] = len(re.findall(r'overrun', capture_text, re.IGNORECASE))
        record['playback_underruns'] = len(re.findall(r'underrun', playback_text, re.IGNORECASE))
        record['alsa_errors'] = len(re.findall(r'(?:read|write) error|Input/output error',
                                              capture_text + playback_text, re.IGNORECASE))
        if record['capture_overruns'] or record['playback_underruns'] or record['alsa_errors']:
            raise RuntimeError('ALSA stream error/xrun')
        runtime_lines = (run / 'process.log').read_text().splitlines()
        telemetry = [json.loads(line) for line in runtime_lines if line.startswith('{')]
        runtime = next(item for item in telemetry if item.get('kind') == 'world_raw_stream_runtime')
        if os.environ.get('WORLD_EXP') == 'pl':
            stats = next(item for item in telemetry if item.get('kind') == 'world_exp_backend')
            record['world_exp_backend'] = stats
            if stats['mode'] != 2 or stats['calls'] <= 0 or stats['fallback']:
                raise RuntimeError('PL did not process all minimum-phase calls')
        if runtime['exit_code'] != 0:
            raise RuntimeError('Runtime check failed')
        if runtime.get('raw_capture_clipped_samples', 0):
            raise RuntimeError('Native capture has near-full-scale samples')
        if require_voiced and runtime.get('voiced_frames', 0) <= 0:
            raise RuntimeError('Speech trial contains no voiced frames')
        if fifo and (not runtime.get('scheduling_fifo') or
                     any(runtime.get(field, -1) for field in ['reader_sched_error', 'analysis_sched_error',
                                                             'render_sched_error', 'writer_sched_error'])):
            raise RuntimeError('Requested real-time scheduling not verified')
        if fifo_io and (not runtime.get('scheduling_fifo_io') or runtime.get('scheduling_fifo') or
                        any(runtime.get(field, -1) for field in ['reader_sched_error', 'analysis_sched_error',
                                                                'render_sched_error', 'writer_sched_error'])):
            raise RuntimeError('Requested I/O-only real-time scheduling not verified')
        record['runtime'] = runtime
        record['exit_code'] = 0
    except (Exception, KeyboardInterrupt) as exc:
        error = str(exc) or type(exc).__name__
        record['error'] = error
    finally:
        # Only handles launched by this supervisor are signaled. No global kill.
        for child in reversed(processes):
            if child.poll() is None:
                child.terminate()
        for child in reversed(processes):
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        for child in processes:
            if child.stdout is not None:
                child.stdout.close()
        for log in logs:
            log.close()
        # Always collect error counts and runtime telemetry, even after failure.
        for name, field, pattern in [('capture', 'capture_overruns', 'overrun'),
                                     ('playback', 'playback_underruns', 'underrun')]:
            path = run / (name + '.log')
            if path.exists():
                record[field] = len(re.findall(pattern, path.read_text(errors='replace'), re.IGNORECASE))
                if record[field]:
                    record['exit_code'] = 1
        path = run / 'process.log'
        if path.exists():
            try:
                telemetry = [json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')]
                record['runtime'] = next(item for item in telemetry if item.get('kind') == 'world_raw_stream_runtime')
                for item in telemetry:
                    if item.get('kind') == 'world_exp_backend':
                        record['world_exp_backend'] = item
            except (StopIteration, ValueError):
                record['runtime_log_incomplete'] = True
        record['child_exits'] = [child.returncode for child in processes]
        if mixer_saved:
            try:
                with (run / 'mixer_restore.log').open('wb') as log:
                    restored = subprocess.run(['alsactl', '-f', str(run / 'mixer_before.state'), 'restore', '0'],
                                              stdout=log, stderr=log, timeout=10)
                record['mixer_restore_exit'] = restored.returncode
                if restored.returncode:
                    record['exit_code'] = 1
            except Exception as exc:
                record['mixer_restore_error'] = str(exc)
                record['exit_code'] = 1
        try:
            record['pcm_after'] = pcm_idle()
        except Exception as exc:
            record['pcm_after_error'] = str(exc)
            record['exit_code'] = 1
        (run / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps(record), flush=True)
    return record['exit_code']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--run', action='store_true')
    parser.add_argument('--seconds', type=int, default=20)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--alsa-period', type=int, default=512)
    parser.add_argument('--capture-buffer', type=int, default=4096)
    parser.add_argument('--playback-buffer', type=int, default=3072)
    parser.add_argument('--start-delay-us', type=int, default=32000)
    parser.add_argument('--prefill-ms', type=int, default=200)
    parser.add_argument('--output-gain-q16', type=int, default=49152)
    parser.add_argument('--input-gain-q16', type=int, default=262144)
    scheduling = parser.add_mutually_exclusive_group()
    scheduling.add_argument('--fifo', action='store_true')
    scheduling.add_argument('--fifo-io', action='store_true')
    parser.add_argument('--require-voiced', action='store_true', help='Reject speech trials without detected voiced input')
    args = parser.parse_args()
    if (args.alsa_period < 128 or args.alsa_period > 1024 or
        any(n < 2*args.alsa_period or n > 8192 or n % args.alsa_period
            for n in (args.capture_buffer, args.playback_buffer)) or
        not 0 <= args.start_delay_us <= 100000):
        parser.error('Invalid ALSA buffer/period/start delay')
    if not 2 <= args.seconds <= 600 or not 0 <= args.prefill_ms <= 500:
        parser.error('seconds must be 2..600; prefill must be 0..500 ms')
    if not 1 <= args.output_gain_q16 <= 65536:
        parser.error('output gain must be 1..65536')
    if not 1 <= args.input_gain_q16 <= 262144:
        parser.error('input gain must be 1..262144')
    if args.check:
        preflight(args.base)
        return 0
    def terminate(signum, frame):
        raise KeyboardInterrupt('Supervisor interrupted by signal %d' % signum)
    signal.signal(signal.SIGTERM, terminate)
    return run_trial(args.base, args.seconds, args.prefill_ms, args.output_gain_q16, args.input_gain_q16,
                     args.fifo, args.fifo_io, args.require_voiced, args.alsa_period,
                     args.capture_buffer, args.playback_buffer, args.start_delay_us)


if __name__ == '__main__':
    sys.exit(main())
