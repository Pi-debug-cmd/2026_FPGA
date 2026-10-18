"""Offline identity / naturalness / content diagnostics for the Seed-VC reference.

Read-only use of existing WAVs. No playback, no board access, no training, no
new audio. Every number here is a diagnostic, never an acceptance decision:
the user's listening stays the gate.

Protocol is deliberately the same as the historical cross evaluator
(report protocol 'mono16k-6s-nonoverlap-tail1.5s-fbank80hamming-cmn-noVAD-rms0.04')
so new numbers can be placed next to the old ones instead of replacing them.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from math import gcd
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / 'build/generated'
EVAL_DEPS = DEPS / 'eval_deps_20261016'
SPEECHMOS_ROOT = next((DEPS / 'eval_sources_20261016').glob('SpeechMOS-*'))
HF_CACHE = ROOT / '交接/核心材料/neural_reference/cache/hf/hub'
WHISPER_SNAPSHOT = next((HF_CACHE / 'models--openai--whisper-small/snapshots').glob('*'), None)

for extra in (EVAL_DEPS, DEPS / 'world_deps', DEPS / 'llvc_cpu_deps', DEPS / 'seed_audio_deps',
              DEPS / 'seed_cpu_deps'):
    if extra.is_dir():
        sys.path.insert(0, str(extra))
sys.path.insert(0, str(SPEECHMOS_ROOT))

os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
os.environ['HF_HUB_CACHE'] = str(HF_CACHE)
os.environ['HF_HOME'] = str(HF_CACHE.parent)

import soundfile as sf  # noqa: E402
import torch  # noqa: E402
import torchaudio  # noqa: E402
import onnxruntime as ort  # noqa: E402
import pyworld  # noqa: E402
from scipy.signal import resample_poly  # noqa: E402
from speechmos.utmos22.strong.model import UTMOS22Strong  # noqa: E402

torch.set_num_threads(4)

BASE = ROOT / 'data/registrations/source_20261015/speaker01'
VOICE = ROOT / 'voice_src/src_1'
CROSS = ROOT / '交接/核心材料/neural_reference/cross_evaluators'
WESPEAKER = CROSS / 'cnceleb_resnet34_LM.onnx'
UTMOS_WEIGHT = CROSS / 'utmos22_strong_step7459_v1.pt'
SEED_OUTPUT = DEPS / 'seed_reference_20261015/output_steps30/vc_source_target_1.0_30_0.7.wav'
SEED_OUTPUT_SHA = '78be5244c6d869b6c9d8558d117718bf326ae024c843a375279c4a4175f346e6'

PROTOCOL = 'mono16k-6s-nonoverlap-tail1.5s-fbank80hamming-cmn-noVAD-rms0.04-utmosFP32-cpu-v1'
TARGET_TRACKS = ['Track 5(1).wav', 'Track 6(1).wav', 'Track 7(1).wav', 'Track 8(1).wav']
HELD_OUT_TRACK = 'Track 9(1).wav'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load16(path: Path, start: float | None = None, seconds: float | None = None) -> np.ndarray:
    """Mono 16 kHz float64 window; explicit offline resampling only."""
    x, sr = sf.read(str(path), dtype='float64', always_2d=False)
    if x.ndim == 2:
        x = x.mean(axis=1)
    if start is not None:
        x = x[int(round(start * sr)):]
    if seconds is not None:
        x = x[:int(round(seconds * sr))]
    if sr != 16000:
        g = gcd(int(sr), 16000)
        x = resample_poly(x, 16000 // g, int(sr) // g)
    return np.ascontiguousarray(x, dtype=np.float64)


def chunks(x: np.ndarray):
    """Same 6 s / tail-1.5 s / silence rule as the historical evaluator."""
    for start in range(0, len(x), 96000):
        clip = x[start:start + 96000]
        if len(clip) >= 24000 and float(np.sqrt(np.mean(clip * clip))) >= 1e-3:
            yield start, clip


class Evaluators:
    def __init__(self) -> None:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(WESPEAKER), sess_options=options,
                                            providers=['CPUExecutionProvider'])
        model = UTMOS22Strong()
        model.load_state_dict(torch.load(str(UTMOS_WEIGHT), map_location='cpu', weights_only=True))
        self.utmos = model.eval()
        self.whisper = None

    def wespeaker(self, x: np.ndarray) -> tuple[np.ndarray, list[dict]]:
        vectors, weights, records = [], [], []
        for position, clip in chunks(x):
            normalized = clip * 0.04 / max(float(np.sqrt(np.mean(clip * clip))), 1e-8)
            feat = torchaudio.compliance.kaldi.fbank(
                torch.from_numpy(normalized * 32768).unsqueeze(0).float(),
                num_mel_bins=80, frame_length=25, frame_shift=10, sample_frequency=16000,
                window_type='hamming', dither=0.0)
            feat = (feat - feat.mean(dim=0)).unsqueeze(0).numpy().astype('float32')
            vector = self.session.run(None, {'feats': feat})[0][0]
            vector = vector / max(float(np.linalg.norm(vector)), 1e-9)
            if not np.isfinite(vector).all():
                raise RuntimeError('Non-finite speaker embedding')
            vectors.append(vector)
            weights.append(len(clip))
            records.append({'start_seconds': position / 16000, 'seconds': len(clip) / 16000})
        if not vectors:
            raise RuntimeError('No valid speaker segment')
        mean = np.average(vectors, axis=0, weights=weights).astype('float64')
        return mean / np.linalg.norm(mean), records

    def naturalness(self, x: np.ndarray) -> float:
        scores, weights = [], []
        for _, clip in chunks(x):
            normalized = clip * 0.04 / max(float(np.sqrt(np.mean(clip * clip))), 1e-8)
            with torch.inference_mode():
                score = float(self.utmos(torch.from_numpy(normalized).unsqueeze(0).float(), 16000).item())
            if not np.isfinite(score):
                raise RuntimeError('Non-finite UTMOS score')
            scores.append(score)
            weights.append(len(clip))
        if not scores:
            raise RuntimeError('No valid naturalness segment')
        return float(np.average(scores, weights=weights))

    def transcribe(self, x: np.ndarray) -> str | None:
        if self.whisper is None:
            if WHISPER_SNAPSHOT is None:
                raise RuntimeError('whisper-small snapshot not found in the offline cache')
            from transformers import WhisperForConditionalGeneration, WhisperProcessor
            # The archived cache has no refs/, so resolve the snapshot directory directly.
            processor = WhisperProcessor.from_pretrained(str(WHISPER_SNAPSHOT), local_files_only=True)
            model = WhisperForConditionalGeneration.from_pretrained(str(WHISPER_SNAPSHOT),
                                                                    local_files_only=True).eval()
            self.whisper = (processor, model)
        processor, model = self.whisper
        inputs = processor(x.astype('float32'), sampling_rate=16000, return_tensors='pt')
        with torch.inference_mode():
            ids = model.generate(inputs.input_features, language='zh', task='transcribe',
                                 max_new_tokens=256)
        return processor.batch_decode(ids, skip_special_tokens=True)[0].strip()


def f0_stats(x: np.ndarray) -> dict:
    frame_period = 10.0
    f0, times = pyworld.dio(x, 16000, f0_floor=71.0, f0_ceil=800.0, frame_period=frame_period)
    f0 = pyworld.stonemask(x, f0, times, 16000)
    voiced = f0[f0 > 0]
    if voiced.size == 0:
        return {'voiced_fraction': 0.0}
    return {
        'seconds': len(x) / 16000,
        'voiced_fraction': float(voiced.size / f0.size),
        'f0_median_hz': float(np.median(voiced)),
        'f0_p10_hz': float(np.percentile(voiced, 10)),
        'f0_p90_hz': float(np.percentile(voiced, 90)),
    }


def band_ratios(x: np.ndarray) -> dict:
    """Coarse spectral balance of voiced-energy frames; descriptive only."""
    spectrum = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    freqs = np.fft.rfftfreq(len(x), 1 / 16000)

    def band(low, high):
        return float(spectrum[(freqs >= low) & (freqs < high)].sum())

    low = band(80, 400)
    mid = band(1000, 4000)
    total = band(80, 8000) + 1e-18
    return {
        'low_to_mid_db': float(10 * np.log10((low + 1e-18) / (mid + 1e-18))),
        'low_share_db': float(10 * np.log10((low + 1e-18) / total)),
        'rms': float(np.sqrt(np.mean(x * x))),
    }


def normalise_text(text: str) -> str:
    drop = set('，。、！？；：""''（）《》 \t\n,.!?;:"\'()')
    return ''.join(ch for ch in text if ch not in drop).lower()


def cer(reference: str, hypothesis: str) -> dict:
    ref, hyp = normalise_text(reference), normalise_text(hypothesis)
    if not ref:
        return {'reference_chars': 0, 'insertions': 0, 'deletions': 0,
                'substitutions': 0, 'distance': 0, 'cer': None}
    previous = list(range(len(hyp) + 1))
    for i, rch in enumerate(ref, 1):
        current = [i]
        for j, hch in enumerate(hyp, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (rch != hch)))
        previous = current
    return {'reference_chars': len(ref), 'hypothesis_chars': len(hyp),
            'distance': previous[-1], 'cer': previous[-1] / len(ref)}


def main() -> None:
    started = time.time()
    if sha256(SEED_OUTPUT) != SEED_OUTPUT_SHA:
        raise SystemExit('Seed reference output changed; refusing to audit a different file')
    evaluators = Evaluators()

    source_window = load16(BASE / 'holdout.wav', start=2.68, seconds=4.8)
    target_window = load16(VOICE / HELD_OUT_TRACK, start=11.0, seconds=4.8)
    old_window = load16(BASE / 'hybrid_comparison/old_fixed.wav', start=2.68, seconds=4.8)
    seed_window = load16(SEED_OUTPUT, start=1.0, seconds=4.8)
    for name, window in (('source', source_window), ('target', target_window),
                         ('world_old', old_window), ('seed30', seed_window)):
        if len(window) != 76800 or not np.isfinite(window).all():
            raise SystemExit(f'Aligned window invalid: {name}')

    items = [
        {'label': 'source_dev_full', 'role': 'source_speaker_full_session',
         'path': BASE / 'holdout.wav', 'audio': load16(BASE / 'holdout.wav')},
        {'label': 'source_dev_window', 'role': 'source_speaker_aligned_window',
         'path': BASE / 'holdout.wav', 'window': '2.68s+4.8s', 'audio': source_window},
        {'label': 'target_track9_window', 'role': 'target_held_out_track_aligned_window',
         'path': VOICE / HELD_OUT_TRACK, 'window': '11.0s+4.8s', 'audio': target_window},
        {'label': 'world_old_full', 'role': 'world_old_recipe_full_output',
         'path': BASE / 'hybrid_comparison/old_fixed.wav', 'audio': load16(BASE / 'hybrid_comparison/old_fixed.wav')},
        {'label': 'world_old_window', 'role': 'world_old_recipe_aligned_window',
         'path': BASE / 'hybrid_comparison/old_fixed.wav', 'window': '2.68s+4.8s', 'audio': old_window},
        {'label': 'seed30_full', 'role': 'seed_reference_full_output',
         'path': SEED_OUTPUT, 'audio': load16(SEED_OUTPUT)},
        {'label': 'seed30_window', 'role': 'seed_reference_aligned_window',
         'path': SEED_OUTPUT, 'window': '1.0s+4.8s', 'audio': seed_window},
    ]

    target_vectors = {}
    for name in TARGET_TRACKS:
        label = 'target_' + name.split()[1].split('(')[0]
        audio = load16(VOICE / name)
        vector, segments = evaluators.wespeaker(audio)
        target_vectors[label] = vector
        items.append({'label': label, 'role': 'target_reference_track',
                      'path': VOICE / name, 'audio': audio, 'embedding': vector,
                      'segments': segments})

    matrix = np.stack([target_vectors[k] for k in sorted(target_vectors)])
    centroid = matrix.mean(axis=0)
    centroid /= np.linalg.norm(centroid)
    pairwise = [float(matrix[i] @ matrix[j]) for i in range(len(matrix))
                for j in range(i + 1, len(matrix))]

    source_reference, _ = evaluators.wespeaker(source_window)

    records = []
    for item in items:
        audio = item.pop('audio')
        vector = item.pop('embedding', None)
        segments = item.pop('segments', None)
        if vector is None:
            vector, segments = evaluators.wespeaker(audio)
        record = dict(item)
        record['path'] = str(Path(item['path']).relative_to(ROOT)).replace('\\', '/')
        record.update({'sha256': sha256(item['path']), 'segments': segments})
        record['wespeaker_cosine_to_target_centroid'] = float(vector @ centroid)
        record['wespeaker_cli_scaled_cosine'] = float((vector @ centroid + 1) / 2)
        record['wespeaker_cosine_to_source_window'] = float(vector @ source_reference)
        record['utmos_predicted'] = evaluators.naturalness(audio)
        record.update(f0_stats(audio))
        record.update(band_ratios(audio))
        records.append(record)
        print(f"{record['label']:<24} id={record['wespeaker_cosine_to_target_centroid']:.4f} "
              f"src={record['wespeaker_cosine_to_source_window']:.4f} "
              f"utmos={record['utmos_predicted']:.3f} "
              f"f0={record.get('f0_median_hz', float('nan')):.1f}Hz", flush=True)

    transcripts, asr_error = {}, None
    try:
        for label, window in (('source_dev_window', source_window), ('target_track9_window', target_window),
                              ('world_old_window', old_window), ('seed30_window', seed_window)):
            transcripts[label] = evaluators.transcribe(window)
            print(f'ASR {label}: {transcripts[label]}', flush=True)
        asr_error = {
            'world_old_vs_source': cer(transcripts['source_dev_window'], transcripts['world_old_window']),
            'seed30_vs_source': cer(transcripts['source_dev_window'], transcripts['seed30_window']),
            'seed30_vs_world_old': cer(transcripts['world_old_window'], transcripts['seed30_window']),
            'note': 'ASR-relative comparison of transcripts, not ground-truth content verification',
        }
    except Exception as error:  # noqa: BLE001 - reported, not hidden
        asr_error = {'status': 'unavailable', 'error': f'{type(error).__name__}: {error}'}

    def pick(label):
        return next(r for r in records if r['label'] == label)

    source_id = pick('source_dev_window')['wespeaker_cosine_to_target_centroid']
    world_id = pick('world_old_window')['wespeaker_cosine_to_target_centroid']
    seed_id = pick('seed30_window')['wespeaker_cosine_to_target_centroid']
    world_nat = pick('world_old_window')['utmos_predicted']
    seed_nat = pick('seed30_window')['utmos_predicted']

    report = {
        'kind': 'seed_reference_offline_audit',
        'date': '2026-10-16',
        'protocol': PROTOCOL,
        'read_only': True, 'audio_generated': False, 'audio_uploaded': False,
        'board_touched': False, 'played': False,
        'assets': {
            'speaker_evaluator': {'path': str(WESPEAKER.relative_to(ROOT)), 'sha256': sha256(WESPEAKER)},
            'utmos_weights': {'path': str(UTMOS_WEIGHT.relative_to(ROOT)), 'sha256': sha256(UTMOS_WEIGHT)},
            'asr_model': 'openai/whisper-small (offline snapshot under 交接/核心材料)',
            'seed_output_sha256': SEED_OUTPUT_SHA,
        },
        'target_pairwise_cosines': pairwise,
        'target_pairwise_mean': float(np.mean(pairwise)),
        'target_pairwise_min': float(np.min(pairwise)),
        'aligned_window_comparison': {
            'source_identity_cosine': source_id,
            'world_old_identity_cosine': world_id,
            'seed30_identity_cosine': seed_id,
            'seed30_minus_world_old_identity': seed_id - world_id,
            'world_old_utmos': world_nat,
            'seed30_utmos': seed_nat,
            'seed30_minus_world_old_utmos': seed_nat - world_nat,
        },
        'asr_content_comparison': asr_error,
        'transcripts': transcripts,
        'files': records,
        'elapsed_seconds': time.time() - started,
        'speaker_identity_accepted': False, 'naturalness_accepted': False,
        'content_verified': False, 'multiple_speakers_verified': False,
        'board_realtime_accepted': False,
        'limitations': [
            'Track 8 is the prompt the Seed reference was conditioned on and is also part of the target centroid, so Seed identity scores are optimistic.',
            'Single source speaker, single session, existing development utterance; not a blind or independent evaluation.',
            'UTMOS is predicted naturalness trained on other domains; Mandarin suitability is uncalibrated and it is not identity.',
            'Speaker cosine is a verification-model score, not percent likeness, and the target tracks score high partly by construction.',
            'Content comparison uses Whisper transcripts of both sides; ASR errors are correlated and this is not ground-truth content verification.',
            'Aligned windows share the same 4.8 s span as the listening gate; level normalisation differs from user playback conditions.',
            'No listening, no Zynq deployment, no measure of 7020 feasibility; RTF numbers come from the earlier reference report.',
        ],
    }
    dest = ROOT / 'report/seed_reference_audit_20261016.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('COMPLETE ' + str(dest), flush=True)


if __name__ == '__main__':
    main()
