"""Pinned offline target-reference conversion; no microphone, playback or board."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for directory in ['llvc_cpu_deps', 'seed_audio_deps', 'seed_cpu_deps']:
    sys.path.insert(0, str(ROOT / 'build/generated' / directory))
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
import yaml
from src.reference.audio_io import read_pcm_wav, downsample_16k, write_pcm16, file_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, choices=[8, 30], default=8)
    args = parser.parse_args()
    base = ROOT / 'build/generated/seed_reference_20261015'
    source = next((base / 'source').glob('seed-vc-*'))
    runtime = base / 'cpu_runtime'
    if not runtime.exists():
        shutil.copytree(source, runtime)
    # Keep the downloaded upstream tree immutable; patch only the execution copy.
    modified = {}
    for relative in ['inference.py', 'modules/length_regulator.py']:
        text = (source / relative).read_text(encoding='utf-8')
        if relative == 'inference.py':
            text = text.replace('.half()', '.float()')  # CPU semantic encoder in FP32.
        else:
            text = text.replace('from dac.nn.quantize import VectorQuantize\n', '')
            text = text.replace('            if vector_quantize:\n',
                                '            if vector_quantize:\n                from dac.nn.quantize import VectorQuantize\n')
        (runtime / relative).write_text(text, encoding='utf-8')
        modified[relative] = {'upstream_sha256': file_sha256(source / relative),
                              'runtime_sha256': file_sha256(runtime / relative)}
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['NUMBA_CACHE_DIR'] = str(base / 'numba_cache')
    os.environ['HF_HOME'] = str(base / 'hf_cache')
    os.chdir(runtime)
    sys.path.insert(0, str(runtime))
    torch.set_num_threads(4)
    torch.manual_seed(20261015)
    manifest = json.loads((ROOT / 'report/seed_reference_assets_20261015.json').read_text(encoding='utf-8'))
    if not manifest['complete']:
        raise ValueError('Assets incomplete')
    assets = {}
    for item in manifest['files']:
        path = Path(item['path'])
        if file_sha256(path) != item['actual_sha256']:
            raise ValueError('Asset SHA changed')
        assets[(item['repository'], item['name'])] = str(path)
    import hf_utils
    def pinned_load(repo_id, model_filename='pytorch_model.bin', config_filename=None):
        path = assets[(repo_id, model_filename)]
        return (path, assets[(repo_id, config_filename)]) if config_filename else path
    hf_utils.load_custom_model_from_hf = pinned_load
    import modules.commons as commons
    loader = commons.load_checkpoint
    loading_audit = []
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
            loading_audit.append({'module': name, 'all_current_learned_parameters_present': True,
                                  'skipped_keys': sorted(skipped),
                                  'skipped_reason': 'Generated position buffer / codebook branch unused for continuous features'})
        return loader(model, optimizer, path, *values, **options)
    commons.load_checkpoint = checked_load
    config = yaml.safe_load((runtime / 'configs/presets/config_dit_mel_seed_uvit_xlsr_tiny.yml').read_text(encoding='utf-8'))
    assert not config['model_params']['length_regulator']['vector_quantize']
    config['model_params']['speech_tokenizer']['name'] = str(base / 'assets/facebook__wav2vec2-xls-r-300m')
    config_path = base / 'cpu_tiny_config.yml'
    config_path.write_text(yaml.safe_dump(config), encoding='utf-8')
    inputs = base / 'inputs'
    inputs.mkdir(exist_ok=True)
    source_path = ROOT / 'data/registrations/source_20261015/speaker01/holdout.wav'
    target_path = ROOT / 'voice_src/src_1/Track 8(1).wav'
    input_records = []
    for path, name, first, count in [(source_path, 'source', 1.68, 6), (target_path, 'target', 0, 8)]:
        rate, signal = read_pcm_wav(path)
        signal = downsample_16k(rate, signal)[round(first * 16000):round((first + count) * 16000)]
        gain = min(.04 / max(float(np.sqrt(np.mean(signal ** 2))), 1e-12), .9 / max(float(np.max(np.abs(signal))), 1e-12))
        destination = inputs / (name + '.wav')
        write_pcm16(destination, signal * gain)
        input_records.append({'role': name, 'original_sha256': file_sha256(path), 'crop_start_s': first,
                              'seconds': count, 'offline_gain': gain, 'input_sha256': file_sha256(destination)})
    output = base / ('output_steps%d' % args.steps)
    import inference
    assert inference.device.type == 'cpu'
    settings = SimpleNamespace(source=str(inputs / 'source.wav'), target=str(inputs / 'target.wav'),
        output=str(output), diffusion_steps=args.steps, length_adjust=1., inference_cfg_rate=.7,
        f0_condition=False, auto_f0_adjust=False, semi_tone_shift=0,
        checkpoint=assets[('Plachta/Seed-VC', 'DiT_uvit_tat_xlsr_ema.pth')], config=str(config_path), fp16=False)
    started = time.perf_counter()
    print('SEED_CPU_REFERENCE_START', args.steps, flush=True)
    inference.main(settings)
    elapsed = time.perf_counter() - started
    generated = next(output.glob('vc_*.wav'))
    import soundfile as sf
    signal, rate = sf.read(generated, dtype='float32')
    if not np.all(np.isfinite(signal)) or np.sqrt(np.mean(signal ** 2)) < 1e-6:
        raise ValueError('Invalid output')
    record = {'kind': 'seed_tiny_cpu_offline_quality_reference', 'steps': args.steps, 'device': 'cpu',
              'inputs': input_records, 'runtime_changes': modified, 'elapsed_with_load_s': elapsed,
              'checkpoint_loading': loading_audit,
              'output': str(generated), 'output_sha256': file_sha256(generated), 'rate': rate,
              'output_seconds': len(signal) / rate, 'peak': float(np.max(np.abs(signal))),
              'clip_samples': int(np.sum(np.abs(signal) >= 1)), 'torch_version': torch.__version__,
              'weights_trained': False, 'source_enrollment_required': False,
              'speaker_identity_accepted': False, 'board_realtime_accepted': False,
              'limitations': 'Offline CPU reference with pretrained general model and target prompt, not a deployable 7020 design. No listening or content acceptance. Timings include model loading; no latency inference. Existing development utterance, no fresh data.'}
    (ROOT / ('report/seed_cpu_reference_steps%d_20261015.json' % args.steps)).write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
