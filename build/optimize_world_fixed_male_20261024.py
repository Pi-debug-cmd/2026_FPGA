"""Tune a source-specific WORLD mapping without looking at the locked holdout.

Selection uses Fixed-Male recording 4 only.  After the candidate is frozen, the
script evaluates recording 5 exactly once.  Recordings 1-3 build the source
profile; target Tracks 5-8 build the target profile; Track 9 remains unused by
selection and is reported only as an independent target-speaker check.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from math import gcd
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.reference.world_fixed_male_mapping import (  # noqa: E402
    blend_aperiodicity,
    map_log_f0,
    normalized_log_shape,
    targetize_spectra,
    warp_bins,
)

RATE = 16000
FFT_SIZE = 1024
FRAME_PERIOD = 10.0


@dataclass(frozen=True)
class Candidate:
    name: str
    warp: float
    strength: float
    detail: float
    clamp_db: float
    ap_mix: float
    pitch_strength: float = 1.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def bootstrap(asset_root: Path):
    generated = asset_root / 'build/generated'
    speechmos = next((generated / 'eval_sources_20261016').glob('SpeechMOS-*'))
    for extra in (generated / 'eval_deps_20261016', generated / 'world_deps',
                  generated / 'llvc_cpu_deps', generated / 'seed_audio_deps',
                  generated / 'seed_cpu_deps', speechmos):
        sys.path.insert(0, str(extra))
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
    module_path = asset_root / 'build/audit_seed_reference_20261016.py'
    spec = importlib.util.spec_from_file_location('world_fixed_male_audit', module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load evaluator module: {module_path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load16(path: Path, sf, resample_poly) -> np.ndarray:
    audio, rate = sf.read(str(path), dtype='float64', always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if rate != RATE:
        common = gcd(int(rate), RATE)
        audio = resample_poly(audio, RATE // common, int(rate) // common)
    return np.ascontiguousarray(audio, dtype=np.float64)


def analyse(audio: np.ndarray, pyworld):
    f0, times = pyworld.dio(audio, RATE, f0_floor=75.0, f0_ceil=400.0,
                            channels_in_octave=2.0, frame_period=FRAME_PERIOD,
                            speed=4, allowed_range=0.1)
    f0 = pyworld.stonemask(audio, f0, times, RATE)
    centers = np.rint(times * RATE).astype(int)
    left = np.maximum(0, centers - 320)
    right = np.minimum(len(audio), centers + 320)
    cumulative = np.r_[0.0, np.cumsum(audio * audio)]
    power = (cumulative[right] - cumulative[left]) / np.maximum(1, right - left)
    f0[power < 10 ** -4.5] = 0.0
    sp = pyworld.cheaptrick(audio, f0, times, RATE, q1=-0.15,
                            f0_floor=75.0, fft_size=FFT_SIZE)
    ap = pyworld.d4c(audio, f0, times, RATE, threshold=0.85, fft_size=FFT_SIZE)
    return f0, np.maximum(sp, 1e-12), np.clip(ap, 0.001, 0.999999999999)


def f0_stats(values: list[np.ndarray]) -> tuple[float, float, float]:
    voiced = np.concatenate([value[value > 0] for value in values])
    if len(voiced) < 300:
        raise RuntimeError(f'too few voiced profile frames: {len(voiced)}')
    return tuple(float(v) for v in np.percentile(voiced, [10, 50, 90]))


def best_warp(source_shape: np.ndarray, target_shape: np.ndarray) -> float:
    low = int(np.ceil(300 / (RATE / FFT_SIZE)))
    high = int(np.floor(4000 / (RATE / FFT_SIZE)))
    best = (float('inf'), 1.0)
    for factor in np.arange(0.85, 1.351, 0.025):
        delta = target_shape[low:high + 1] - warp_bins(source_shape, float(factor))[low:high + 1]
        delta -= delta.mean()
        best = min(best, (float(np.mean(delta * delta)), float(factor)))
    return best[1]


def synthesize(analysis, candidate: Candidate, profile: dict, pyworld) -> np.ndarray:
    audio, f0, spectra, ap = analysis
    voiced = f0 > 0
    mapped_f0 = map_log_f0(f0, profile['source_f0'], profile['target_f0'],
                           candidate.pitch_strength)
    mapped_sp = targetize_spectra(
        spectra, voiced, profile['source_shape'], profile['target_shape'],
        candidate.warp, candidate.strength, candidate.detail, candidate.clamp_db)
    mapped_ap = blend_aperiodicity(ap, profile['target_ap'], voiced, candidate.ap_mix)
    output = pyworld.synthesize(mapped_f0, np.ascontiguousarray(mapped_sp),
                                np.ascontiguousarray(mapped_ap), RATE,
                                frame_period=FRAME_PERIOD)[:len(audio)]
    output = np.asarray(output, dtype=np.float64)
    if not np.isfinite(output).all():
        raise RuntimeError(f'non-finite output for {candidate.name}')
    peak = float(np.max(np.abs(output)))
    if peak > 0.98:
        output *= 0.98 / peak
    return output


def candidate_grid(warp: float) -> list[Candidate]:
    candidates = [Candidate('a1_like', warp, 0.65, 1.0, 3.0, 0.0)]
    for strength in (0.8, 1.0, 1.2):
        for detail in (0.55, 0.75, 1.0):
            for ap_mix in (0.0, 0.35):
                name = f's{strength:.2f}_d{detail:.2f}_ap{ap_mix:.2f}'
                candidates.append(Candidate(name, warp, strength, detail, 9.0, ap_mix))
    for factor in sorted(set((1.0, 1.1, 1.2, round(warp, 3)))):
        candidates.append(Candidate(f'warp{factor:.3f}', factor, 1.0, 0.75, 9.0, 0.0))
    return candidates


def evaluate_fast(audio: np.ndarray, source_vector: np.ndarray, target_centroid: np.ndarray,
                  evaluators) -> dict:
    vector, segments = evaluators.wespeaker(audio)
    return {
        'identity': float(vector @ target_centroid),
        'leakage': float(vector @ source_vector),
        'utmos': evaluators.naturalness(audio),
        'segments': segments,
    }


def score(row: dict) -> float:
    # Equalized ratios prevent identity alone from selecting the old A3 failure mode.
    identity = min(row['identity'] / 0.45, 1.25)
    leakage = min(0.10 / max(row['leakage'], 0.01), 1.25)
    naturalness = min(row['utmos'] / 2.30, 1.25)
    return float(min(identity, leakage, naturalness) + 0.15 * (identity + leakage + naturalness))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset-root', type=Path, required=True,
                        help='Existing project root that contains ignored evaluator dependencies')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'build/generated/world_fixed_male_20261024')
    args = parser.parse_args()
    asset_root = args.asset_root.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    audit = bootstrap(asset_root)
    import pyworld  # noqa: E402
    import soundfile as sf  # noqa: E402
    from scipy.signal import resample_poly  # noqa: E402

    source_dir = ROOT / '人物音频资料/男声'
    target_dir = ROOT / '人物音频资料/女声'
    paths = {
        'source_train': [source_dir / f'标准录音 {index}.wav' for index in (1, 2, 3)],
        'source_validation': source_dir / '标准录音 4.wav',
        'source_holdout': source_dir / '标准录音 5.wav',
        'target_train': [target_dir / f'Track {index}.wav' for index in (5, 6, 7, 8)],
        'target_holdout': target_dir / 'Track 9.wav',
    }
    input_hashes = {str(path.relative_to(ROOT)).replace('\\', '/'): sha256(path)
                    for value in paths.values()
                    for path in (value if isinstance(value, list) else [value])}

    source_train = [(audio := load16(path, sf, resample_poly), *analyse(audio, pyworld))
                    for path in paths['source_train']]
    target_train = [(audio := load16(path, sf, resample_poly), *analyse(audio, pyworld))
                    for path in paths['target_train']]
    validation_audio = load16(paths['source_validation'], sf, resample_poly)
    validation = (validation_audio, *analyse(validation_audio, pyworld))

    source_spectra = np.concatenate([row[2] for row in source_train])
    source_voiced = np.concatenate([row[1] > 0 for row in source_train])
    target_spectra = np.concatenate([row[2] for row in target_train])
    target_voiced = np.concatenate([row[1] > 0 for row in target_train])
    source_shape = normalized_log_shape(source_spectra, source_voiced)
    target_shape = normalized_log_shape(target_spectra, target_voiced)
    target_ap = np.mean(np.concatenate([row[3][row[1] > 0] for row in target_train]), axis=0)
    profile = {
        'source_f0': f0_stats([row[1] for row in source_train]),
        'target_f0': f0_stats([row[1] for row in target_train]),
        'source_shape': source_shape,
        'target_shape': target_shape,
        'target_ap': target_ap,
    }
    fitted_warp = best_warp(source_shape, target_shape)

    evaluators = audit.Evaluators()
    target_vectors = [evaluators.wespeaker(row[0])[0] for row in target_train]
    target_centroid = np.mean(np.stack(target_vectors), axis=0)
    target_centroid /= np.linalg.norm(target_centroid)
    target_holdout_audio = load16(paths['target_holdout'], sf, resample_poly)
    target_holdout_identity = float(evaluators.wespeaker(target_holdout_audio)[0] @ target_centroid)
    validation_source_vector = evaluators.wespeaker(validation_audio)[0]
    validation_source_text = evaluators.transcribe(validation_audio)

    rows = []
    for candidate in candidate_grid(fitted_warp):
        audio = synthesize(validation, candidate, profile, pyworld)
        path = output_dir / f'validation_{candidate.name}.wav'
        sf.write(str(path), audio.astype(np.float32), RATE, subtype='PCM_16')
        metrics = evaluate_fast(audio, validation_source_vector, target_centroid, evaluators)
        row = {'candidate': asdict(candidate), 'path': str(path), **metrics}
        row['selection_score'] = score(row)
        rows.append(row)
        print(f"FAST {candidate.name:<20} id={row['identity']:.3f} leak={row['leakage']:.3f} "
              f"utmos={row['utmos']:.3f} score={row['selection_score']:.3f}", flush=True)

    # Run Whisper only on the best balanced candidates plus the A1-like control.
    ranked = sorted(rows, key=lambda item: item['selection_score'], reverse=True)
    cer_rows = []
    selected_for_cer = {row['candidate']['name'] for row in ranked[:5]} | {'a1_like'}
    for row in rows:
        if row['candidate']['name'] not in selected_for_cer:
            continue
        audio = load16(Path(row['path']), sf, resample_poly)
        text = evaluators.transcribe(audio)
        row['asr_text'] = text
        row['cer'] = audit.cer(validation_source_text, text)['cer']
        cer_rows.append(row)
        print(f"CER  {row['candidate']['name']:<20} cer={row['cer']:.3f} text={text}", flush=True)

    eligible = [row for row in cer_rows if row['cer'] is not None and row['cer'] <= 0.15]
    frozen = max(eligible or cer_rows, key=lambda item: item['selection_score'])
    frozen_candidate = Candidate(**frozen['candidate'])

    # Locked holdout is first loaded and evaluated only after the candidate is frozen.
    holdout_audio = load16(paths['source_holdout'], sf, resample_poly)
    holdout = (holdout_audio, *analyse(holdout_audio, pyworld))
    holdout_source_vector = evaluators.wespeaker(holdout_audio)[0]
    holdout_source_text = evaluators.transcribe(holdout_audio)
    holdout_output = synthesize(holdout, frozen_candidate, profile, pyworld)
    holdout_path = output_dir / f'holdout_frozen_{frozen_candidate.name}.wav'
    sf.write(str(holdout_path), holdout_output.astype(np.float32), RATE, subtype='PCM_16')
    holdout_metrics = evaluate_fast(holdout_output, holdout_source_vector,
                                    target_centroid, evaluators)
    holdout_text = evaluators.transcribe(holdout_output)
    holdout_metrics.update({
        'asr_text': holdout_text,
        'source_asr_text': holdout_source_text,
        'cer': audit.cer(holdout_source_text, holdout_text)['cer'],
        'path': str(holdout_path),
    })
    gates = {
        'identity_ge_0_45': holdout_metrics['identity'] >= 0.45,
        'leakage_le_0_10': holdout_metrics['leakage'] <= 0.10,
        'utmos_ge_2_30': holdout_metrics['utmos'] >= 2.30,
        'cer_le_0_15': holdout_metrics['cer'] is not None and holdout_metrics['cer'] <= 0.15,
    }
    report = {
        'kind': 'world_fixed_male_source_specific_sweep',
        'date': '2026-10-24',
        'task': 'PS-20261021-10',
        'protocol': audit.PROTOCOL + ' + whole-utterance Fixed-Male 1-3/4/5 split',
        'input_hashes': input_hashes,
        'split': {
            'source_profile': ['标准录音 1.wav', '标准录音 2.wav', '标准录音 3.wav'],
            'selection_only': '标准录音 4.wav',
            'locked_holdout_after_freeze': '标准录音 5.wav',
            'target_profile': ['Track 5.wav', 'Track 6.wav', 'Track 7.wav', 'Track 8.wav'],
            'target_holdout_not_used_for_selection': 'Track 9.wav',
        },
        'profile': {
            'source_f0_p10_median_p90': profile['source_f0'],
            'target_f0_p10_median_p90': profile['target_f0'],
            'fitted_warp': fitted_warp,
            'target_track9_identity_to_train_centroid': target_holdout_identity,
        },
        'validation_source_asr_text': validation_source_text,
        'validation_candidates': rows,
        'frozen_candidate': asdict(frozen_candidate),
        'holdout': holdout_metrics,
        'gates': gates,
        'all_objective_gates_pass': all(gates.values()),
        'elapsed_seconds': round(time.time() - started, 1),
        'limitations': [
            'This is an offline whole-utterance WORLD experiment, not the streaming v23 implementation.',
            'UTMOS is an out-of-domain predictor and objective gates do not replace listening.',
            'The five source files are independent files but cross-date session separation is unproven.',
            'No board, Vivado, PL, live microphone, playback, or user listening was performed.',
        ],
    }
    report_path = output_dir / 'result.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('HOLDOUT', json.dumps({'candidate': frozen_candidate.name, **holdout_metrics,
                                 'gates': gates}, ensure_ascii=False), flush=True)
    print('COMPLETE', report_path, flush=True)


if __name__ == '__main__':
    main()
