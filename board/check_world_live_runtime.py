"""File/pipe checks only; never invokes ALSA or accesses PL."""
import argparse
import array
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import wave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('input_wav', type=Path)
    parser.add_argument('output_dir', type=Path)
    parser.add_argument('--prefill-ms', type=int, default=180)
    parser.add_argument('--output-gain-q16', type=int, default=65536)
    parser.add_argument('--input-gain-q16', type=int, default=65536)
    parser.add_argument('--fifo', action='store_true')
    args = parser.parse_args()
    args.output_dir.mkdir(exist_ok=False)
    with wave.open(str(args.input_wav), 'rb') as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getnframes()) != (16000, 1, 2, 80000):
            raise ValueError('Expected pinned five-second input')
        raw = wav.readframes(80000)
    native = array.array('I')
    for sample in array.array('h', raw):
        left = (sample * 256) & 0xffffff
        native.extend([left, 0xabcdef, left, 0xabcdef])
    checks = []
    for mode, source in [('pcm16', raw), ('native_s24', native.tobytes())]:
        output = args.output_dir / (mode + '.raw')
        with output.open('wb') as stream:
            command = [str(args.binary), '5', mode, str(args.prefill_ms)]
            if args.fifo or args.input_gain_q16 != 65536 or args.output_gain_q16 != 65536:
                command.extend([str(args.output_gain_q16), str(args.input_gain_q16)])
            if args.fifo:
                command.append('fifo')
            process = subprocess.run(command, input=source,
                                     stdout=stream, stderr=subprocess.PIPE, timeout=25)
        if process.returncode:
            raise RuntimeError(process.stderr.decode())
        record = json.loads(process.stderr)
        if args.fifo and (not record['scheduling_fifo'] or any(record[k] for k in
            ['reader_sched_error', 'analysis_sched_error', 'render_sched_error', 'writer_sched_error'])):
            raise AssertionError('FIFO scheduling not installed')
        stride = 2 if mode == 'pcm16' else 16
        if output.stat().st_size != (80000 + args.prefill_ms * 16) * stride:
            raise AssertionError('Incomplete output')
        record.update(test=mode, output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        checks.append(record)
    if sys.platform.startswith('linux'):
        timeout_command = [str(args.binary), '1', 'pcm16', '0']
        if args.fifo:
            timeout_command.extend([str(args.output_gain_q16), str(args.input_gain_q16), 'fifo'])
        # No capture process: held-open input pipe must time out instead of hang.
        child = subprocess.Popen(timeout_command, stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            child.wait(timeout=8)
            record = json.loads(child.stderr.read())
            if child.returncode != 7:
                raise AssertionError('Input progress timeout not reported')
            checks.append(dict(record, test='held_input_timeout'))
        finally:
            child.stdin.close()
            if child.poll() is None:
                child.kill(); child.wait(timeout=3)
        child = subprocess.Popen(timeout_command, stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            time.sleep(.2)
            child.terminate(); child.wait(timeout=3)
            record = json.loads(child.stderr.read())
            if child.returncode != 130:
                raise AssertionError('SIGTERM was not handled')
            checks.append(dict(record, test='sigterm_held_input'))
        finally:
            child.stdin.close()
            if child.poll() is None:
                child.kill(); child.wait(timeout=3)
    record = {'kind': 'world_live_file_checks', 'checks': checks,
              'limitation': 'Unpaced raw-file/pipe checks only; no capture/playback, latency or xrun evidence'}
    (args.output_dir / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
