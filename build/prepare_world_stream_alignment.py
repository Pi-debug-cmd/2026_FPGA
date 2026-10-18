"""Isolate the streaming DC-removal difference from the approved batch synth."""
import hashlib
import argparse
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--full', action='store_true', help='Also align sub-sample phase and release samples after FFT lookahead')
args = parser.parse_args()
upstream = root / 'build/generated/world_source_v035/pyworld-0.3.5/lib/World/src'
stream_path = upstream / 'synthesisrealtime.cpp'
stream = stream_path.read_text()
batch = (upstream / 'synthesis.cpp').read_text()
start = 'static void RemoveDCComponent('
stop = '\n//-----------------------------------------------------------------------------\n// GetPeriodicResponse()'
stream_begin, batch_begin = stream.index(start), batch.index(start)
stream_end, batch_end = stream.index(stop, stream_begin), batch.index(stop, batch_begin)
stream = stream[:stream_begin] + batch[batch_begin:batch_end] + stream[stream_end:]
for old, new in [
    ('synth->dc_remover = new double[synth->fft_size / 2];',
     'synth->dc_remover = new double[synth->fft_size];'),
    ('GetDCRemover(synth->fft_size / 2, synth->dc_remover);',
     'GetDCRemover(synth->fft_size, synth->dc_remover);')]:
    if stream.count(old) != 1:
        raise ValueError('Pinned realtime source changed: ' + old)
    stream = stream.replace(old, new)
if args.full:
    def replace_once(old, new):
        global stream
        if stream.count(old) != 1:
            raise ValueError('Pinned source occurrence differs: ' + old[:70])
        stream = stream.replace(old, new)

    old = '''      synth->pulse_locations[pointer][number_of_pulses] =
        time_axis[i] - static_cast<double>(synth->handoff) / synth->fs;
      synth->pulse_locations_index[pointer][number_of_pulses] =
        matlab_round(synth->pulse_locations[pointer][number_of_pulses] *
            synth->fs);'''
    new = '''      const double grid_time = time_axis[i] -
        static_cast<double>(synth->handoff) / synth->fs;
      const double y1 = wrap_phase[i] - 2.0 * world::kPi;
      const double y2 = wrap_phase[i + 1];
      const double fraction = -y1 / (y2 - y1);
      synth->pulse_locations[pointer][number_of_pulses] = grid_time + fraction / synth->fs;
      synth->pulse_locations_index[pointer][number_of_pulses] = matlab_round(grid_time * synth->fs);'''
    replace_once(old, new)
    # The batch DC section copied above already includes the phase helper.
    if stream.count('static void GetSpectrumWithFractionalTimeShift(') != 1:
        raise ValueError('Batch phase helper missing or duplicated')
    replace_once('const double *dc_remover, double *periodic_response) {',
                 'const double *dc_remover, double *periodic_response, double fractional_time_shift, int fs) {')
    periodic_begin = stream.index('static void GetPeriodicResponse(')
    periodic_end = stream.index('static void GetSpectralEnvelope(', periodic_begin)
    periodic = stream[periodic_begin:periodic_end]
    anchor = '  fft_execute(inverse_real_fft->inverse_fft);'
    if periodic.count(anchor) != 1:
        raise ValueError('Periodic FFT anchor changed')
    periodic = periodic.replace(anchor, '''  const double coefficient = 2.0 * world::kPi * fractional_time_shift * fs / fft_size;
  GetSpectrumWithFractionalTimeShift(fft_size, coefficient, inverse_real_fft);
''' + anchor)
    stream = stream[:periodic_begin] + periodic + stream[periodic_end:]
    replace_once('  // Synthesis of the periodic response\n  GetPeriodicResponse', '''  const int pulse_pointer = synth->current_pointer % synth->number_of_pointers;
  const double fractional_time_shift = synth->pulse_locations[pulse_pointer][synth->i] -
    current_location / static_cast<double>(synth->fs);
  // Synthesis of the periodic response
  GetPeriodicResponse''')
    replace_once('      synth->dc_remover, periodic_response);',
                 '      synth->dc_remover, periodic_response, fractional_time_shift, synth->fs);')
    # Both the locked-state test and output readiness must include future pulses.
    anchor = 'synth->synthesized_sample + synth->buffer_size >= synth->last_location'
    if stream.count(anchor) != 2:
        raise ValueError('Readiness anchors changed')
    stream = stream.replace(anchor, 'synth->synthesized_sample + synth->buffer_size + synth->fft_size / 2 >= synth->last_location')
    replace_once('while (current_location < synth->synthesized_sample + synth->buffer_size) {',
                 'while (current_location < synth->synthesized_sample + synth->buffer_size + synth->fft_size / 2) {')
    replace_once('''        log(spectrum[i] * aperiodic_ratio[i] +
        world::kMySafeGuardMinimum) / 2.0;''',
                 '        log(spectrum[i] * aperiodic_ratio[i]) / 2.0;')
out = root / ('build/generated/world_budget/aligned_world_full' if args.full else 'build/generated/world_budget/aligned_world')
out.mkdir(exist_ok=True)
result = out / 'synthesisrealtime.cpp'
result.write_text(stream, newline='\n')
record = {'kind': 'stream_full_batch_alignment_experiment' if args.full else 'stream_dc_matches_batch_experiment',
          'upstream_sha256': hashlib.sha256(stream_path.read_bytes()).hexdigest(),
          'generated_sha256': hashlib.sha256(result.read_bytes()).hexdigest(),
          'scope': 'DC, fractional pulse phase, FFT lookahead and noise log formula' if args.full else 'DC response length, buffer allocation and removal formula only',
          'limitation': ('Analysis is still offline; 32ms synthesis lookahead and tail handling need validation' if args.full else
                         'Fractional pulse timing and other stream differences remain; no quality acceptance')}
(out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
