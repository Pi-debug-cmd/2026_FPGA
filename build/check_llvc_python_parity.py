"""Checkpoint/export/C comparison; does not accept timbre or board performance."""
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llvc_host_model import load_v2, torch
from src.reference.audio_io import file_sha256, write_pcm16


def main():
    torch.set_num_threads(2)
    model, checkpoint, config, snapshot = load_v2()
    from llvc_online_stream import LLVCAudioStream
    base = ROOT / 'build/generated/llvc_host_audit_20261015'
    signal = np.fromfile(base / 'input.f32', dtype='<f4')
    expected = np.fromfile(base / 'output.f32', dtype='<f4')
    stream = LLVCAudioStream(model)
    started = time.perf_counter()
    parts = []
    for start in range(0, len(signal), 208):
        parts.extend(stream.feed(signal[start:start + 208]))
    parts.extend(stream.finish())
    output = np.concatenate(parts)
    elapsed = time.perf_counter() - started
    if output.shape != expected.shape or not np.all(np.isfinite(output)):
        raise ValueError('Python output finite/count mismatch')
    output.astype('<f4').tofile(base / 'python_output.f32')
    peak = float(np.max(np.abs(output)))
    write_pcm16(base / 'python_output.wav', output * min(1., .9 / max(peak, 1e-12)))
    error = output.astype(np.float64) - expected
    rmse = float(np.sqrt(np.mean(error ** 2)))
    rms = float(np.sqrt(np.mean(output.astype(np.float64) ** 2)))
    correlation = float(np.corrcoef(output, expected)[0, 1])
    # Replay the unchanged export body against this loaded model, with only its
    # output directory changed. Do not import training modules or run their globals.
    exporter = ROOT / '交接/核心材料/neural_reference/export_reduced_20261007.py'
    text = exporter.read_text(encoding='utf-8')
    body = text[text.index('floats = []'):]
    import struct
    namespace = {'net': model, 'sd': model.state_dict(), 'np': np, 'torch': torch,
                 'struct': struct, 'BUD': base, '__name__': 'isolated_export'}
    exec(compile(body, str(exporter), 'exec'), namespace)
    model_bin = base / 'llvc_deploy_model_reduced.bin'
    baseline_bin = base / 'model_v2.bin'
    exact_export = file_sha256(model_bin) == file_sha256(baseline_bin)
    exported, historical = model_bin.read_bytes(), baseline_bin.read_bytes()
    header = np.frombuffer(historical[:44], dtype='<u4')
    offsets = np.frombuffer(historical[44:44 + 512], dtype='<u4')
    first, last = int(header[8] + offsets[110]), int(header[8] + offsets[111])
    outside_label_identical = (len(exported) == len(historical) and
                               exported[:first] == historical[:first] and exported[last:] == historical[last:])
    old_label = np.frombuffer(historical[first:last], dtype='<f4')
    new_label = np.frombuffer(exported[first:last], dtype='<f4')
    label_error = float(np.max(np.abs(old_label - new_label)))
    record = {'kind': 'llvc_original_checkpoint_export_and_scalar_parity',
              'torch_version': torch.__version__, 'threads': 2,
              'checkpoint_sha256': file_sha256(checkpoint), 'configuration_sha256': file_sha256(config),
              'python_source_sha256': {p.name: file_sha256(p) for p in snapshot.iterdir() if p.suffix == '.py'},
              'exporter_sha256': file_sha256(exporter), 'exact_export_matches_historical_bin': exact_export,
              'all_bytes_outside_computed_label_constant_identical': outside_label_identical,
              'computed_label_constant_differing_floats': int(np.sum(old_label != new_label)),
              'computed_label_constant_max_abs_difference': label_error,
              'export_attribution': 'Only the computed zero-label embedding differs; all other constants, learned floats, scales and packed weights match. Different arithmetic environment is a plausible cause, not independently proven.',
              'export_sha256': file_sha256(model_bin), 'input_samples': len(signal), 'output_samples': len(output),
              'python_wall_s': elapsed, 'correlation_fp32_vs_int8_c': correlation,
              'rmse_fp32_vs_int8_c': rmse, 'normalized_rmse': rmse / max(rms, 1e-20),
              'max_abs_error': float(np.max(np.abs(error))),
              'python_clip_samples': int(np.sum(np.abs(output) >= 1)),
              'python_output_sha256': file_sha256(base / 'python_output.f32'),
              'target_condition_interface': 'Net.forward creates label=zeros; target identity learned in weights, no reference-audio argument.',
              'speaker_identity_accepted': False, 'board_realtime_accepted': False,
              'limitations': 'FP32 checkpoint compared to int8-weight/activation C; sample equality is not expected. Metrics are this development excerpt only. Numerical parity and exact export do not prove target identity, novel target registration, or board latency.'}
    (ROOT / 'report/llvc_checkpoint_parity_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))
    if not outside_label_identical or label_error > 1e-6:
        raise RuntimeError('Export differs outside bounded computed-label rounding')


if __name__ == '__main__':
    main()
