"""Generate an isolated WORLD synthesis variant from the pinned source."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'build/generated/world_source_v035/pyworld-0.3.5/lib/World/src/synthesis.cpp'
original = source.read_text()
old = '''  double re, im, re2, im2;
  for (int i = 0; i <= fft_size / 2; ++i) {
    re = inverse_real_fft->spectrum[i][0];
    im = inverse_real_fft->spectrum[i][1];
    re2 = cos(coefficient * i);
    im2 = sqrt(1.0 - re2 * re2);  // sin(pshift)

    inverse_real_fft->spectrum[i][0] = re * re2 + im * im2;
    inverse_real_fft->spectrum[i][1] = im * re2 - re * im2;
  }'''
new = '''  // Codex project optimization: fractional delay is in [0, 1/fs], so
  // coefficient*i is in [0, pi] and the original positive sqrt equals sin.
  // Keep upstream interpolation, FFT, excitation and pulse phase unchanged.
  const double step_re = cos(coefficient), step_im = sin(coefficient);
  double phase_re = 1.0, phase_im = 0.0;
  for (int i = 0; i <= fft_size / 2; ++i) {
    const double re = inverse_real_fft->spectrum[i][0];
    const double im = inverse_real_fft->spectrum[i][1];
    inverse_real_fft->spectrum[i][0] = re * phase_re + im * phase_im;
    inverse_real_fft->spectrum[i][1] = im * phase_re - re * phase_im;
    const double next_re = phase_re * step_re - phase_im * step_im;
    phase_im = phase_im * step_re + phase_re * step_im;
    phase_re = next_re;
  }'''
if original.count(old) != 1:
    raise ValueError('Pinned synthesis function changed; inspect before applying optimization')
result = original.replace(old, new)
out = root / 'build/generated/world_budget/optimized_world'
out.mkdir(exist_ok=True)
path = out / 'synthesis.cpp'
path.write_text(result, newline='\n')
record = {'kind': 'world_fractional_delay_phase_recurrence',
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'generated_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'scope': 'Batch synthesis only; upstream source and realtime synthesizer unchanged',
          'limitation': 'Floating point recurrence needs waveform agreement and ARM performance verification'}
(out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
