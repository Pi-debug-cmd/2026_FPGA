"""Offline Seed-VC teacher sweep using a deterministic multi-utterance target registration prompt.

No board, microphone or playback is used.  The upstream source and downloaded
weights are SHA-checked through the existing asset manifest before inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
for directory in ['llvc_cpu_deps', 'seed_audio_deps', 'seed_cpu_deps']:
    sys.path.insert(0, str(ROOT / 'build/generated' / directory))
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
import yaml

from src.reference.audio_io import downsample_16k, file_sha256, read_pcm_wav, write_pcm16


TARGET_TRACKS = [f'Track {number}(1).wav' for number in range(5, 9)]


def select_speech_window(signal: np.ndarray, rate: int, seconds: float) -> tuple[int, np.ndarray]:
    """Choose a high-activity window without relying on transcript or target holdout data."""
    count = round(seconds * rate)
    if len(signal) < count:
        raise ValueError('Target registration track is too short')
    frame = round(.02 * rate)
    hop = round(.01 * rate)
    squares = np.convolve(np.asarray(signal, dtype=np.float64) ** 2,
                          np.ones(frame, dtype=np.float64) / frame, mode='valid')[::hop]
    active = squares > 10 ** (-45 / 10)
    frames = max(1, int(np.ceil((count - frame) / hop)) + 1)
    activity = np.convolve(active.astype(np.float64), np.ones(frames), mode='valid')
    energy = np.convolve(squares, np.ones(frames), mode='valid')
    score = activity + .01 * np.log(np.maximum(energy, 1e-20))
    start_frame = int(np.argmax(score))
    start = min(start_frame * hop, len(signal) - count)
    return start, np.asarray(signal[start:start + count], dtype=np.float64).copy()


def make_inputs(base: Path) -> tuple[list[dict], Path, Path]:
    inputs = base / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    source_original = ROOT / 'data/registrations/source_20261015/speaker01/holdout.wav'
    rate, source = read_pcm_wav(source_original)
    source = downsample_16k(rate, source)[round(1.68 * 16000):round(7.68 * 16000)]
    source_gain = min(.04 / max(float(np.sqrt(np.mean(source ** 2))), 1e-12),
                      .9 / max(float(np.max(np.abs(source))), 1e-12))
    source_path = inputs / 'source.wav'
    write_pcm16(source_path, source * source_gain)

    records: list[dict] = [{
        'role': 'source', 'original': str(source_original.relative_to(ROOT)),
        'original_sha256': file_sha256(source_original), 'crop_start_s': 1.68,
        'seconds': 6.0, 'offline_gain': source_gain,
    }]
    parts = []
    fade = np.linspace(0.0, 1.0, round(.01 * 16000), endpoint=False)
    for filename in TARGET_TRACKS:
        original = ROOT / 'voice_src/src_1' / filename
        rate, signal = read_pcm_wav(original)
        signal = downsample_16k(rate, signal)
        start, part = select_speech_window(signal, 16000, 2.0)
        part[:len(fade)] *= fade
        part[-len(fade):] *= fade[::-1]
        parts.append(part)
        records.append({
            'role': 'target_registration_segment', 'file': str(original.relative_to(ROOT)),
            'sha256': file_sha256(original), 'crop_start_s': start / 16000,
            'seconds': len(part) / 16000,
        })
    target = np.concatenate(parts)
    target_gain = min(.04 / max(float(np.sqrt(np.mean(target ** 2))), 1e-12),
                      .9 / max(float(np.max(np.abs(target))), 1e-12))
    target_path = inputs / 'target_registered.wav'
    write_pcm16(target_path, target * target_gain)
    records.append({
        'role': 'target_registration_prompt', 'construction': 'four_tracks_x_2s_high_activity',
        'seconds': len(target) / 16000, 'offline_gain': target_gain,
        'sha256': file_sha256(target_path), 'holdout_track9_used': False,
    })
    return records, source_path, target_path


def prepare_runtime(base: Path) -> tuple[Path, dict, dict, list[dict]]:
    source = next((ROOT / 'build/generated/seed_reference_20261015/source').glob('seed-vc-*'))
    runtime = base / 'cpu_runtime'
    if not runtime.exists():
        shutil.copytree(source, runtime)
    modified = {}
    for relative in ['inference.py', 'modules/length_regulator.py']:
        text = (source / relative).read_text(encoding='utf-8')
        if relative == 'inference.py':
            text = text.replace('.half()', '.float()')
        else:
            text = text.replace('from dac.nn.quantize import VectorQuantize\n', '')
            text = text.replace('            if vector_quantize:\n',
                                '            if vector_quantize:\n                from dac.nn.quantize import VectorQuantize\n')
        destination = runtime / relative
        destination.write_text(text, encoding='utf-8')
        modified[relative] = {
            'upstream_sha256': file_sha256(source / relative),
            'runtime_sha256': file_sha256(destination),
        }
    manifest = json.loads((ROOT / 'report/seed_reference_assets_20261015.json').read_text(encoding='utf-8'))
    if not manifest['complete']:
        raise ValueError('Seed assets are incomplete')
    assets = {}
    for item in manifest['files']:
        path = Path(item['path'])
        if file_sha256(path) != item['actual_sha256']:
            raise ValueError('Seed asset SHA changed: ' + str(path))
        assets[(item['repository'], item['name'])] = str(path)
    loading_audit: list[dict] = []
    return runtime, assets, modified, loading_audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cfg', type=float, nargs='+', default=[.45, .7, .95])
    parser.add_argument('--steps', type=int, default=30)
    parser.add_argument('--seed', type=int, default=20261018)
    parser.add_argument('--tag', default='controlled')
    args = parser.parse_args()
    if args.steps < 1 or any(value < 0 or value > 2 for value in args.cfg):
        raise SystemExit('Invalid steps/cfg value')

    if not args.tag.replace('_', '').replace('-', '').isalnum():
        raise SystemExit('Tag must contain only letters, numbers, underscores or hyphens')
    base = ROOT / ('build/generated/quality_exploration_20261018/seed_registration_' + args.tag)
    base.mkdir(parents=True, exist_ok=True)
    inputs, source_path, target_path = make_inputs(base)
    runtime, assets, modified, loading_audit = prepare_runtime(base)
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['NUMBA_CACHE_DIR'] = str(base / 'numba_cache')
    os.environ['HF_HOME'] = str(base / 'hf_cache')
    os.chdir(runtime)
    sys.path.insert(0, str(runtime))
    torch.set_num_threads(4)
    torch.manual_seed(args.seed)

    import hf_utils
    def pinned_load(repo_id, model_filename='pytorch_model.bin', config_filename=None):
        path = assets[(repo_id, model_filename)]
        return (path, assets[(repo_id, config_filename)]) if config_filename else path
    hf_utils.load_custom_model_from_hf = pinned_load

    import modules.commons as commons
    original_loader = commons.load_checkpoint
    def checked_load(model, optimizer, path, *values, **options):
        state = torch.load(path, map_location='cpu', weights_only=True)['net']
        for name, network in model.items():
            supplied = {key.removeprefix('module.'): value for key, value in state[name].items()}
            for key, parameter in network.named_parameters():
                if key not in supplied or supplied[key].shape != parameter.shape:
                    raise ValueError('Learned parameter missing/mismatched: ' + name + '/' + key)
            own = network.state_dict()
            skipped = {key for key, value in supplied.items() if key not in own or own[key].shape != value.shape}
            allowed = {'estimator.input_pos'} if name == 'cfm' else set()
            if name == 'length_regulator' and not network.is_discrete:
                allowed = {'extra_codebook_mask_tokens.0', 'extra_codebooks.0.weight'}
            if skipped - allowed:
                raise ValueError('Unexpected checkpoint keys: ' + str(skipped - allowed))
            loading_audit.append({'module': name, 'skipped_keys': sorted(skipped)})
        return original_loader(model, optimizer, path, *values, **options)
    commons.load_checkpoint = checked_load

    config = yaml.safe_load((runtime / 'configs/presets/config_dit_mel_seed_uvit_xlsr_tiny.yml').read_text(encoding='utf-8'))
    config['model_params']['speech_tokenizer']['name'] = str(
        ROOT / 'build/generated/seed_reference_20261015/assets/facebook__wav2vec2-xls-r-300m')
    config_path = base / 'cpu_tiny_config.yml'
    config_path.write_text(yaml.safe_dump(config), encoding='utf-8')
    import inference
    if inference.device.type != 'cpu':
        raise RuntimeError('This reproducible sweep must run on CPU')

    outputs = []
    for cfg in args.cfg:
        # Reset for every condition so CFG comparisons do not consume different RNG streams.
        torch.manual_seed(args.seed)
        output_dir = base / ('cfg_%0.2f' % cfg)
        settings = SimpleNamespace(
            source=str(source_path), target=str(target_path), output=str(output_dir),
            diffusion_steps=args.steps, length_adjust=1.0, inference_cfg_rate=cfg,
            f0_condition=False, auto_f0_adjust=False, semi_tone_shift=0,
            checkpoint=assets[('Plachta/Seed-VC', 'DiT_uvit_tat_xlsr_ema.pth')],
            config=str(config_path), fp16=False,
        )
        started = time.perf_counter()
        inference.main(settings)
        elapsed = time.perf_counter() - started
        generated = next(output_dir.glob('vc_*.wav'))
        import soundfile as sf
        signal, rate = sf.read(generated, dtype='float32')
        if not np.all(np.isfinite(signal)) or float(np.sqrt(np.mean(signal ** 2))) < 1e-6:
            raise ValueError('Invalid Seed output for cfg=' + str(cfg))
        outputs.append({
            'cfg': cfg, 'steps': args.steps, 'path': str(generated.relative_to(ROOT)),
            'sha256': file_sha256(generated), 'elapsed_with_load_s': elapsed,
            'rate': rate, 'seconds': len(signal) / rate,
            'peak': float(np.max(np.abs(signal))), 'clip_samples': int(np.sum(np.abs(signal) >= 1)),
        })

    record = {
        'kind': 'seed_vc_multi_utterance_target_registration_sweep',
        'date': '2026-10-18', 'device': 'cpu', 'seed': args.seed, 'tag': args.tag, 'inputs': inputs,
        'runtime_changes': modified, 'checkpoint_loading': loading_audit,
        'outputs': outputs, 'played': False, 'board_touched': False,
        'target_track9_used_for_registration': False,
        'limitations': [
            'Single source speaker and existing development utterance.',
            'Seed-VC is an offline quality teacher, not a Zynq-7020 runtime candidate.',
            'Objective scores do not establish absence of AI-like artifacts; listening requires fresh readiness.',
        ],
    }
    report = ROOT / ('report/quality_exploration_seed_sweep_20261018_' + args.tag + '.json')
    report.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
