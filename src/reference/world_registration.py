"""Prepare a source-to-target WORLD configuration before realtime operation."""
import json
from pathlib import Path
import numpy as np

from src.reference.audio_io import read_pcm_wav, downsample_16k, file_sha256
from src.reference.source_target_mapping import fit_pitch_mapping, map_pitch
from src.reference.timbre_envelope import normalized_log_shape, register_envelope, apply_envelope


def analyze(signal):
    import pyworld as world
    signal = np.ascontiguousarray(signal, dtype=np.float64)
    f0, times = world.dio(signal, 16000, f0_floor=75, f0_ceil=400,
                         frame_period=10, speed=4)
    f0 = world.stonemask(signal, f0, times, 16000)
    centers = np.rint(times * 16000).astype(int)
    left, right = np.maximum(0, centers - 320), np.minimum(len(signal), centers + 320)
    energy = np.r_[0., np.cumsum(signal * signal)]
    f0[(energy[right] - energy[left]) / np.maximum(1, right - left) < 10 ** -4.5] = 0
    spectrum = world.cheaptrick(signal, f0, times, 16000, fft_size=1024)
    return f0, times, spectrum


def load_enrollment(path, analysis_gain=1.):
    rate, signal = read_pcm_wav(path)
    if not np.isfinite(analysis_gain) or not 0 < analysis_gain <= 8:
        raise ValueError('Analysis gain outside (0, 8]')
    if len(signal) / rate < 5 or np.any(np.abs(signal) >= 32760 / 32768):
        raise ValueError('Need >=5 seconds without near-full-scale capture')
    converted = downsample_16k(rate, signal) * analysis_gain
    if np.max(np.abs(converted)) >= 1:
        raise ValueError('Analysis gain would clip; recording not registered')
    return converted


def fit_configuration(source_f0, source_sp, target_f0, target_shape):
    pitch = fit_pitch_mapping(source_f0, target_f0)
    envelope = register_envelope(normalized_log_shape(source_sp, source_f0 > 0), target_shape, 16000)
    limit = 3 * np.log(10) / 10
    envelope['log_power_delta'] = np.clip(envelope['log_power_delta'], -limit, limit).tolist()
    envelope['gain_limit_db'] = 3
    return {'version': 1, 'kind': 'experimental_world_source_target_configuration',
            'sample_rate': 16000, 'fft_size': 1024, 'frame_period_ms': 10,
            'pitch': pitch, 'envelope': envelope, 'envelope_strength': .65,
            'speaker_identity_accepted': False, 'realtime_accepted': False,
            'limitations': 'Statistical pitch/envelope configuration, not a trained neural model. Source AP retained; global spectral averages mix phonemes and microphones.'}


def save_configuration(path, configuration):
    # Validate complete numeric encoding before touching a prior valid configuration.
    encoded = json.dumps(configuration, indent=2, allow_nan=False) + '\n'
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(encoded, encoding='utf-8')
    temporary.replace(path)


def register(source_path, target_manifest, root, output_path, source_analysis_gain=1.):
    root, source_path, output_path = Path(root), Path(source_path), Path(output_path)
    manifest = json.loads(Path(target_manifest).read_text(encoding='utf-8'))
    targets = [(root / entry['path'], entry) for entry in manifest['source_files']]
    inputs = [source_path, Path(target_manifest)] + [path for path, _ in targets]
    if output_path.resolve() in [path.resolve() for path in inputs]:
        raise ValueError('Configuration must not overwrite input material')
    for path, entry in targets:
        if file_sha256(path) != entry['sha256']:
            raise ValueError('Target enrollment hash changed')
    f0, _, sp = analyze(load_enrollment(source_path, source_analysis_gain))
    target_f0, shapes, counts = [], [], []
    for path, entry in targets:
        target_pitch, _, target_sp = analyze(load_enrollment(path))
        target_f0.extend(target_pitch)
        shapes.append(normalized_log_shape(target_sp, target_pitch > 0))
        counts.append(int(np.sum(target_pitch > 0)))
    configuration = fit_configuration(f0, sp, target_f0, np.average(shapes, axis=0, weights=counts))
    configuration['enrollment'] = {'source_sha256': file_sha256(source_path),
                                  'source_analysis_gain': source_analysis_gain,
                                  'target_manifest_sha256': file_sha256(target_manifest),
                                  'target_files': manifest['source_files']}
    save_configuration(output_path, configuration)
    return configuration


def convert_file(input_path, configuration):
    import pyworld as world
    rate, signal = read_pcm_wav(input_path)
    signal = downsample_16k(rate, signal) * configuration['enrollment']['source_analysis_gain']
    f0, times, sp = analyze(signal)
    ap = world.d4c(signal, f0, times, 16000, fft_size=1024)
    mapped_sp = apply_envelope(sp, f0 > 0, configuration['envelope'], configuration['envelope_strength'])
    result = world.synthesize(map_pitch(f0, configuration['pitch']), np.ascontiguousarray(mapped_sp),
                              ap, 16000, frame_period=10)[:len(signal)]
    if len(result) != len(signal) or not np.all(np.isfinite(result)):
        raise ValueError('Invalid synthesis')
    return result
