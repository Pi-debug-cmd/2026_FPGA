"""Isolated host-only historical LLVC reference; no board or audio devices."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.reference.audio_io import file_sha256, read_pcm_wav, downsample_16k, write_pcm16


def main():
    original = ROOT / '交接/核心材料/deploy_runtime'
    base = ROOT / 'build/generated/llvc_host_audit_20261015'
    snapshot = base / 'source_snapshot'
    snapshot.mkdir(parents=True, exist_ok=True)
    names = ['deploy_llvc.c', 'llvc_runtime.c', 'llvc_runtime.h', 'gemm_ref.c', 'gemm_backend.h']
    sources = {}
    for name in names:
        shutil.copyfile(original / name, snapshot / name)
        sources[name] = file_sha256(snapshot / name)
        if sources[name] != file_sha256(original / name):
            raise ValueError('Snapshot mismatch')
    model = ROOT / '交接/核心材料/board_budget_20261005/llvc_deploy_model_reduced.bin'
    expected = '4e635452493b67b1a83fa70cd356bbfbc3ac605339e7a0c5e37c9c4ed5f5e7bd'
    if file_sha256(model) != expected:
        raise ValueError('Historical v2 model hash mismatch')
    shutil.copyfile(model, base / 'model_v2.bin')
    compiler = Path('D:/mingw64/bin/gcc.exe')
    executable = base / 'llvc_scalar.exe'
    compiled = subprocess.run([str(compiler), '-O2', '-std=gnu11', '-I', str(snapshot),
                               *[str(snapshot / name) for name in ['deploy_llvc.c', 'llvc_runtime.c', 'gemm_ref.c']],
                               '-lm', '-o', str(executable)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    (base / 'build.log').write_bytes(compiled.stdout)
    if compiled.returncode:
        raise RuntimeError('Host build failed: ' + compiled.stdout.decode(errors='replace')[-2000:])
    source_path = ROOT / 'data/registrations/source_20261015/speaker01/holdout.wav'
    rate, signal = read_pcm_wav(source_path)
    signal = downsample_16k(rate, signal)
    # One second before the already-used five-second excerpt warms streaming state.
    start, count = round(1.68 * 16000), 96000
    input_signal = np.asarray(signal[start:start + count], dtype='<f4')
    if len(input_signal) != count:
        raise ValueError('Short source')
    (base / 'input.f32').write_bytes(input_signal.tobytes())
    env = {key: value for key, value in os.environ.items() if key not in ['LLVC_DUMP', 'LLVC_DUMP_BLOCK']}
    started = time.perf_counter()
    result = subprocess.run([str(executable), 'model_v2.bin'], input=input_signal.tobytes(),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=base, env=env, timeout=120)
    elapsed = time.perf_counter() - started
    (base / 'runtime_stderr.log').write_bytes(result.stderr)
    (base / 'output.f32').write_bytes(result.stdout)
    output = np.frombuffer(result.stdout, dtype='<f4')
    if result.returncode or len(output) != count or not np.all(np.isfinite(output)):
        raise RuntimeError('Host reference failed finite/count check')
    peak = float(np.max(np.abs(output)))
    gain = min(1., .9 / max(peak, 1e-12))
    write_pcm16(base / 'output.wav', output * gain)
    checkpoints = [path for path in (ROOT / '交接/核心材料').rglob('*')
                   if path.suffix.lower() in {'.pt', '.pth', '.onnx', '.npz'}]
    record = {'kind': 'historical_llvc_v2_scalar_host_file_gate', 'source_snapshots': sources,
              'compiler': str(compiler), 'model_sha256': expected, 'binary_sha256': file_sha256(executable),
              'source_sha256': file_sha256(source_path), 'input_start_s': 1.68, 'input_samples': count,
              'output_samples': len(output), 'input_gain': 1., 'elapsed_host_wall_s': elapsed,
              'host_wall_rtf': elapsed / 6, 'output_peak': peak,
              'output_rms': float(np.sqrt(np.mean(output.astype(np.float64) ** 2))),
              'output_clip_samples': int(np.sum(np.abs(output) >= 1)), 'archive_gain': gain,
              'output_f32_sha256': file_sha256(base / 'output.f32'),
              'checkpoint_asset_count_pt_pth_onnx_npz': len(checkpoints),
              'previous_checkpoint_missing_claim_corrected': True,
              'speaker_identity_accepted': False, 'board_realtime_accepted': False,
              'limitations': 'Unchanged historical scalar C model, not a newly trained or source-registered model. Host file execution only, no PL/ALSA. Original model parity still needs independent reproduction. This fixed-target v2 model does not demonstrate registering a new target. Six-second development excerpt, one source speaker; no listening or identity acceptance.'}
    (ROOT / 'report/llvc_host_reference_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
