"""File-only gate for bounded output low-frequency guard; voice mapping is frozen."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'build/generated/world_deps'))
from src.reference.world_registration import analyze
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16, file_sha256
from src.reference.low_frequency_guard import suppress_low_events

base = ROOT / 'data/registrations/source_20261015/speaker01'
rate, source = read_pcm_wav(base / 'holdout.wav')
source = downsample_16k(rate, source)
f0, _, _ = analyze(source)
output = base / 'low_frequency_guard'
output.mkdir(exist_ok=True)
signals = {'source': source, 'old_fixed': read_pcm_wav(base / 'hybrid_comparison/old_fixed.wav')[1]}
results = {}
for name, signal in signals.items():
    guarded, metadata = suppress_low_events(signal, f0)
    if len(guarded) != len(signal) or not np.all(np.isfinite(guarded)):
        raise ValueError('Invalid guard result')
    if np.max(np.abs(guarded)) >= 1:
        raise ValueError('Guard output clipping')
    path = output / (name + '_guarded.wav')
    write_pcm16(path, guarded)
    crop = slice(round(2.68 * 16000), round(7.68 * 16000))
    metadata.update({'wav_sha256': file_sha256(path), 'peak': float(np.max(np.abs(guarded))),
                     'raw_clip_samples': 0,
                     'full_signal_difference_rms': float(np.sqrt(np.mean((guarded - signal) ** 2))),
                     'played_crop_difference_over_signal_rms': float(np.sqrt(np.mean((guarded[crop] - signal[crop]) ** 2) / np.mean(signal[crop] ** 2))),
                     'waveform_sample_alignment_preserved': True})
    # Band-power ratios over the entire previous five-second excerpt, no gain normalization.
    window = np.hanning(1024)
    bins = np.fft.rfftfreq(1024, 1 / 16000) < 90
    def low_power(x):
        powers = [np.sum(np.abs(np.fft.rfft(x[i:i + 1024] * window))[bins] ** 2)
                  for i in range(crop.start, crop.stop - 1024 + 1, 160)]
        return float(np.sum(powers))
    metadata['played_crop_below90hz_power_ratio_after_before'] = low_power(guarded) / max(low_power(signal), 1e-30)
    results[name] = metadata
record = {'kind': 'bounded_low_frequency_guard_offline_gate', 'results': results,
          'configuration_sha256': file_sha256(base / 'configuration_cue_v2.json'),
          'configuration_changed': False, 'new_recording_or_playback': False,
          'limitations': 'Only low-frequency-dominant unvoiced coefficient frames targeted, max6dB; overlap/add can affect samples neighboring voiced boundaries. Acoustic candidates lack manual breath labels. Does not treat glottal rasp or source identity. 64ms centered offline frames, not a validated causal realtime implementation. No subjective or target identity acceptance.'}
(ROOT / 'report/low_frequency_guard_gate_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
