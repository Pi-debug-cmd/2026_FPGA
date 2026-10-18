"""Versioned target-registration profile shared with the realtime integration owner."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 'target-profile-v2'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def parse_world_profile(path: Path) -> dict[str, Any]:
    scalar: dict[str, float | int] = {}
    bands: dict[str, float] = {}
    ap: dict[str, float] = {}
    spectrum: list[float] | None = None
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        fields = line.split()
        if fields[0] == 'band_db' and len(fields) == 3:
            bands[fields[1]] = float(fields[2])
        elif fields[0] == 'ap_mean' and len(fields) == 3:
            ap[fields[1]] = float(fields[2])
        elif fields[0] == 'spectrum_db' and len(fields) > 1:
            spectrum = [float(value) for value in fields[1:]]
        elif len(fields) == 2:
            value = float(fields[1])
            scalar[fields[0]] = int(value) if value.is_integer() else value
        else:
            raise ValueError('Unrecognized WORLD profile line: ' + line[:80])
    required = {
        'rate', 'frame_period_ms', 'fft_size', 'samples', 'frames', 'voiced_frames',
        'voiced_fraction', 'f0_median_hz', 'f0_p10_hz', 'f0_p90_hz',
        'f0_min_hz', 'f0_max_hz', 'spectrum_bins',
    }
    missing = required - scalar.keys()
    if missing:
        raise ValueError('Missing WORLD profile fields: ' + ', '.join(sorted(missing)))
    if spectrum is None or len(spectrum) != scalar['spectrum_bins']:
        raise ValueError('Spectrum length does not match spectrum_bins')
    return {'scalar': scalar, 'bands_db': bands, 'aperiodicity_mean': ap, 'spectrum_db': spectrum}


def build_profile(world_path: Path, source_audio: Path | None = None,
                  speaker_embedding: list[float] | None = None,
                  embedding_model: str | None = None,
                  snr_db: float | None = None,
                  native_clip_samples: int | None = None) -> dict[str, Any]:
    world = parse_world_profile(world_path)
    scalar = world['scalar']
    voiced_seconds = scalar['voiced_frames'] * scalar['frame_period_ms'] / 1000.0
    registration_checks = {
        'voiced_seconds': voiced_seconds,
        'voiced_seconds_minimum': 10.0,
        'snr_db': snr_db,
        'snr_db_minimum': 20.0,
        'native_clip_samples': native_clip_samples,
        'native_clip_samples_maximum': 0,
        'speaker_embedding_available': speaker_embedding is not None,
    }
    a1_ready = voiced_seconds >= 5.0 and (native_clip_samples in (None, 0))
    neural_ready = (voiced_seconds >= 10.0 and snr_db is not None and snr_db >= 20.0
                    and native_clip_samples == 0 and speaker_embedding is not None)
    payload: dict[str, Any] = {
        'schema_version': SCHEMA_VERSION,
        'source': {
            'world_profile_path': str(world_path),
            'world_profile_sha256': sha256(world_path),
            'audio_path': str(source_audio) if source_audio else None,
            'audio_sha256': sha256(source_audio) if source_audio else None,
        },
        'analysis': {
            'sample_rate_hz': scalar['rate'], 'frame_period_ms': scalar['frame_period_ms'],
            'fft_size': scalar['fft_size'], 'frames': scalar['frames'],
            'voiced_frames': scalar['voiced_frames'], 'voiced_fraction': scalar['voiced_fraction'],
        },
        'pitch_hz': {
            'minimum': scalar['f0_min_hz'], 'p10': scalar['f0_p10_hz'],
            'median': scalar['f0_median_hz'], 'p90': scalar['f0_p90_hz'],
            'maximum': scalar['f0_max_hz'],
        },
        'world_acoustics': {
            'bands_db': world['bands_db'], 'aperiodicity_mean': world['aperiodicity_mean'],
            'spectrum_db': world['spectrum_db'],
        },
        'speaker_condition': {
            'model': embedding_model, 'dimension': len(speaker_embedding) if speaker_embedding else 0,
            'embedding': speaker_embedding,
        },
        'registration_checks': registration_checks,
        'runtime_capabilities': {
            'a1_world_ready': a1_ready,
            'neural_target_condition_ready': neural_ready,
        },
        'acceptance': {
            'accepted_for_a1': a1_ready,
            'accepted_for_neural_target_condition': neural_ready,
            'reason': ('complete' if neural_ready else
                       'speaker embedding and/or SNR/native-clip evidence missing'),
        },
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':')).encode('utf-8')
    payload['integrity'] = {'algorithm': 'sha256', 'payload_sha256': hashlib.sha256(canonical).hexdigest()}
    return payload


def verify_profile(profile: dict[str, Any]) -> bool:
    if profile.get('schema_version') != SCHEMA_VERSION or 'integrity' not in profile:
        return False
    expected = profile['integrity'].get('payload_sha256')
    payload = {key: value for key, value in profile.items() if key != 'integrity'}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest() == expected
