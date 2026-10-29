"""Native VC teacher smoke test on permitted male training recordings only."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--recordings', nargs='+', type=int, choices=(1, 2, 3), default=[1])
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    root = args.asset_root.resolve()
    for key, child in {'TEMP': 'tmp', 'TMP': 'tmp', 'HF_HOME': 'cache/hf',
                       'TORCH_HOME': 'cache/torch', 'XDG_CACHE_HOME': 'cache/xdg',
                       'NUMBA_CACHE_DIR': 'cache/numba', 'MPLCONFIGDIR': 'cache/matplotlib'}.items():
        path = workspace / child
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    source = workspace / 'source/CosyVoice'
    assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == '074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc'
    sys.path[:0] = [str(source), str(source / 'third_party/Matcha-TTS')]
    assets = json.loads((workspace / 'models/asset_manifest.json').read_text(encoding='utf-8'))
    assert assets['complete'] and assets['revision'] == '29e01c4e8d000f4bcd70751be16fa94bf3d85a18'
    model_path = workspace / 'models/Fun-CosyVoice3-0.5B-2512'
    for row in assets['files']:
        path = model_path / row['name']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path
    target = root / '交接/核心材料/目标参考/target_t6_8s.wav'
    assert sha(target) == '4651ab56a9b285c0d645bd6f0b94f7987e6ed8bd5171e54c37048b436e177c8f'
    repo = Path(__file__).resolve().parents[1]
    frozen = json.loads((repo / 'report/fallback_one_to_one_assets_20261021.json').read_text(encoding='utf-8'))
    selected = [next(r for r in frozen['fixed_source']['files'] if r['role'] == f'train{i}')
                for i in args.recordings]
    for row in selected:
        assert sha(root / row['path']) == row['sha256']

    import torch
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from math import gcd
    torch.set_num_threads(4)
    assert torch.cuda.is_available()
    from transformers import AutoConfig, Qwen2ForCausalLM
    original = Qwen2ForCausalLM.from_pretrained

    def config_only(path, *a, **kw):
        config = AutoConfig.from_pretrained(path, local_files_only=True)
        old = torch.get_default_dtype()
        try:
            torch.set_default_dtype(torch.float16)
            return Qwen2ForCausalLM(config)
        finally:
            torch.set_default_dtype(old)

    from cosyvoice.cli.model import CosyVoice3Model
    upstream_init = CosyVoice3Model.__init__

    def half_storage(self, llm, flow, hift, *a, **kw):
        llm.half()
        flow.half()
        upstream_init(self, llm, flow, hift, *a, **kw)

    Qwen2ForCausalLM.from_pretrained = staticmethod(config_only)
    CosyVoice3Model.__init__ = half_storage
    started = time.perf_counter()
    try:
        from cosyvoice.cli.cosyvoice import CosyVoice3
        model = CosyVoice3(str(model_path), fp16=True)
    finally:
        Qwen2ForCausalLM.from_pretrained = original
        CosyVoice3Model.__init__ = upstream_init
    load_seconds = time.perf_counter() - started
    print('STRICT_TEACHER_LOADED', load_seconds, flush=True)
    output = workspace / 'runs/fixed_male_teacher_20261027'
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / 'generation.json').exists(), 'Do not overwrite existing generation evidence'
    rows = []
    for row in selected:
        torch.manual_seed(20261005)
        np.random.seed(20261005)
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        source_path = root / row['path']
        started = time.perf_counter()
        chunks = [r['tts_speech'].detach().cpu().float().numpy().reshape(-1)
                  for r in model.inference_vc(str(source_path), str(target), stream=False, speed=1.)]
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        signal = np.concatenate(chunks)
        assert signal.size and np.isfinite(signal).all()
        rms = float(np.sqrt(np.mean(signal ** 2)))
        assert rms > 1e-6
        gain = min(.08 / rms, .90 / max(float(np.max(np.abs(signal))), 1e-8))
        signal = resample_poly(signal * gain, 16000 // gcd(16000, model.sample_rate),
                               model.sample_rate // gcd(16000, model.sample_rate)).astype('float32')
        path = output / (row['role'] + '_teacher.wav')
        assert not path.exists(), path
        sf.write(path, signal, 16000, subtype='FLOAT')
        info = sf.info(source_path)
        rows.append({'role': row['role'], 'source_path': row['path'], 'source_sha256': row['sha256'],
                     'source_seconds': info.duration, 'teacher_path': str(path),
                     'teacher_sha256': sha(path), 'teacher_seconds': len(signal) / 16000,
                     'inference_seconds': elapsed, 'gain_only': gain,
                     'peak_cuda_bytes': torch.cuda.max_memory_allocated(),
                     'teacher_human_quality_accepted': False})
        evidence = {'kind': 'fixed_male_native_vc_teacher_generation', 'rows': rows,
                    'complete': len(rows) == len(selected), 'script_sha256': sha(Path(__file__)),
                    'asset_manifest_sha256': sha(workspace / 'models/asset_manifest.json'),
                    'model_revision': assets['revision'], 'load_seconds': load_seconds,
                    'target_sha256': sha(target), 'target_path': str(target),
                    'torch': torch.__version__, 'torchaudio': importlib.metadata.version('torchaudio'),
                    'transformers': importlib.metadata.version('transformers'),
                    'gpu': torch.cuda.get_device_name(), 'asr_to_tts': False,
                    'waveform_time_warp': False, 'recording4_used': False,
                    'recording5_used': False, 'target_track9_used': False,
                    'student_trained': False, 'playback': False, 'board_touched': False}
        (output / 'generation.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('GENERATED', row['role'], len(signal) / 16000, elapsed, flush=True)


if __name__ == '__main__':
    main()
