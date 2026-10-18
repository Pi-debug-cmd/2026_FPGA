"""Create a four-way target-registration teacher comparison; never plays audio."""
from __future__ import annotations

import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'build/generated/seed_cpu_deps'))
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.signal import resample_poly
import soundfile as sf
from src.reference.audio_io import downsample_16k, file_sha256, read_pcm_wav, write_pcm16


def load_seed(path: Path, start_s: float, count: int) -> np.ndarray:
    signal, rate = sf.read(path, dtype='float64')
    if rate != 22050 or signal.ndim != 1 or not np.all(np.isfinite(signal)):
        raise ValueError('Unexpected Seed output: ' + str(path))
    converted = resample_poly(signal, 320, 441)
    start = round(start_s * 16000)
    return converted[start:start + count]


def main() -> None:
    count = round(4.8 * 16000)
    target_path = ROOT / 'voice_src/src_1/Track 9(1).wav'
    rate, target = read_pcm_wav(target_path)
    target = downsample_16k(rate, target)[round(11 * 16000):round(11 * 16000) + count]
    old_seed = ROOT / 'build/generated/seed_reference_20261015/output_steps30/vc_source_target_1.0_30_0.7.wav'
    controlled = ROOT / 'build/generated/quality_exploration_20261018/seed_registration_controlled_seed20261019'
    cfg70 = next((controlled / 'cfg_0.70').glob('vc_*.wav'))
    cfg95 = next((controlled / 'cfg_0.95').glob('vc_*.wav'))
    paths = [target_path, old_seed, cfg70, cfg95]
    segments = [target, load_seed(old_seed, 1.0, count),
                load_seed(cfg70, 1.0, count), load_seed(cfg95, 1.0, count)]
    if any(len(signal) != count or not np.all(np.isfinite(signal)) for signal in segments):
        raise ValueError('Invalid listening segment')
    rms = [float(np.sqrt(np.mean(signal * signal))) for signal in segments]
    common = min([.08] + [.85 * level / max(float(np.max(np.abs(signal))), 1e-12)
                          for signal, level in zip(segments, rms)])
    offset = np.arange(127) - 63
    kernel = 2 * .225 * np.sinc(2 * .225 * offset) * np.hamming(127)
    kernel *= 2 / kernel.sum()
    rendered, gains = [], []
    for signal, level in zip(segments, rms):
        gain = common / level
        expanded = np.zeros(count * 2)
        expanded[::2] = signal * gain
        rendered.append(np.convolve(expanded, kernel, mode='same'))
        gains.append(gain)
    silence = np.zeros(32000)
    joined = np.concatenate([silence] + [item for index, signal in enumerate(rendered)
                                        for item in ([silence, signal] if index else [signal])])
    if not np.all(np.isfinite(joined)) or np.max(np.abs(joined)) >= 1:
        raise ValueError('Invalid comparison waveform')
    output = ROOT / 'data/registrations/source_20261015/speaker01/quality_exploration_comparison'
    output.mkdir(parents=True, exist_ok=True)
    wav = output / 'comparison.wav'
    packed = output / 'comparison.wav.gz'
    write_pcm16(wav, joined, 32000)
    packed.write_bytes(gzip.compress(wav.read_bytes(), compresslevel=9, mtime=0))
    record = {
        'kind': 'seed_target_registration_quality_listening_gate', 'date': '2026-10-18',
        'order': ['target_track9', 'seed_single_track8_cfg070',
                  'seed_multi_track_cfg070_seed20261019', 'seed_multi_track_cfg095_seed20261019'],
        'duration_s': len(joined) / 32000, 'segment_seconds': 4.8,
        'gap_seconds': 1.0, 'leading_silence_seconds': 1.0,
        'source_absolute_crop_start_s': 2.68, 'target_crop_start_s': 11.0,
        'input_sha256': {path.name + '_' + str(index): file_sha256(path)
                         for index, path in enumerate(paths)},
        'gains': gains, 'peak': float(np.max(np.abs(joined))), 'clip_samples': 0,
        'wav_sha256': file_sha256(wav), 'gzip_sha256': file_sha256(packed),
        'played': False, 'board_touched': False, 'accepted': False,
        'limitations': [
            'Ordered development comparison on one existing source utterance.',
            'Seed outputs are stochastic PC-only teachers; no Zynq runtime claim.',
            'Subjective AI-like artifacts and target similarity require fresh playback readiness.',
        ],
    }
    manifest = output / 'manifest.json'
    manifest.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'report/quality_exploration_listening_gate_20261018.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
