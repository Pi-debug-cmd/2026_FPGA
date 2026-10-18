"""Verify downloaded capture, register source, and prepare the real PL F0 recipe."""
import gzip
import hashlib
import json
from pathlib import Path
import wave

from src.ps.profile_recipe import build_recipe
from src.reference.voice_profile import register_wav

root = Path(__file__).resolve().parents[1]
base = root / 'data/registrations/source_20261011'
manifest = json.loads((base / 'capture_manifest.json').read_text())
if manifest['native_clip_fraction'] > 0.01:
    raise ValueError('Native capture clipped; preserve previous calibration')
packed = (base / 'capture.wav.gz').read_bytes()
if hashlib.sha256(packed).hexdigest() != manifest['gzip_sha256']:
    raise ValueError('Capture transfer checksum mismatch')
wav = gzip.decompress(packed)
if hashlib.sha256(wav).hexdigest() != manifest['wav_sha256']:
    raise ValueError('Decoded WAV checksum mismatch')
audio = base / 'capture.wav'
audio.write_bytes(wav)
with wave.open(str(audio), 'rb') as stream:
    if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth(), stream.getnframes()) != (
            manifest['sample_rate'], manifest['channels'], 2, manifest['frames']):
        raise ValueError('Capture format differs from manifest')
source_path = root / 'data/profiles/source.json'
source = register_wav(audio, source_path)
recipe = build_recipe(source_path, root / 'data/profiles/target.json',
                      root / 'data/profiles/current_recipe.json')
print(json.dumps({'source_f0_median_hz': source['f0_median_hz'],
                  'source_voiced_coverage_s': source['voiced_frame_coverage_s'],
                  'target_f0_median_hz': recipe['target_profile']['f0_median_hz'],
                  'ratio': recipe['ratio'], 'ratio_q16': recipe['ratio_q16'],
                  'kind': recipe['kind']}, indent=2))
