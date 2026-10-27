"""Verify Deepseek batch/stream S24_LE parity against its PCM16 path."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    t = np.arange(32000 * 2) / 32000
    x = np.rint(6000 * np.sin(2 * np.pi * 140 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))).astype('<i2')
    pcm = np.repeat(x[:, None], 2, axis=1).tobytes()
    native = np.repeat((x.astype('<i4') * 256)[:, None], 2, axis=1).astype('<i4').tobytes()
    results = []
    for mode in ([], ['--stream', '300']):
        outputs = []
        for fmt, payload, dtype, scale in [('pcm16', pcm, '<i2', 32768), ('native_s24', native, '<i4', 8388608)]:
            cmd = [args.exe, '2', fmt, '200', '--model', args.model, '--preset', 'live', *mode]
            p = subprocess.run(cmd, input=payload, capture_output=True, check=True)
            samples = np.frombuffer(p.stdout, dtype=dtype).astype(np.float64) / scale
            outputs.append(samples)
        assert outputs[0].size == outputs[1].size == 128000
        error = float(np.max(np.abs(outputs[0] - outputs[1])))
        assert error <= 1 / 32768, error
        results.append({'mode': 'stream' if mode else 'batch', 'max_abs_error': error, 'limit': 1 / 32768, 'samples_stereo': outputs[0].size, 'passed': True})
    Path(args.output).write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
