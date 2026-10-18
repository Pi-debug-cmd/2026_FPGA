"""Measure blocked-runtime CPU; no ALSA, PL, playback or clock modification."""
import argparse
import json
from pathlib import Path
import os
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--modes', nargs='+', choices=['normal', 'fifo', 'fifo_io'], default=['normal', 'fifo'])
    args = parser.parse_args()
    results = []
    for mode in args.modes:
        started = time.monotonic()
        child = subprocess.Popen([str(args.binary), '1', 'pcm16', '0', '65536', '65536', mode],
                                 stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            ticks = os.sysconf('SC_CLK_TCK')
            last_cpu = {}
            while child.poll() is None and time.monotonic() - started < 8:
                for task in (Path('/proc') / str(child.pid) / 'task').glob('*'):
                    try:
                        fields = (task / 'stat').read_text().rsplit(')', 1)[1].split()
                        # Fields 14/15, with state (field 3) at list position 0.
                        last_cpu[task.name] = (int(fields[11]), int(fields[12]))
                    except (OSError, ValueError, IndexError):
                        pass  # A thread may exit between directory/read operations.
                time.sleep(.2)
            child.wait(timeout=1)
            runtime = json.loads(child.stderr.read())
            if child.returncode != 7:
                raise RuntimeError('Unexpected wait-test exit: ' + str(runtime))
            results.append({'mode': mode, 'elapsed_s': time.monotonic() - started,
                            'sampled_user_cpu_s': sum(v[0] for v in last_cpu.values()) / ticks,
                            'sampled_system_cpu_s': sum(v[1] for v in last_cpu.values()) / ticks,
                            'sampled_threads': len(last_cpu), 'clock_ticks_per_s': ticks,
                            'cpu_measurement': 'Latest per-thread /proc stat snapshots, may omit final ~0.2s',
                            'runtime': runtime})
        finally:
            child.stdin.close()
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)
    print(json.dumps({'kind': 'world_held_input_cpu_probe', 'checks': results}))


if __name__ == '__main__':
    main()
