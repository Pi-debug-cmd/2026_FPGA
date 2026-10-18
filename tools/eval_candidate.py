#!/usr/bin/env python3
"""统一候选评测：对任意 WAV 输出四项指标（身份/源泄漏/UTMOS/内容），便于独立复核。

用法：
  python tools/eval_candidate.py <wav> [--label 名称] [--start 2.68] [--seconds 4.8] [--json 输出路径]

协议与 report/seed_reference_audit_20261016.json 一致，数字可直接与历史对照：
  身份 = 对 Track5～8 质心的 WeSpeaker 余弦；泄漏 = 对源窗口余弦；
  UTMOS = 预测自然度；内容 = whisper 转写相对源句字错率。
只读；不播放、不录音、不碰板卡。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))

import audit_seed_reference_20261016 as audit  # noqa: E402

BASELINES = {
    'A1_world_old': {'identity': 0.216, 'leakage': 0.383, 'utmos': 2.095, 'cer': 0.389},
    'A1_closed_loop': {'identity': 0.190, 'leakage': 0.172, 'utmos': 2.035, 'cer': 0.167},
    'seed_vc_pc_only': {'identity': 0.551, 'leakage': 0.021, 'utmos': 2.736, 'cer': 0.111},
    'target_self_similarity': {'identity': 0.911},
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wav', type=Path)
    parser.add_argument('--label', default=None)
    parser.add_argument('--start', type=float, default=2.68)
    parser.add_argument('--source-start', type=float, default=None,
                        help='源参考窗口起点；省略时与 --start 相同。用于候选重新从 0 计时的情况。')
    parser.add_argument('--seconds', type=float, default=4.8)
    parser.add_argument('--json', type=Path, default=None)
    args = parser.parse_args()

    if not args.wav.exists():
        raise SystemExit(f'找不到 {args.wav}')
    label = args.label or args.wav.stem

    evaluators = audit.Evaluators()
    vectors = {}
    for name in audit.TARGET_TRACKS:
        key = 'target_' + name.split()[1].split('(')[0]
        vectors[key] = evaluators.wespeaker(audit.load16(audit.VOICE / name))[0]
    matrix = np.stack([vectors[k] for k in sorted(vectors)])
    centroid = matrix.mean(axis=0)
    centroid /= np.linalg.norm(centroid)

    source_start = args.start if args.source_start is None else args.source_start
    source = audit.load16(audit.BASE / 'holdout.wav', start=source_start, seconds=args.seconds)
    source_vector = evaluators.wespeaker(source)[0]
    source_text = evaluators.transcribe(source)

    audio = audit.load16(args.wav, start=args.start, seconds=args.seconds)
    vector, _ = evaluators.wespeaker(audio)
    text = evaluators.transcribe(audio)
    record = {
        'label': label,
        'path': str(args.wav),
        'window': {'start_s': args.start, 'seconds': args.seconds, 'rate': 16000},
        'source_reference_window': {'start_s': source_start, 'seconds': args.seconds, 'rate': 16000},
        'identity_cosine_to_target_centroid': float(vector @ centroid),
        'leakage_cosine_to_source_window': float(vector @ source_vector),
        'utmos_predicted': evaluators.naturalness(audio),
        'asr_text': text,
        'content_cer_vs_source': audit.cer(source_text, text),
        'source_asr_text': source_text,
    }
    record.update(audit.f0_stats(audio))

    print(json.dumps(record, ensure_ascii=False, indent=2))
    print('\n对照（同一 4.8 秒窗）：')
    print(f"{'对象':<22}{'身份':>8}{'泄漏':>8}{'UTMOS':>8}{'字错':>8}")
    print(f"{label:<22}{record['identity_cosine_to_target_centroid']:>8.3f}"
          f"{record['leakage_cosine_to_source_window']:>8.3f}"
          f"{record['utmos_predicted']:>8.3f}"
          f"{record['content_cer_vs_source'].get('cer') or 0:>8.3f}")
    for name, values in BASELINES.items():
        print(f"{name:<22}{values.get('identity', float('nan')):>8.3f}"
              f"{values.get('leakage', float('nan')):>8.3f}"
              f"{values.get('utmos', float('nan')):>8.3f}"
              f"{values.get('cer', float('nan')):>8.3f}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\n已写入 {args.json}')


if __name__ == '__main__':
    main()
