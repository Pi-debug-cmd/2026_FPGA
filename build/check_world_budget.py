"""Compare an ARM budget output against the same pinned host WORLD analysis."""
import json
from pathlib import Path
import sys
import numpy as np
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'build/generated/world_deps'))
sys.path.insert(0, str(root))
import pyworld as world
from src.reference.audio_io import read_pcm_wav
from src.reference.timbre_envelope import apply_envelope
from src.reference.voice_profile import estimate_f0

base = root / 'build/generated/world_budget'
rate, signal = read_pcm_wav(base / 'input16k.wav')
assert rate == 16000
signal = np.ascontiguousarray(signal)
checks = []
variants = [('harvest', 'harvest', 5, 2), ('dio', 'dio', 5, 2)]
if (base / 'dio_fast_v3_arm.wav').exists():
    variants.append(('dio_fast_v3', 'dio', 10, 1))
for name, algorithm, period, radius in variants:
    f0, times = getattr(world, algorithm)(signal, rate, f0_floor=75, f0_ceil=400, frame_period=period)
    f0 = world.stonemask(signal, f0, times, rate)
    centers = np.rint(times * rate).astype(int)
    left, right = np.maximum(0, centers - 320), np.minimum(len(signal), centers + 320)
    energy = np.concatenate(([0.], np.cumsum(signal * signal)))
    f0[(energy[right] - energy[left]) / np.maximum(1, right - left) < 10 ** -4.5] = 0
    voiced = f0 > 0
    edges = np.diff(np.concatenate(([False], voiced, [False])).astype(int))
    for first, last in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        original = f0[first:last].copy()
        for i in range(len(original)):
            f0[first + i] = np.median(original[max(0, i - radius):i + radius + 1])
    sp = world.cheaptrick(signal, f0, times, rate, fft_size=1024)
    ap = world.d4c(signal, f0, times, rate, fft_size=1024)
    profile = {'formant_warp': 1.15, 'log_power_delta': [0.] * 513}
    sp = apply_envelope(sp, voiced, profile, .65)
    reference = world.synthesize(f0 * (108722 / 65536), np.ascontiguousarray(sp), ap,
                                 rate, frame_period=period)[:len(signal)]
    board_rate, actual = read_pcm_wav(base / (name + '_arm.wav'))
    assert board_rate == rate and len(actual) == len(signal)
    correlation = float(np.corrcoef(reference, actual)[0, 1])
    error = float(np.sqrt(np.mean((reference - actual) ** 2)))
    observed_f0, _ = estimate_f0(actual)
    checks.append({'algorithm': name, 'correlation': correlation, 'rmse': error,
                   'f0_median_hz': float(np.median(observed_f0)),
                   'voiced_coverage_s': len(observed_f0) * .01,
                   'clip_fraction': float(np.mean(np.abs(actual) >= 32760 / 32768))})
    # Numerical agreement only; neither listening quality nor latency acceptance.
    if correlation < .999 or error > .001 or not np.isfinite(error):
        raise ValueError('ARM output differs from pinned host reference: ' + algorithm)
record = {'kind': 'offline_arm_world_agreement', 'checks': checks,
          'limitation': 'Batch processing a five-second crop; not a streaming latency test'}
(root / 'report/world_budget_agreement_20261011.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
