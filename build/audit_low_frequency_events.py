"""Locate low-frequency-dominant events; labels are acoustic, not breath detections."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.reference.audio_io import read_pcm_wav, downsample_16k, file_sha256


def measure(path):
    rate, raw = read_pcm_wav(path)
    signal = downsample_16k(rate, raw)
    size, hop = 1024, 160
    window = np.hanning(size)
    starts = np.arange(0, len(signal) - size + 1, hop)
    frames = np.stack([signal[start:start + size] for start in starts])
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    frames -= frames.mean(axis=1, keepdims=True)
    power = np.abs(np.fft.rfft(frames * window, axis=1)) ** 2
    frequency = np.fft.rfftfreq(size, 1 / 16000)
    low = np.sum(power[:, frequency < 90], axis=1)
    ratio = low / np.maximum(np.sum(power, axis=1), 1e-30)
    candidates = (ratio > .65) & (rms > .003)
    edges = np.diff(np.r_[False, candidates, False].astype(int))
    events = []
    for first, stop in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        events.append({'start_s': float(starts[first] / 16000),
                       'end_s': float((starts[stop - 1] + size) / 16000),
                       'maximum_below_90hz_fraction': float(np.max(ratio[first:stop])),
                       'maximum_rms': float(np.max(rms[first:stop]))})
    return {'path': str(path.relative_to(ROOT)), 'sha256': file_sha256(path),
            'events': events, 'candidate_frames': int(np.sum(candidates)),
            'below_90hz_fraction_p50_p90_p99': np.percentile(ratio[rms > .003], [50, 90, 99]).tolist()}


base = ROOT / 'data/registrations/source_20261015/speaker01'
record = {'frame_size': 1024, 'hop': 160, 'rate': 16000,
          'experimental_detection': 'below90Hz_power_fraction >0.65 and rms >0.003; no human event labels',
          'recordings': [measure(base / name) for name in ['preparation_cue_v2.wav', 'holdout.wav']],
          'limitations': 'Low-frequency dominance is not a breath or wind label. Detection threshold is an inspection heuristic; does not detect all breaths or glottal rasp. First-second events may be startup/handling; no known cause. No audio modified.'}
(ROOT / 'report/low_frequency_events_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
