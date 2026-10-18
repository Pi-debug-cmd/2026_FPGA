"""Paced synthetic pipe diagnostic; no ALSA, microphone, speaker or PL access."""
import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import threading
import time


def synthetic_source(seconds):
    # Low-level harmonic fixture exercises voiced analysis without clipping.
    source = array.array('I')
    for i in range(32000):
        value = int(120000 * (math.sin(2 * math.pi * 160 * i / 32000)
                             + .3 * math.sin(2 * math.pi * 320 * i / 32000)))
        source.extend([value & 0xffffff, value & 0xffffff])
    return source.tobytes() * seconds


def run(binary, seconds, mode, input_second=None):
    raw = synthetic_source(seconds) if input_second is None else input_second.read_bytes() * seconds
    if len(raw) != seconds * 256000:
        raise ValueError('Expected one second of 32kHz S24_LE stereo in 32-bit words')
    started = time.monotonic()
    child = subprocess.Popen([str(binary), str(seconds), 'native_s24', '200',
                              '49152', '262144', mode], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    errors, gaps, feed_lateness = [], [], []
    digest = hashlib.sha256()
    output_bytes = [0]

    def feed():
        try:
            for index in range(seconds * 125):
                target = started + (index + 1) * .008
                time.sleep(max(0, target - time.monotonic()))
                feed_lateness.append(time.monotonic() - target)
                child.stdin.write(raw[index * 2048:(index + 1) * 2048])
                child.stdin.flush()
        except Exception as exc:
            errors.append('feed: ' + repr(exc))
        finally:
            child.stdin.close()

    def drain():
        previous = time.monotonic()
        try:
            while True:
                block = child.stdout.read(2048)
                if not block:
                    break
                now = time.monotonic()
                # Exclude the silence-to-first-processed-block startup gap.
                if output_bytes[0] > 200 * 256:
                    gaps.append(now - previous)
                previous = now
                digest.update(block)
                output_bytes[0] += len(block)
        except Exception as exc:
            errors.append('drain: ' + repr(exc))

    feeder = threading.Thread(target=feed)
    drainer = threading.Thread(target=drain)
    feeder.start()
    drainer.start()
    ticks = os.sysconf('SC_CLK_TCK')
    cpu, samples = {}, []
    try:
        while child.poll() is None and time.monotonic() - started < seconds + 10:
            for task in (Path('/proc') / str(child.pid) / 'task').glob('*'):
                try:
                    fields = (task / 'stat').read_text().rsplit(')', 1)[1].split()
                    cpu[task.name] = (int(fields[11]) + int(fields[12])) / ticks
                except (OSError, ValueError, IndexError):
                    pass
            samples.append({'elapsed_s': time.monotonic() - started, 'threads_cpu_s': dict(cpu)})
            time.sleep(.25)
        child.wait(timeout=1)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=3)
        feeder.join(timeout=3)
        drainer.join(timeout=3)
    runtime = json.loads(child.stderr.read())
    expected = (seconds * 32000 + 6400) * 8
    if errors or child.returncode or output_bytes[0] != expected:
        raise RuntimeError(str((errors, child.returncode, output_bytes, runtime)))
    if runtime['scheduling_fifo'] != (mode == 'fifo') or runtime.get('scheduling_fifo_io', False) != (mode == 'fifo_io'):
        raise RuntimeError('Requested scheduling mode not reported: ' + str(runtime))
    if any(runtime[key] for key in ['reader_sched_error', 'analysis_sched_error', 'render_sched_error', 'writer_sched_error']):
        raise RuntimeError('Thread scheduling was not verified: ' + str(runtime))
    return {'mode': mode, 'runtime': runtime, 'output_bytes': output_bytes[0],
            'input_second_sha256': hashlib.sha256(raw[:256000]).hexdigest(),
            'output_sha256': digest.hexdigest(), 'cpu_samples': samples,
            'max_output_chunk_gap_ms': max(gaps, default=0) * 1000,
            'output_chunk_gaps_over_24ms': sum(gap > .024 for gap in gaps),
            'max_input_release_lateness_ms': max(feed_lateness, default=0) * 1000,
            'limitation': 'Synthetic paced input, immediate pipe sink; gaps are not ALSA xruns or latency.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--seconds', type=int, default=20, choices=range(1, 601))
    parser.add_argument('--modes', nargs='+', choices=['normal', 'fifo', 'fifo_io'], default=['normal', 'fifo'])
    parser.add_argument('--input-second', type=Path, help='Pinned one-second native raw fixture, repeated for the trial')
    args = parser.parse_args()
    checks = [run(args.binary, args.seconds, mode, args.input_second) for mode in args.modes]
    args.output.write_text(json.dumps({'checks': checks}, indent=2) + '\n')
    for check in checks:
        print(json.dumps({key: value for key, value in check.items() if key != 'cpu_samples'}))
