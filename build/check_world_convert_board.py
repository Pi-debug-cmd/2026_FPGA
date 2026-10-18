"""板上闭环结果核对：ARM 转换输出 vs 宿主输出，并给出四项指标。

1) 波形/频谱层面：ARM 与宿主同源同算法，比较相关与逐 bin dB 偏差。
2) 音色层面：用与 2026-10-16 相同的四项指标（身份/源泄漏/UTMOS/内容）评价板上产物。
只读本地文件。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))

import audit_seed_reference_20261016 as audit  # noqa: E402

OUT = ROOT / 'build/generated/world_register_20261016'
ARM = OUT / 'closed_loop_arm.wav'
HOST = OUT / 'convert_host.wav'
WINDOW_START, WINDOW_SECONDS = 2.68, 4.8


def power_frames(signal: np.ndarray, size: int = 1024, hop: int = 320) -> np.ndarray:
    window = np.hanning(size)
    return np.array([np.abs(np.fft.rfft(signal[i:i + size] * window)) ** 2
                     for i in range(0, len(signal) - size, hop)])


def main() -> None:
    if not ARM.exists() or not HOST.exists():
        raise SystemExit('run build/run_world_convert_board.ps1 first')

    import soundfile as sf
    arm, rate_arm = sf.read(str(ARM), dtype='float64', always_2d=False)
    host, rate_host = sf.read(str(HOST), dtype='float64', always_2d=False)
    if rate_arm != rate_host:
        raise SystemExit('sample-rate mismatch')
    n = min(len(arm), len(host))
    difference = np.abs(arm[:n] - host[:n])
    a, b = power_frames(arm[:n]), power_frames(host[:n])
    ratio_db = 10 * np.log10(np.maximum(a.sum(0), 1e-30) / np.maximum(b.sum(0), 1e-30))
    waveform = {
        'seconds_arm': len(arm) / rate_arm, 'seconds_host': len(host) / rate_host,
        'max_abs_diff': float(difference.max()),
        'correlation': float(np.corrcoef(arm[:n], host[:n])[0, 1]),
        'spectral_per_bin_abs_db_max': float(np.abs(ratio_db).max()),
        'spectral_per_bin_abs_db_median': float(np.median(np.abs(ratio_db))),
        'total_energy_db': float(10 * np.log10(a.sum() / b.sum())),
    }

    # 四项指标：用同一目标质心与同一协议
    evaluators = audit.Evaluators()
    vectors = {}
    for name in audit.TARGET_TRACKS:
        label = 'target_' + name.split()[1].split('(')[0]
        vectors[label] = evaluators.wespeaker(audit.load16(audit.VOICE / name))[0]
    matrix = np.stack([vectors[k] for k in sorted(vectors)])
    centroid = matrix.mean(axis=0)
    centroid /= np.linalg.norm(centroid)

    source_window = audit.load16(audit.BASE / 'holdout.wav', start=WINDOW_START, seconds=WINDOW_SECONDS)
    source_vector = evaluators.wespeaker(source_window)[0]
    source_text = evaluators.transcribe(source_window)

    window = audit.load16(ARM, start=WINDOW_START, seconds=WINDOW_SECONDS)
    vector, segments = evaluators.wespeaker(window)
    text = evaluators.transcribe(window)
    metrics = {
        'identity_cosine_to_target_centroid': float(vector @ centroid),
        'leakage_cosine_to_source_window': float(vector @ source_vector),
        'utmos_predicted': evaluators.naturalness(window),
        'asr_text': text,
        'content_cer_vs_source': audit.cer(source_text, text),
        'source_asr_text': source_text,
        'segments': segments,
    }
    metrics.update(audit.f0_stats(window))

    # 对照：同一窗口的旧配方与 Seed 参考（历史数字）
    reference = {
        'world_old_window': {'identity': 0.2160, 'leakage': 0.3833, 'utmos': 2.095},
        'seed30_window': {'identity': 0.5509, 'leakage': 0.0205, 'utmos': 2.736},
        'target_self_pairwise_mean': 0.9106,
    }

    failures = []
    if waveform['correlation'] < 0.999:
        failures.append(f"ARM/宿主相关 {waveform['correlation']:.6f} < 0.999")
    if waveform['spectral_per_bin_abs_db_max'] > 0.5:
        failures.append(f"频谱偏差 {waveform['spectral_per_bin_abs_db_max']:.3f} dB > 0.5")
    if not np.isfinite(metrics['utmos_predicted']):
        failures.append('UTMOS 非有限值')

    report = {
        'kind': 'world_convert_board_closed_loop',
        'date': '2026-10-17',
        'board': {'port': 'COM14', 'os': 'PetaLinux 2022.2', 'kernel': '5.15.0-xilinx',
                  'remote_dir': '/tmp/codex_convert_20261017'},
        'run_log': 'report/world_convert_board_20261017.log',
        'waveform_arm_vs_host': waveform,
        'metrics_on_board_output': metrics,
        'historical_reference_window': reference,
        'failures': failures,
        'audio_played': False, 'recorded': False, 'alsa_touched': False, 'pl_switched': False,
        'limitations': [
            '板上只做文件读写，未接触 ALSA、未播放、未录音、未切 PL；不是实时链路。',
            '输入为已有开发句，不是现场录音；注册画像来自已有目标录音切片，不是现场注册。',
            '映射为逐频点 ±3dB 钳位版本（无 24 阶倒谱平滑），与历史配方不同，不能与历史数字直接等同。',
            '仍然只有一个源说话人、一句开发语音，非盲评；身份数值只作横向参考。',
            'ARM 与宿主波形不逐点相同（同一 WORLD 源的两次编译），判据为相关与频谱偏差。',
        ],
    }
    dest = ROOT / 'report/world_convert_board_20261017.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"arm-vs-host corr={waveform['correlation']:.6f} "
          f"spec_max={waveform['spectral_per_bin_abs_db_max']:.3f}dB")
    print(f"board output: identity={metrics['identity_cosine_to_target_centroid']:.4f} "
          f"leakage={metrics['leakage_cosine_to_source_window']:.4f} "
          f"utmos={metrics['utmos_predicted']:.3f} cer={metrics['content_cer_vs_source']['cer']:.3f}")
    print(('ALL PASS' if not failures else 'FAILURES: ' + '; '.join(failures)) + f' -> {dest}')


if __name__ == '__main__':
    main()
