"""Frozen prepared configuration on separate speech; no registration or audio I/O."""
import argparse
import gzip
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'build/generated/world_deps'))
import pyworld as world
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16, file_sha256
from src.reference.world_registration import analyze
from src.reference.source_target_mapping import map_pitch
from src.reference.timbre_envelope import apply_envelope
from src.reference.spectral_balance import apply_balance


def load(path):
    rate, signal = read_pcm_wav(path)
    return downsample_16k(rate, signal)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('configuration', type=Path)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--hybrid', action='store_true', help='Old spectral warp with prepared pitch; development comparison')
    mode.add_argument('--balance-profile', type=Path, help='Broad spectral balance on the old recipe, keeping pitch/AP')
    args = parser.parse_args()
    frozen_sha = file_sha256(args.configuration)
    config = json.loads(args.configuration.read_text(encoding='utf-8'))
    if file_sha256(args.input) == config['enrollment']['source_sha256']:
        raise ValueError('Evaluation audio must differ from preparation')
    source = load(args.input) * config['enrollment']['source_analysis_gain']
    f0, times, sp = analyze(source)
    if np.sum(f0 > 0) < 300:
        raise ValueError('Insufficient voiced test material')
    ap = world.d4c(source, f0, times, 16000, fft_size=1024)
    old_profile = {'formant_warp': 1.15, 'log_power_delta': [0.] * 513}
    mapped = map_pitch(f0, config['pitch'])
    variants = {
        'old_fixed': (f0 * (108722 / 65536), apply_envelope(sp, f0 > 0, old_profile, .65)),
        'prepared_pitch': (mapped, sp),
        'prepared_timbre': (mapped, apply_envelope(sp, f0 > 0, config['envelope'], config['envelope_strength'])),
    }
    if args.hybrid:
        variants['prepared_pitch_old_warp'] = (mapped, variants['old_fixed'][1])
    if args.balance_profile:
        balance = json.loads(args.balance_profile.read_text(encoding='utf-8'))
        if (balance['source_sha256'] != config['enrollment']['source_sha256'] or
            balance['target_manifest_sha256'] != config['enrollment']['target_manifest_sha256']):
            raise ValueError('Balance profile enrollment differs')
        variants['balanced_old_fixed'] = (variants['old_fixed'][0],
            apply_balance(variants['old_fixed'][1], f0 > 0, balance))
    args.output.mkdir(parents=True, exist_ok=True)
    rendered, metrics = {}, {}
    for name, (pitch, spectrum) in variants.items():
        signal = world.synthesize(np.ascontiguousarray(pitch), np.ascontiguousarray(spectrum),
                                  ap, 16000, frame_period=10)[:len(source)]
        if len(signal) != len(source) or not np.all(np.isfinite(signal)):
            raise ValueError('Invalid output: ' + name)
        rendered[name] = signal
        peak = float(np.max(np.abs(signal)))
        gain = min(1., .9 / max(peak, 1e-12))
        path = args.output / (name + '.wav')
        write_pcm16(path, signal * gain)
        metrics[name] = {'raw_peak': peak, 'raw_clip_samples': int(np.sum(np.abs(signal) >= 1)),
                         'archive_gain': gain, 'wav_sha256': file_sha256(path),
                         'parameter_f0_median_hz': float(np.median(pitch[pitch > 0]))}
    # Pick a five-second speech-rich excerpt after the first second. Selection
    # only affects the listening crop; neither test speech nor target holdout fits parameters.
    starts = range(100, len(f0) - 500)
    start_frame = max(starts, key=lambda i: int(np.sum(f0[i:i + 500] > 0)))
    start = start_frame * 160
    length = 80000
    target_manifest = json.loads((ROOT / 'data/profiles/target.json').read_text(encoding='utf-8'))
    if file_sha256(ROOT / 'data/profiles/target.json') != config['enrollment']['target_manifest_sha256']:
        raise ValueError('Target manifest changed')
    target_path = ROOT / target_manifest['held_out_file']
    target = load(target_path)
    target_start = max(range(16000, len(target) - length, 1600),
                       key=lambda i: float(np.mean(target[i:i + length] ** 2)))
    order = (['target', 'old_fixed', 'prepared_pitch_old_warp', 'prepared_timbre'] if args.hybrid
             else ['target', 'old_fixed', 'prepared_pitch', 'prepared_timbre'])
    if args.balance_profile:
        order = ['target', 'old_fixed', 'balanced_old_fixed']
    segments = [target[target_start:target_start + length]] + [rendered[name][start:start + length] for name in order[1:]]
    if any(len(x) != length for x in segments):
        raise ValueError('Incomplete listening crop')
    rms = [float(np.sqrt(np.mean(x * x))) for x in segments]
    if min(rms) <= 1e-10:
        raise ValueError('Silent listening segment')
    common_rms = min([.08] + [.85 * level / max(float(np.max(np.abs(x))), 1e-12) for x, level in zip(segments, rms)])
    # Use the native playback rate and the established interpolation filter.
    offsets = np.arange(127) - 63
    kernel = 2 * .225 * np.sinc(2 * .225 * offsets) * np.hamming(127)
    kernel *= 2 / kernel.sum()
    parts, gains = [], []
    for segment, level in zip(segments, rms):
        gain = common_rms / level
        expanded = np.zeros(length * 2)
        expanded[::2] = segment * gain
        parts.append(np.convolve(expanded, kernel, mode='same'))
        gains.append(gain)
    joined = np.concatenate([part for i, segment in enumerate(parts)
                             for part in ([np.zeros(32000), segment] if i else [segment])])
    # Leave a second for playback startup without losing target reference speech.
    joined = np.r_[np.zeros(32000), joined]
    peak = float(np.max(np.abs(joined)))
    if peak >= 1 or not np.all(np.isfinite(joined)):
        raise ValueError('Invalid comparison waveform')
    audio = args.output / 'comparison.wav'
    write_pcm16(audio, joined, 32000)
    packed = args.output / 'comparison.wav.gz'
    packed.write_bytes(gzip.compress(audio.read_bytes(), compresslevel=9, mtime=0))
    if file_sha256(args.configuration) != frozen_sha:
        raise ValueError('Frozen configuration changed')
    development = bool(args.hybrid or args.balance_profile)
    record = {'kind': ('prepared_world_spectral_balance_development_comparison' if args.balance_profile else
                       'prepared_world_hybrid_development_comparison' if args.hybrid
                       else 'prepared_world_single_speaker_heldout_comparison'),
              'evaluation_role': ('development_after_listening_feedback' if development else 'initial_heldout_utterance'),
              'balance_profile_sha256': file_sha256(args.balance_profile) if args.balance_profile else None,
              'configuration_sha256': frozen_sha, 'input_sha256': file_sha256(args.input),
              'target_holdout_sha256': file_sha256(target_path), 'configuration_refitted': False,
              'voiced_frames': int(np.sum(f0 > 0)), 'variants': metrics, 'order': order,
              'source_crop_start_s': start / 16000, 'target_crop_start_s': target_start / 16000,
              'segment_seconds': 5, 'gap_seconds': 1, 'leading_silence_seconds': 1,
              'rate': 32000, 'duration_s': len(joined) / 32000, 'gains': gains,
              'peak': peak, 'clip_fraction': float(np.mean(np.abs(joined) >= 1)),
              'wav_sha256': file_sha256(audio), 'gzip_sha256': file_sha256(packed),
              'speaker_identity_accepted': False, 'realtime_accepted': False,
              'requires_new_final_holdout': development,
              'limitations': 'Single source, separate utterance in same session. Offline whole-recording analysis; not causal runtime. Ordered listening preview, not randomized blind evaluation. Equal RMS does not guarantee equal perceived loudness. Speech-rich crops selected for listening only.'}
    (args.output / 'manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
