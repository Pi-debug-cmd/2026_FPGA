"""Incremental raw runtime regression, independent FIR oracle and failed I/O."""
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time
import wave
import sys
import argparse

import numpy as np

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.reference.audio_io import write_pcm16

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version', type=int, default=12)
args = parser.parse_args()
base = root / ("build/generated/world_budget/live_checks" if args.version == 12 else
               f"build/generated/world_budget/live_checks_v{args.version}")
base.mkdir(exist_ok=True)
program = root / f"build/generated/world_budget/world_live_native_v{args.version}.exe"
serial = root / "build/generated/world_budget/world_sliding_shared_native.exe"
results = []

def run(name, raw, seconds, mode="pcm16", prefill=0, expected=0, fragmented=False, gain=65536, input_gain=65536):
    args = [str(program), str(seconds), mode, str(prefill)] + ([str(gain)] if gain != 65536 else [])
    if input_gain != 65536:
        args = [str(program), str(seconds), mode, str(prefill), str(gain), str(input_gain)]
    if fragmented:
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        def feed():
            try:
                for first in range(0, len(raw), 997):
                    process.stdin.write(raw[first:first + 997])
                    process.stdin.flush()
                    time.sleep(.0002)
            finally:
                process.stdin.close()
        worker = threading.Thread(target=feed)
        worker.start()
        output = process.stdout.read()
        stderr = process.stderr.read().decode()
        process.wait(timeout=30); worker.join()
        code = process.returncode
    else:
        process = subprocess.run(args, input=raw, capture_output=True, timeout=45)
        output, stderr, code = process.stdout, process.stderr.decode(), process.returncode
    if code != expected:
        raise RuntimeError(f"{name}: exit {code}, {stderr}")
    record = json.loads(stderr)
    for key, bound in [("input_queue_peak", 64), ("parameter_queue_peak", 8),
                       ("output_queue_peak", 32), ("window_samples_max", 3807), ("live_parameters_max", 16)]:
        if record[key] > bound:
            raise AssertionError(f"{name}: {key} exceeds {bound}")
    record.update(name=name, sha256=hashlib.sha256(output).hexdigest())
    if not expected:
        stride = 16 if mode == "native_s24" else 2
        if len(output) != (seconds * 16000 + prefill * 16) * stride:
            raise AssertionError(f"{name}: output length")
        if record['captured16k'] != seconds * 16000 or record['played16k'] != seconds * 16000:
            raise AssertionError(f"{name}: dropped samples")
    results.append(record)
    (base / (name + ".raw")).write_bytes(output)
    return output

def reference(raw, name):
    pcm = np.frombuffer(raw, '<i2')
    source = base / (name + '_input.wav')
    output = base / (name + '_serial.wav')
    write_pcm16(source, pcm.astype(float) / 32768)
    subprocess.run([str(serial), str(source), str(output), 'hop40'], check=True, capture_output=True, timeout=30)
    with wave.open(str(output), 'rb') as wav:
        return wav.readframes(wav.getnframes())

with wave.open(str(root / 'build/generated/world_budget/input16k.wav'), 'rb') as wav:
    speech = wav.readframes(wav.getnframes())
for name, raw, seconds in [('speech', speech, 5), ('silence', bytes(32000), 1)]:
    expected = reference(raw, name)
    for fragmented in [False, True]:
        output = run(name + ('_fragmented' if fragmented else '_burst'), raw, seconds, fragmented=fragmented)
        if output != expected:
            raise AssertionError(f"{name}: sliding PCM changed")
    padded = run(name + '_prefill', raw, seconds, prefill=180)
    if padded != bytes(180 * 16 * 2) + expected:
        raise AssertionError('Prefill changed synthesis state')

run('truncated_sample', speech[:-1], 5, expected=3)
run('short_input', speech[:2000], 5, expected=3)
run('native_partial_frame', bytes(32000 * 8 - 1), 1, 'native_s24', expected=3)
run('native_silence', bytes(32000 * 8), 1, 'native_s24', prefill=180)

# Native channel/slot checks and independent causal 127-tap conversion oracle.
t = np.arange(32000) / 32000
source = .08 * np.sin(2 * np.pi * 140 * t) + .015 * np.sin(2 * np.pi * 280 * t)
source[(t > .45) & (t < .6)] = 0
signed = np.rint(source * 8388608).astype(np.int32)
words = np.zeros((32000, 2), dtype='<u4')
words[:, 0] = signed.astype(np.uint32) & 0xffffff
# Right channel intentionally unrelated, and high byte nonzero: only left 24 bits count.
words[:, 0] |= np.uint32(0x5a000000)
words[:, 1] = np.uint32(0xabcdef)
native = run('native_voiced', words.tobytes(), 1, 'native_s24')
offsets = np.arange(127) - 63
kernel = .45 * np.sinc(.45 * offsets) * np.hamming(127)
kernel /= kernel.sum()
filtered = np.convolve(signed.astype(float) / 8388608, kernel)[:32000:2]
# A quantized extra WORLD run is diagnostic only: F0 decisions can change under
# tiny quantization, so it is not the numerical oracle for the resampler.
pcm = np.clip(np.rint(filtered * 32768), -32768, 32767).astype('<i2')
rendered = run('native_oracle_pcm', pcm.tobytes(), 1)
mono = np.frombuffer(rendered, '<i2').astype(float) / 32767
expanded = np.zeros(32000); expanded[::2] = mono
oracle = np.convolve(expanded, 2 * kernel)[:32000]
packed = np.frombuffer(native, '<u4').reshape(-1, 2)
if not np.array_equal(packed[:, 0], packed[:, 1]):
    raise AssertionError('Native playback channels differ')
actual = ((packed[:, 0].astype(np.int64) ^ 0x800000) - 0x800000) / 8388608
rmse = float(np.sqrt(np.mean((actual - oracle) ** 2)))
correlation = float(np.corrcoef(actual, oracle)[0, 1])
adapter = base / 'check_world_fir.exe'
subprocess.run(['D:/mingw64/bin/g++.exe', '-O3', '-std=c++11', '-Wall', '-Wextra', '-Werror',
                str(root / 'sim/check_world_fir.cpp'), '-o', str(adapter)], check=True, timeout=30)
fir_checks = []
for mode, samples, expected in [
    ('down', signed.astype(float) / 8388608, filtered),
    ('up', mono, oracle),
]:
    result = subprocess.run([str(adapter), mode], input=samples.astype('<f8').tobytes(),
                            capture_output=True, check=True, timeout=30)
    observed = np.frombuffer(result.stdout, '<f8')
    error = float(np.max(np.abs(observed - expected)))
    if error > 1e-14:
        raise AssertionError(f'{mode} FIR mismatch: {error}')
    fir_checks.append({'mode': mode, 'max_error': error})
# Frequency response of the causal decimator: speech passband and alias rejection.
def attenuation(frequency):
    return float(20 * np.log10(abs(np.sum(kernel * np.exp(-2j * np.pi * frequency * np.arange(127) / 32000)))))
if attenuation(3000) < -.2 or attenuation(10000) > -40:
    raise AssertionError('FIR alias rejection failed')

# Long input catches window trimming and repeated ownership-slot reuse.
run('speech60_bounded', speech * 12, 60)
if args.version >= 13:
    scaled = run('speech240_scaled', speech, 5, prefill=240, gain=49152)
    body = np.frombuffer(scaled, '<i2')[240 * 16:].astype(np.int32)
    expected = np.frombuffer(reference(speech, 'gain_reference'), '<i2').astype(np.int32) * .75
    if np.max(np.abs(body - expected)) > 1.25:
        raise AssertionError('Output attenuation changed more than quantization')
if args.version >= 14:
    amplified = run('speech_input_gain2', speech, 5, input_gain=131072, gain=49152)
    scaled_input = (np.frombuffer(speech, '<i2').astype(np.int32) * 2).astype('<i2').tobytes()
    comparison = run('speech_input_gain2_oracle', scaled_input, 5, gain=49152)
    if amplified != comparison:
        raise AssertionError('Software input gain differs from independently scaled source')
record = {'checks': results, 'fir_independent_checks': fir_checks,
          'extra_quantization_world_rmse_diagnostic': rmse, 'extra_quantization_world_correlation_diagnostic': correlation,
          'fir_3khz_db': attenuation(3000), 'fir_10khz_db': attenuation(10000),
          'fir_delay_per_conversion_ms': 63 / 32000 * 1000,
          'limitation': 'Host pipe and file regression; no ARM runtime budget, ALSA xrun, listening or end-to-end latency acceptance'}
destination = root / ('report/world_live_host_checks_20261013.json' if args.version == 12 else
                      f'report/world_live_host_checks_v{args.version}_20261013.json')
destination.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'checks_passed': len(results), 'fir_checks': fir_checks, 'report': str(destination)}))
