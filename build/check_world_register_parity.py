"""注册工具数值一致性核对：宿主 C++ 画像 vs PC 端 pyworld 同一算法。

两者共用 WORLD 0.3.5 的同一份 C++ 核，因此 f0 统计、频带比例与 AP 均值应逐项一致；
本脚本量化差异并留档，不把“接近”说成“相同”。
只读本地文件，不涉及板卡、录音或播放。
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT / 'build/generated/world_deps', ROOT / 'build/generated/seed_cpu_deps'):
    if extra.is_dir():
        sys.path.insert(0, str(extra))

import pyworld  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy.signal import resample_poly  # noqa: E402
from math import gcd  # noqa: E402

OUT = ROOT / 'build/generated/world_register_20261016'
INPUTS = OUT / 'inputs'
HOST = OUT / 'world_register_host.exe'
VOICE = ROOT / 'voice_src/src_1'
FRAME_PERIOD = 10.0
F0_FLOOR, F0_CEIL = 71.0, 800.0
BANDS = [('80_400', 80.0, 400.0), ('400_1000', 400.0, 1000.0), ('1000_2000', 1000.0, 2000.0),
         ('2000_4000', 2000.0, 4000.0), ('4000_8000', 4000.0, 8000.0)]
AP_BANDS = [('below_1000', 0.0, 1000.0), ('1000_3000', 1000.0, 3000.0), ('3000_8000', 3000.0, 8000.0)]


def load16(path: Path, seconds: float | None = None) -> np.ndarray:
    x, sr = sf.read(str(path), dtype='float64', always_2d=False)
    if x.ndim == 2:
        x = x.mean(axis=1)
    if seconds is not None:
        x = x[:int(round(seconds * sr))]
    if sr != 16000:
        g = gcd(int(sr), 16000)
        x = resample_poly(x, 16000 // g, int(sr) // g)
    return np.ascontiguousarray(x, dtype=np.float64)


def prepare_inputs() -> list[dict]:
    INPUTS.mkdir(parents=True, exist_ok=True)
    prepared = []
    single = load16(VOICE / 'Track 8(1).wav', seconds=10.0)
    sf.write(str(INPUTS / 'target_t8_10s.wav'), single.astype(np.float32), 16000, subtype='PCM_16')
    prepared.append({'name': 'target_t8_10s', 'source': 'Track 8(1).wav 前10秒',
                     'path': INPUTS / 'target_t8_10s.wav', 'seconds': len(single) / 16000})
    parts = [load16(VOICE / f'Track {n}(1).wav', seconds=5.0) for n in range(5, 9)]
    joined = np.concatenate(parts)
    sf.write(str(INPUTS / 'target_t5_8_20s.wav'), joined.astype(np.float32), 16000, subtype='PCM_16')
    prepared.append({'name': 'target_t5_8_20s', 'source': 'Track 5～8 各前5秒拼接',
                     'path': INPUTS / 'target_t5_8_20s.wav', 'seconds': len(joined) / 16000})
    # 质量门槛负样本：0.5 秒过短录音，应被拒绝（返回 3）。
    sf.write(str(INPUTS / 'reject_too_short.wav'), single[:8000].astype(np.float32), 16000, subtype='PCM_16')
    prepared.append({'name': 'reject_too_short', 'source': '0.5秒片段',
                     'path': INPUTS / 'reject_too_short.wav', 'seconds': 0.5, 'expect_reject': 3})
    # 质量门槛负样本：全静音，应被拒绝（返回 5）。
    sf.write(str(INPUTS / 'reject_silent.wav'), np.zeros(32000, dtype=np.float32), 16000, subtype='PCM_16')
    prepared.append({'name': 'reject_silent', 'source': '2秒全静音',
                     'path': INPUTS / 'reject_silent.wav', 'seconds': 2.0, 'expect_reject': 5})
    return prepared


def parse_profile(path: Path) -> dict:
    values: dict = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        if parts[0] in ('band_db', 'ap_mean'):
            values[f'{parts[0]}_{parts[1]}'] = float(parts[2])
        elif parts[0] == 'spectrum_db':
            values['spectrum_db'] = [float(v) for v in parts[1:]]
        elif len(parts) == 2:
            values[parts[0]] = float(parts[1])
    return values


def pyworld_profile(x: np.ndarray, fft_size: int) -> dict:
    f0, t = pyworld.dio(x, 16000, f0_floor=F0_FLOOR, f0_ceil=F0_CEIL,
                        channels_in_octave=2.0, frame_period=FRAME_PERIOD, speed=1, allowed_range=0.1)
    f0 = pyworld.stonemask(x, f0, t, 16000)
    voiced = f0 > 0
    sp = pyworld.cheaptrick(x, f0, t, 16000, q1=-0.15, f0_floor=F0_FLOOR, fft_size=fft_size)
    ap = pyworld.d4c(x, f0, t, 16000, threshold=0.85, fft_size=fft_size)
    mean_sp = sp[voiced].mean(axis=0)
    mean_ap = ap[voiced].mean(axis=0)
    bins = mean_sp.shape[0]
    freqs = np.linspace(0, 8000, bins)
    total = float(mean_sp.sum())
    profile = {
        'voiced_frames': int(voiced.sum()),
        'voiced_fraction': float(voiced.mean()),
        'f0_median_hz': float(np.median(f0[voiced])),
        'f0_p10_hz': float(np.percentile(f0[voiced], 10)),
        'f0_p90_hz': float(np.percentile(f0[voiced], 90)),
    }
    for name, low, high in BANDS:
        mask = (freqs >= low) & (freqs < high)
        profile[f'band_db_{name}'] = float(10 * math.log10(float(mean_sp[mask].sum()) / total))
    for name, low, high in AP_BANDS:
        mask = (freqs >= low) & (freqs < high)
        profile[f'ap_mean_{name}'] = float(mean_ap[mask].mean())
    return profile


def main() -> None:
    if not HOST.exists():
        raise SystemExit('host binary missing; run build/build_world_register.ps1 first')
    prepared = prepare_inputs()
    results, failures = [], []

    for item in prepared:
        profile_path = OUT / f"{item['name']}.profile.txt"
        completed = subprocess.run([str(HOST), str(item['path']), str(profile_path)],
                                   capture_output=True, text=True)
        record = {'name': item['name'], 'source': item['source'], 'seconds': item['seconds'],
                  'exit_code': completed.returncode, 'stdout': completed.stdout.strip(),
                  'stderr': completed.stderr.strip()}
        if 'expect_reject' in item:
            record['expect_reject'] = item['expect_reject']
            record['reject_correct'] = completed.returncode == item['expect_reject']
            if not record['reject_correct']:
                failures.append(f"{item['name']}: 期望拒绝码 {item['expect_reject']}，实得 {completed.returncode}")
            results.append(record)
            print(f"{item['name']:<20} exit={completed.returncode} (expect {item['expect_reject']})", flush=True)
            continue

        c_profile = parse_profile(profile_path)
        x = load16(item['path'])
        reference = pyworld_profile(x, int(c_profile['fft_size']))
        keys = ['voiced_frames', 'voiced_fraction', 'f0_median_hz', 'f0_p10_hz', 'f0_p90_hz']
        keys += [f'band_db_{name}' for name, _, _ in BANDS]
        keys += [f'ap_mean_{name}' for name, _, _ in AP_BANDS]
        comparison, worst = {}, 0.0
        for key in keys:
            difference = abs(float(c_profile[key]) - float(reference[key]))
            comparison[key] = {'cpp': float(c_profile[key]), 'pyworld': float(reference[key]),
                               'abs_diff': difference}
            worst = max(worst, difference)
        record.update({'profile_sha256': None, 'comparison': comparison, 'max_abs_diff': worst,
                       'tolerance': 1e-5, 'within_tolerance': worst <= 1e-5})
        if not record['within_tolerance']:
            failures.append(f"{item['name']}: 最大差异 {worst:.3e} 超出容差")
        results.append(record)
        print(f"{item['name']:<20} exit=0 max_abs_diff={worst:.3e} "
              f"f0_median={c_profile['f0_median_hz']:.3f}Hz", flush=True)

    report = {
        'kind': 'world_register_host_parity',
        'date': '2026-10-16',
        'tool': 'src/ps/world_register.cpp',
        'protocol': {'rate': 16000, 'bits': 16, 'frame_period_ms': FRAME_PERIOD,
                     'f0_floor': F0_FLOOR, 'f0_ceil': F0_CEIL, 'q1': -0.15, 'd4c_threshold': 0.85,
                     'comparison': 'relative quantities only (scale invariant)'},
        'tolerance_rationale': ('容差 1e-5 覆盖累加顺序带来的浮点差异：C++ 按帧顺序累加 513 个频点，'
                                'numpy 用成对求和；实测最大差约 4e-7，属算术顺序而非算法差异。'
                                '两者共用同一份 WORLD 0.3.5 C++ 核，f0 与声道统计应逐项吻合。'),
        'files': results, 'failures': failures,
        'host_binary': str(HOST.relative_to(ROOT)),
        'board_deployed': False, 'board_run': False, 'audio_played': False,
        'limitations': [
            '主机 x86_64 编译结果，不是板端 ARM 运行结果；板端一致性须另行上传核对。',
            '输入为已有目标录音切片，不是现场注册录音；未验证真实现场噪声与电平条件。',
            '画像与 PC 端 pyworld 同源（同一份 WORLD 0.3.5 C++），所以一致只说明移植正确，不代表算法有效。',
        ],
    }
    dest = ROOT / 'report/world_register_parity_20261016.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(('ALL PASS' if not failures else 'FAILURES: ' + '; '.join(failures)) + f' -> {dest}', flush=True)


if __name__ == '__main__':
    main()
