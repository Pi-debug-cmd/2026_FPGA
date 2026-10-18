"""板上转换工具（world_convert）数值一致性核对：C++ 实现 vs pyworld 同算法 Python 镜像。

同一输入音频 + 同一目标画像，比较两条路径的合成波形与映射参数（scale / warp / delta RMS）。
只读本地文件，不涉及板卡、录音或播放。
"""
from __future__ import annotations

import json
import subprocess
import sys
from math import gcd
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT / 'build/generated/world_deps', ROOT / 'build/generated/seed_cpu_deps'):
    if extra.is_dir():
        sys.path.insert(0, str(extra))

import pyworld  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy.signal import resample_poly  # noqa: E402

OUT = ROOT / 'build/generated/world_register_20261016'
INPUTS = OUT / 'inputs'
HOST = OUT / 'world_convert_host.exe'
REGISTER = OUT / 'world_register_host.exe'
PROFILE = OUT / 'profile_t5_8.txt'
SOURCE = INPUTS / 'source_holdout.wav'

RATE = 16000
FRAME_MS = 10.0
F0_FLOOR, F0_CEIL, DIO_SPEED = 75.0, 400.0, 4
FFT_SIZE = 1024
BINS = FFT_SIZE // 2 + 1
STRENGTH = 0.65
DELTA_LIMIT = 3.0 * np.log(10.0) / 10.0
ENERGY_FLOOR = 10 ** -4.5


def load16(path: Path) -> np.ndarray:
    x, sr = sf.read(str(path), dtype='float64', always_2d=False)
    if x.ndim == 2:
        x = x.mean(axis=1)
    if sr != RATE:
        g = gcd(int(sr), RATE)
        x = resample_poly(x, RATE // g, int(sr) // g)
    return np.ascontiguousarray(x, dtype=np.float64)


def analyse(x: np.ndarray):
    f0, t = pyworld.dio(x, RATE, f0_floor=F0_FLOOR, f0_ceil=F0_CEIL,
                        channels_in_octave=2.0, frame_period=FRAME_MS, speed=DIO_SPEED,
                        allowed_range=0.1)
    f0 = pyworld.stonemask(x, f0, t, RATE)
    centers = np.rint(t * RATE).astype(int)
    left = np.maximum(0, centers - 320)
    right = np.minimum(len(x), centers + 320)
    energy = np.r_[0.0, np.cumsum(x * x)]
    power = (energy[right] - energy[left]) / np.maximum(1, right - left)
    f0[power < ENERGY_FLOOR] = 0.0
    sp = pyworld.cheaptrick(x, f0, t, RATE, q1=-0.15, f0_floor=F0_FLOOR, fft_size=FFT_SIZE)
    ap = pyworld.d4c(x, f0, t, RATE, threshold=0.85, fft_size=FFT_SIZE)
    return f0, t, sp, ap


def warp(shape: np.ndarray, factor: float) -> np.ndarray:
    bins = np.arange(len(shape), dtype=np.float64)
    return np.interp(bins / factor, bins, shape)


def parse_profile(path: Path) -> dict:
    values: dict = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        if parts[0] == 'spectrum_db':
            values['spectrum_db'] = np.array([float(v) for v in parts[1:]])
        elif len(parts) == 2:
            values[parts[0]] = float(parts[1])
    return values


def mirror(x: np.ndarray, profile: dict) -> tuple[np.ndarray, dict]:
    f0, t, sp, ap = analyse(x)
    voiced = f0 > 0
    if voiced.sum() < 30:
        raise RuntimeError('too few voiced frames')
    log_f0 = np.log(f0[voiced])
    src_p10, src_med, src_p90 = np.percentile(log_f0, [10, 50, 90])
    tgt_p10, tgt_med, tgt_p90 = (np.log(profile['f0_p10_hz']), np.log(profile['f0_median_hz']),
                                 np.log(profile['f0_p90_hz']))
    spread = src_p90 - src_p10
    scale = float(np.clip((tgt_p90 - tgt_p10) / spread, 0.5, 2.0)) if spread >= 0.05 else 1.0

    log_sp = np.log(sp)
    source_shape = (log_sp[voiced] - log_sp[voiced].mean(axis=1, keepdims=True)).mean(axis=0)
    spectrum_db = profile['spectrum_db']
    target_shape = (spectrum_db - spectrum_db.mean()) * (np.log(10.0) / 10.0)

    bin_hz = RATE / FFT_SIZE
    freqs = np.arange(BINS) * bin_hz
    roi = (freqs >= 300.0) & (freqs <= 4000.0)
    best = (np.inf, 1.0)
    for step in range(17):
        factor = 0.85 + 0.025 * step
        diff = target_shape[roi] - warp(source_shape, factor)[roi]
        score = float(np.mean((diff - diff.mean()) ** 2))
        if score < best[0]:
            best = (score, factor)
    factor = best[1]
    delta = np.clip(target_shape - warp(source_shape, factor), -DELTA_LIMIT, DELTA_LIMIT)

    mapped_f0 = f0.copy()
    mapped_f0[voiced] = np.clip(np.exp(tgt_med + scale * (log_f0 - src_med)), F0_FLOOR, F0_CEIL)

    frame_factor = 1.0 + STRENGTH * (factor - 1.0)
    mapped_sp = sp.copy()
    for index in np.flatnonzero(voiced):
        frame = log_sp[index]
        frame = frame - frame.mean()
        candidate = np.exp(warp(frame, frame_factor) + STRENGTH * delta)
        mapped_sp[index] = candidate * (sp[index].sum() / candidate.sum())

    audio = pyworld.synthesize(mapped_f0, np.ascontiguousarray(mapped_sp), ap, RATE,
                               frame_period=FRAME_MS)[:len(x)]
    info = {'scale': scale, 'warp': factor,
            'delta_db_rms': float(10.0 / np.log(10.0) * np.sqrt(np.mean(delta ** 2))),
            'voiced_frames': int(voiced.sum())}
    return np.asarray(audio, dtype=np.float64), info


def parse_cpp(stdout: str) -> dict:
    info = {}
    for token in stdout.split():
        if '=' in token:
            key, _, value = token.partition('=')
            try:
                info[key] = float(value)
            except ValueError:
                pass
    return info


def main() -> None:
    if not HOST.exists() or not REGISTER.exists():
        raise SystemExit('build/build_world_register.ps1 must be run first')

    # 目标画像（板上注册工具的同一份产物）
    subprocess.run([str(REGISTER), str(INPUTS / 'target_t5_8_20s.wav'), str(PROFILE)],
                   check=True, capture_output=True, text=True)

    # 源音频：16 kHz 单声道 PCM16（已有 32 kHz 留出句降采样）
    if not SOURCE.exists():
        source = load16(ROOT / 'data/registrations/source_20261015/speaker01/holdout.wav')
        sf.write(str(SOURCE), source.astype(np.float32), RATE, subtype='PCM_16')

    host_out = OUT / 'convert_host.wav'
    completed = subprocess.run([str(HOST), str(SOURCE), str(PROFILE), str(host_out)],
                               capture_output=True, text=True)
    if completed.returncode != 0:
        raise SystemExit(f'convert failed: {completed.returncode} {completed.stderr}')
    cpp = parse_cpp(completed.stdout)

    x = load16(SOURCE)
    reference, py_info = mirror(x, parse_profile(PROFILE))

    cpp_audio, rate = sf.read(str(host_out), dtype='float64', always_2d=False)
    if rate != RATE:
        raise SystemExit('unexpected output rate')
    length = min(len(cpp_audio), len(reference))
    difference = np.abs(cpp_audio[:length] - reference[:length])
    max_diff = float(difference.max())
    rms_diff = float(np.sqrt(np.mean(difference ** 2)))
    signal_rms = float(np.sqrt(np.mean(reference[:length] ** 2)))
    correlation = float(np.corrcoef(cpp_audio[:length], reference[:length])[0, 1])

    # 频谱一致性：同一 WORLD 源的两次编译差异应在 dB 级可忽略，而不是波形逐点相同。
    def power_frames(signal: np.ndarray, size: int = 1024, hop: int = 320) -> np.ndarray:
        window = np.hanning(size)
        return np.array([np.abs(np.fft.rfft(signal[i:i + size] * window)) ** 2
                         for i in range(0, len(signal) - size, hop)])

    a, b = power_frames(reference[:length]), power_frames(cpp_audio[:length])
    ratio_db = 10 * np.log10(np.maximum(a.sum(0), 1e-30) / np.maximum(b.sum(0), 1e-30))
    spectral = {'frames': int(len(a)),
                'per_bin_abs_db_max': float(np.abs(ratio_db).max()),
                'per_bin_abs_db_median': float(np.median(np.abs(ratio_db))),
                'total_energy_db': float(10 * np.log10(a.sum() / b.sum()))}

    comparison = {
        'scale': {'cpp': cpp.get('scale'), 'python': py_info['scale'],
                  'abs_diff': abs(cpp.get('scale', 0) - py_info['scale'])},
        'warp': {'cpp': cpp.get('warp'), 'python': py_info['warp'],
                 'abs_diff': abs(cpp.get('warp', 0) - py_info['warp'])},
        'delta_db_rms': {'cpp': cpp.get('delta_db_rms'), 'python': py_info['delta_db_rms'],
                         'abs_diff': abs(cpp.get('delta_db_rms', 0) - py_info['delta_db_rms'])},
        'voiced_frames': {'cpp': cpp.get('voiced'), 'python': py_info['voiced_frames']},
    }
    failures = []
    if comparison['scale']['abs_diff'] > 1e-3:
        failures.append('scale 不一致（超出打印精度）')
    if comparison['warp']['abs_diff'] > 1e-3:
        failures.append('warp 因子不一致')
    if comparison['delta_db_rms']['abs_diff'] > 1e-3:
        failures.append('delta RMS 不一致')
    if comparison['voiced_frames']['cpp'] != comparison['voiced_frames']['python']:
        failures.append('有声帧数不一致')
    if correlation < 0.999:
        failures.append(f'波形相关 {correlation:.6f} 低于 0.999')
    if spectral['per_bin_abs_db_max'] > 0.5:
        failures.append(f"频谱最大偏差 {spectral['per_bin_abs_db_max']:.3f} dB 超过 0.5 dB")

    report = {
        'kind': 'world_convert_host_parity',
        'date': '2026-10-17',
        'tool': 'src/ps/world_convert.cpp',
        'input': {'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
                  'profile': str(PROFILE.relative_to(ROOT)).replace('\\', '/'),
                  'seconds': len(x) / RATE},
        'parameters': comparison,
        'waveform': {'cpp_seconds': len(cpp_audio) / RATE, 'max_abs_diff': max_diff,
                     'rms_diff': rms_diff, 'reference_rms': signal_rms,
                     'relative_rms_diff': rms_diff / signal_rms if signal_rms > 0 else None,
                     'correlation': correlation, 'spectral': spectral,
                     'peak_cpp': float(np.max(np.abs(cpp_audio))),
                     'clipped_cpp': int(np.sum(np.abs(cpp_audio) >= 1.0))},
        'tolerance': {'map_parameters': 1e-3, 'waveform_correlation_min': 0.999,
                      'spectral_per_bin_db_max': 0.5},
        'tolerance_rationale': (
            '映射参数按 C++ printf 精度（6/4 位小数）比对，故取 1e-3。'
            '波形不逐点相同：pyworld 预编译包与本次 MinGW/ARM 编译使用的是同一份 WORLD 0.3.5 源码，'
            '但浮点求值顺序不同；实测频谱逐 bin 偏差约 0.03～0.06 dB、总能量 0.03 dB、波形相关 0.9994，'
            '属相位级差异而非算法差异，因此判据用相关与频谱误差，不伪造逐点相等。'),
        'failures': failures,
        'board_deployed': False, 'audio_played': False,
        'limitations': [
            '主机 x86_64 运行，不是板端 ARM 结果；板端一致性须另行比对。',
            '映射为逐频点 ±3dB 钳位版本，未使用历史配方的 24 阶倒谱平滑，因此不是历史配方复现。',
            '数值一致只说明移植正确，不代表音色有效；身份/自然度/内容由独立指标评价。',
        ],
    }
    dest = ROOT / 'report/world_convert_parity_20261017.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"scale={comparison['scale']['cpp']:.6f} warp={comparison['warp']['cpp']:.4f} "
          f"voiced={comparison['voiced_frames']['cpp']} max_abs_diff={max_diff:.3e} "
          f"rel_rms={report['waveform']['relative_rms_diff']:.3e}")
    print(('ALL PASS' if not failures else 'FAILURES: ' + '; '.join(failures)) + f' -> {dest}')


if __name__ == '__main__':
    main()
