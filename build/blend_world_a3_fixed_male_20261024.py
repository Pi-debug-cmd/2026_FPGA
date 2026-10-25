"""Blend the clear WORLD branch with the existing high-identity A3 envelope.

This is a second, independent selection round.  Fixed-Male recording 4 selects
one blend.  Recording 5 is loaded only after the blend coefficient is frozen.
No audio is played and no board state is touched.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from build.optimize_world_fixed_male_20261024 import (  # noqa: E402
    Candidate,
    RATE,
    analyse,
    best_warp,
    bootstrap,
    evaluate_fast,
    f0_stats,
    load16,
    score,
)
from src.reference.world_fixed_male_mapping import (  # noqa: E402
    map_log_f0,
    normalized_log_shape,
    targetize_spectra,
)


def content_tokens(model, audio, torch):
    wav = torch.from_numpy(np.asarray(audio, dtype=np.float32)).view(1, 1, -1)
    with torch.inference_mode():
        if hasattr(model, 'convnet_pre'):
            context = model.convnet_pre.init_ctx_buf(1, wav.device)
            conv_out, _ = model.convnet_pre(wav, context)
            mode = model.convnet_config['skip_connection']
            wav = wav + conv_out if mode == 'add' else wav * conv_out if mode == 'multiply' else conv_out
        padding = (model.L, model.L) if model.lookahead else (0, 0)
        remainder = (-wav.shape[-1]) % model.L
        wav = torch.nn.functional.pad(wav, (0, remainder))
        wav = torch.nn.functional.pad(wav, padding)
        latent = model.in_conv(wav)
        context = model.mask_gen.encoder.init_ctx_buf(1, latent.device)
        encoded, _ = model.mask_gen.encoder(latent, context)
    return encoded[0].transpose(0, 1).contiguous().numpy()


def stack_context(values: np.ndarray, radius: int = 2) -> np.ndarray:
    padded = np.pad(values, ((radius, radius), (0, 0)), mode='edge')
    return np.concatenate([padded[i:i + len(values)] for i in range(2 * radius + 1)], axis=1)


def dct16(values: np.ndarray, dct) -> np.ndarray:
    return dct(values, type=2, norm='ortho')[:16].astype(np.float32)


class ContentNetFactory:
    @staticmethod
    def build(torch, input_dim: int, hidden: int):
        class ContentNet(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.trunk = torch.nn.Sequential(
                    torch.nn.Linear(input_dim, hidden), torch.nn.ReLU(),
                    torch.nn.Linear(hidden, hidden), torch.nn.ReLU())
                self.head = torch.nn.Linear(hidden, 49)

            def forward(self, values):
                output = self.head(self.trunk(values))
                return output[:, :48], output[:, 48]
        return ContentNet()


def a3_parameters(audio: np.ndarray, analysed, assets: dict) -> tuple[np.ndarray, np.ndarray]:
    torch = assets['torch']
    f0, spectra, _ = analysed
    voiced = f0 > 0
    content = content_tokens(assets['llvc'], audio, torch)
    frame_count = content.shape[0] // 10
    content = np.stack([content[index * 10:(index + 1) * 10].mean(axis=0)
                        for index in range(frame_count)])
    content = (content - assets['content_mean']) @ assets['content_proj']
    if len(content) < len(spectra):
        content = np.concatenate([content, np.repeat(content[-1:], len(spectra) - len(content), axis=0)])
    content = stack_context(content[:len(spectra)])
    logmel = np.log(np.maximum(spectra @ assets['mel'].T, 1e-10))
    acoustic = np.clip(logmel - logmel[voiced].mean(axis=0), -6.0, 6.0)
    logf0 = np.log(np.maximum(f0, 1e-6))
    median = float(np.median(logf0[voiced]))
    spread = max(float(np.percentile(logf0[voiced], 90) - np.percentile(logf0[voiced], 10)), 0.05)
    zscore = np.clip((logf0 - median) / spread, -4.0, 4.0)
    zscore[~voiced] = 0.0
    extras = np.stack([zscore, np.full(len(f0), median), np.full(len(f0), spread),
                       np.full(len(f0), float(voiced.mean()))], axis=1)
    features = np.concatenate([content, acoustic, extras,
                               np.tile(assets['profile_vector'], (len(f0), 1))], axis=1).astype(np.float32)
    with torch.inference_mode():
        residual, predicted_f0 = assets['model'](torch.from_numpy(features))
    logmel_target = assets['profile']['mel_mu'][None, :] + residual.numpy()
    spectra_target = np.maximum(np.exp(logmel_target) @ assets['mel_pinv'].T, 1e-12)
    mapped_f0 = f0.copy()
    mapped_f0[voiced] = np.clip(np.exp(predicted_f0.numpy()[voiced]), 75.0, 400.0)
    return mapped_f0, spectra_target


def prepare_branches(audio: np.ndarray, analysed, world_profile: dict,
                     world_candidate: Candidate, assets: dict):
    f0, spectra, ap = analysed
    voiced = f0 > 0
    world_f0 = map_log_f0(f0, world_profile['source_f0'], world_profile['target_f0'], 1.0)
    world_sp = targetize_spectra(spectra, voiced, world_profile['source_shape'],
                                 world_profile['target_shape'], world_candidate.warp,
                                 world_candidate.strength, world_candidate.detail,
                                 world_candidate.clamp_db)
    a3_f0, a3_sp = a3_parameters(audio, analysed, assets)
    return len(audio), voiced, world_f0, world_sp, a3_f0, a3_sp, ap


def synthesize_blend(branches, alpha_mid: float, alpha_high: float,
                     pitch_alpha: float, pyworld) -> np.ndarray:
    output_length, voiced, world_f0, world_sp, a3_f0, a3_sp, ap = branches
    mixed_f0 = world_f0.copy()
    mixed_f0[voiced] = np.exp((1 - pitch_alpha) * np.log(world_f0[voiced])
                              + pitch_alpha * np.log(a3_f0[voiced]))
    frequencies = np.linspace(0.0, RATE / 2, world_sp.shape[1])
    alpha_curve = np.full_like(frequencies, alpha_mid)
    transition = np.clip((frequencies - 3500.0) / 1500.0, 0.0, 1.0)
    alpha_curve = alpha_mid + transition * (alpha_high - alpha_mid)
    mixed_sp = np.exp((1 - alpha_curve[None, :]) * np.log(world_sp)
                      + alpha_curve[None, :] * np.log(a3_sp))
    output = pyworld.synthesize(mixed_f0, np.ascontiguousarray(mixed_sp),
                                np.ascontiguousarray(ap), RATE,
                                frame_period=10.0)[:output_length]
    output = np.asarray(output, dtype=np.float64)
    peak = float(np.max(np.abs(output)))
    if peak > 0.98:
        output *= 0.98 / peak
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'build/generated/world_a3_blend_20261024')
    args = parser.parse_args()
    asset_root = args.asset_root.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    audit = bootstrap(asset_root)
    import pyworld
    import soundfile as sf
    import torch
    from scipy.fftpack import dct
    from scipy.signal import resample_poly
    sys.path.insert(0, str(asset_root / 'build'))
    llvc_host_model = importlib.import_module('llvc_host_model')
    torch.set_num_threads(4)

    a3_dir = asset_root / 'build/generated/a3_neural'
    frontend = np.load(a3_dir / 'frontend.npz')
    a3_profile = dict(np.load(a3_dir / 'profile_t5_8_20s.npz'))
    pca = np.load(a3_dir / 'content_pca.npz')
    checkpoint = torch.load(a3_dir / 'a3_content.pt', map_location='cpu', weights_only=False)
    model = ContentNetFactory.build(torch, checkpoint['in_dim'], checkpoint['hidden'])
    model.load_state_dict(checkpoint['state_dict'])
    model.eval()
    llvc, _, _, _ = llvc_host_model.load_v2()
    llvc.eval()
    profile_vector = np.concatenate([
        np.array([a3_profile['f0_log_p10'], a3_profile['f0_log_med'],
                  a3_profile['f0_log_p90'], a3_profile['f0_log_std']], dtype=np.float32),
        dct16(a3_profile['mel_mu'], dct),
    ])
    assets = {'torch': torch, 'llvc': llvc, 'model': model, 'profile': a3_profile,
              'mel': frontend['mel'], 'mel_pinv': np.linalg.pinv(frontend['mel']),
              'content_mean': pca['mean'], 'content_proj': pca['proj'],
              'profile_vector': profile_vector}

    source_dir = ROOT / '人物音频资料/男声'
    target_dir = ROOT / '人物音频资料/女声'
    source_train_audio = [load16(source_dir / f'标准录音 {i}.wav', sf, resample_poly) for i in (1, 2, 3)]
    target_train_audio = [load16(target_dir / f'Track {i}.wav', sf, resample_poly) for i in (5, 6, 7, 8)]
    source_train = [(audio, *analyse(audio, pyworld)) for audio in source_train_audio]
    target_train = [(audio, *analyse(audio, pyworld)) for audio in target_train_audio]
    source_spectra = np.concatenate([row[2] for row in source_train])
    source_voiced = np.concatenate([row[1] > 0 for row in source_train])
    target_spectra = np.concatenate([row[2] for row in target_train])
    target_voiced = np.concatenate([row[1] > 0 for row in target_train])
    source_shape = normalized_log_shape(source_spectra, source_voiced)
    target_shape = normalized_log_shape(target_spectra, target_voiced)
    fitted_warp = best_warp(source_shape, target_shape)
    world_profile = {
        'source_f0': f0_stats([row[1] for row in source_train]),
        'target_f0': f0_stats([row[1] for row in target_train]),
        'source_shape': source_shape, 'target_shape': target_shape,
        'target_ap': np.mean(np.concatenate([row[3][row[1] > 0] for row in target_train]), axis=0),
    }
    world_candidate = Candidate('a1_like', fitted_warp, 0.65, 1.0, 3.0, 0.0)

    evaluators = audit.Evaluators()
    target_vectors = [evaluators.wespeaker(audio)[0] for audio in target_train_audio]
    centroid = np.mean(np.stack(target_vectors), axis=0)
    centroid /= np.linalg.norm(centroid)

    validation_audio = load16(source_dir / '标准录音 4.wav', sf, resample_poly)
    validation_analysis = analyse(validation_audio, pyworld)
    validation_vector = evaluators.wespeaker(validation_audio)[0]
    validation_text = evaluators.transcribe(validation_audio)
    validation_branches = prepare_branches(validation_audio, validation_analysis,
                                           world_profile, world_candidate, assets)
    blend_configs = []
    for alpha in (0.0, 0.3, 0.5, 0.6, 0.8, 1.0):
        blend_configs.append({'name': f'flat_{alpha:.2f}', 'alpha_mid': alpha,
                              'alpha_high': alpha, 'pitch_alpha': alpha})
    for alpha_mid in (0.5, 0.6, 0.7, 0.8):
        for alpha_high in (0.0, 0.15, 0.30):
            blend_configs.append({'name': f'band_m{alpha_mid:.2f}_h{alpha_high:.2f}',
                                  'alpha_mid': alpha_mid, 'alpha_high': alpha_high,
                                  'pitch_alpha': min(alpha_mid, 0.6)})
    rows = []
    for config in blend_configs:
        output = synthesize_blend(validation_branches, config['alpha_mid'],
                                  config['alpha_high'], config['pitch_alpha'], pyworld)
        path = output_dir / f"validation_{config['name']}.wav"
        sf.write(str(path), output.astype(np.float32), RATE, subtype='PCM_16')
        row = {'blend': config, 'path': str(path),
               **evaluate_fast(output, validation_vector, centroid, evaluators)}
        row['selection_score'] = score(row)
        rows.append(row)
        print(f"FAST {config['name']:<20} id={row['identity']:.3f} leak={row['leakage']:.3f} "
              f"utmos={row['utmos']:.3f} score={row['selection_score']:.3f}", flush=True)

    ranked = sorted(rows, key=lambda item: item['selection_score'], reverse=True)
    selected = {row['blend']['name'] for row in ranked[:7]} | {'flat_0.00', 'flat_1.00'}
    for row in rows:
        if row['blend']['name'] not in selected:
            continue
        output = load16(Path(row['path']), sf, resample_poly)
        text = evaluators.transcribe(output)
        row['asr_text'] = text
        row['cer'] = audit.cer(validation_text, text)['cer']
        print(f"CER {row['blend']['name']:<20} cer={row['cer']:.3f}", flush=True)
    assessed = [row for row in rows if 'cer' in row and row['cer'] <= 0.15]
    frozen = max(assessed or [row for row in rows if 'cer' in row],
                 key=lambda item: item['selection_score'])
    frozen_blend = frozen['blend']

    holdout_audio = load16(source_dir / '标准录音 5.wav', sf, resample_poly)
    holdout_analysis = analyse(holdout_audio, pyworld)
    holdout_vector = evaluators.wespeaker(holdout_audio)[0]
    holdout_text = evaluators.transcribe(holdout_audio)
    holdout_branches = prepare_branches(holdout_audio, holdout_analysis, world_profile,
                                        world_candidate, assets)
    holdout_output = synthesize_blend(holdout_branches, frozen_blend['alpha_mid'],
                                      frozen_blend['alpha_high'],
                                      frozen_blend['pitch_alpha'], pyworld)
    holdout_path = output_dir / f"holdout_frozen_{frozen_blend['name']}.wav"
    sf.write(str(holdout_path), holdout_output.astype(np.float32), RATE, subtype='PCM_16')
    holdout = evaluate_fast(holdout_output, holdout_vector, centroid, evaluators)
    holdout_output_text = evaluators.transcribe(holdout_output)
    holdout.update({'cer': audit.cer(holdout_text, holdout_output_text)['cer'],
                    'source_asr_text': holdout_text, 'asr_text': holdout_output_text,
                    'path': str(holdout_path)})
    gates = {'identity_ge_0_45': holdout['identity'] >= 0.45,
             'leakage_le_0_10': holdout['leakage'] <= 0.10,
             'utmos_ge_2_30': holdout['utmos'] >= 2.30,
             'cer_le_0_15': holdout['cer'] is not None and holdout['cer'] <= 0.15}
    report = {
        'kind': 'world_a3_parameter_blend_fixed_male', 'date': '2026-10-24',
        'task': 'PS-20261021-10',
        'protocol': audit.PROTOCOL + ' + Fixed-Male 1-3/4/5 split',
        'world_branch': asdict(world_candidate),
        'a3_branch': {'checkpoint': str(a3_dir / 'a3_content.pt'),
                      'checkpoint_note': 'existing frozen high-identity envelope model'},
        'validation_source_asr_text': validation_text,
        'validation_candidates': rows,
        'frozen_blend': frozen_blend,
        'holdout': holdout,
        'gates': gates,
        'all_objective_gates_pass': all(gates.values()),
        'elapsed_seconds': round(time.time() - started, 1),
        'limitations': [
            'Offline whole-utterance experiment; no board, playback, or live-stream claim.',
            'The A3 checkpoint is an existing local generated asset and is not a Git-delivered model.',
            'UTMOS is out-of-domain and does not replace listening.',
        ],
    }
    result_path = output_dir / 'result.json'
    result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('HOLDOUT', json.dumps({'blend': frozen_blend, **holdout, 'gates': gates},
                                 ensure_ascii=False), flush=True)
    print('COMPLETE', result_path, flush=True)


if __name__ == '__main__':
    main()
