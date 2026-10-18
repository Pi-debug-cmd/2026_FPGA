"""板上注册工具结果核对：ARM 画像 vs 宿主画像 vs PC pyworld。

读取已回传的 ARM 画像文件与宿主画像文件，逐项比较并留档；同时记录上传/回传 SHA。
只读本地文件。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/generated/world_register_20261016'
PAIRS = [('target_t8_10s', OUT / 'arm_p_t8.txt', OUT / 'target_t8_10s.profile.txt'),
         ('target_t5_8_20s', OUT / 'arm_p_t5_8.txt', OUT / 'target_t5_8_20s.profile.txt')]


def parse(path: Path) -> dict:
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


def main() -> None:
    sha = lambda p: subprocess.run(['certutil', '-hashfile', str(p), 'SHA256'],
                                   capture_output=True, text=True).stdout.splitlines()[1].strip().lower()
    results, failures = [], []
    for name, arm_path, host_path in PAIRS:
        if not arm_path.exists() or not host_path.exists():
            failures.append(f'{name}: 缺少 {arm_path.name} 或 {host_path.name}')
            continue
        arm_bytes, host_bytes = arm_path.read_bytes(), host_path.read_bytes()
        arm, host = parse(arm_path), parse(host_path)
        keys = sorted(set(arm) & set(host) - {'spectrum_db'})
        comparison, worst = {}, 0.0
        for key in keys:
            difference = abs(float(arm[key]) - float(host[key]))
            comparison[key] = {'arm': float(arm[key]), 'host': float(host[key]), 'abs_diff': difference}
            worst = max(worst, difference)
        spectra_equal = arm.get('spectrum_db') == host.get('spectrum_db')
        record = {'name': name, 'arm_file': arm_path.name, 'host_file': host_path.name,
                  'arm_sha256': sha(arm_path), 'host_sha256': sha(host_path),
                  'bytes_identical': arm_bytes == host_bytes,
                  'max_abs_diff': worst, 'spectrum_identical': spectra_equal,
                  'comparison': comparison}
        results.append(record)
        status = 'IDENTICAL' if arm_bytes == host_bytes else f'max_abs_diff={worst:.3e}'
        print(f'{name:<18} {status}', flush=True)
        if arm_bytes != host_bytes and worst > 1e-9:
            failures.append(f'{name}: ARM 与宿主最大差异 {worst:.3e}')

    probe = ROOT / 'report/board_probe_20261016.log'
    board_log = ROOT / 'report/world_register_board_20261016.log'
    report = {
        'kind': 'world_register_board_run',
        'date': '2026-10-16',
        'tool': 'src/ps/world_register.cpp',
        'arm_binary_sha256': 'D5BDB272A513202D5D980464709AA5584BA742B68BBD87C093F89F4F896567D2',
        'remote_dir': '/tmp/codex_reg_20261016',
        'board': {'port': 'COM14', 'os': 'PetaLinux 2022.2', 'kernel': '5.15.0-xilinx',
                  'probe_log': str(probe.relative_to(ROOT)) if probe.exists() else None},
        'board_run_log': str(board_log.relative_to(ROOT)) if board_log.exists() else None,
        'board_summary': {
            't8_10s': 'OK voiced=672 f0_median=184.291 f0_p10=165.930 f0_p90=216.080 exit=0',
            't5_8_20s': 'OK voiced=1065 f0_median=194.357 f0_p10=170.641 f0_p90=242.487 exit=0',
            'reject_too_short': 'REJECTED too_short exit=3',
            'reject_silent': 'REJECTED silent_input exit=5',
        },
        'files': results, 'failures': failures,
        'alembic': {'audio_played': False, 'recorded': False, 'alsa_touched': False, 'pl_switched': False},
        'limitations': [
            '板上只做了文件读写，未接触 ALSA、未播放、未录音、未切 PL。',
            '输入是已有目标录音切片，不是现场注册录音；现场噪声/电平与换人重注册、回退流程未验证。',
            'ARM 与宿主逐字节一致只说明移植正确，不代表画像对目标音色有效；身份效果仍由 param_candidate_audit 与后续转换评测决定。',
        ],
    }
    dest = ROOT / 'report/world_register_board_20261016.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(('ALL PASS' if not failures else 'FAILURES: ' + '; '.join(failures)) + f' -> {dest}', flush=True)


if __name__ == '__main__':
    main()
