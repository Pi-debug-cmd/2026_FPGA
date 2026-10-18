"""判决性实验第一刀：用同四项指标审计已有的参数化候选。

不合成新音频，只评价 data/registrations/source_20261015/speaker01 下已有的对照输出，
回答“参数化（WORLD 系）目标化到底把身份相似度推到多高”。

复用 build/audit_seed_reference_20261016.py 的评测器与协议，保证数字可比。
只读；无录音、无播放、无板卡操作。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))

import audit_seed_reference_20261016 as audit  # noqa: E402  (sets up sys.path/env)

BASE = audit.BASE
WINDOW_START = 2.68
WINDOW_SECONDS = 4.8

CANDIDATES = [
    ('world_old_fixed', '现役旧固定配方（对照基线）', BASE / 'hybrid_comparison/old_fixed.wav'),
    ('prepared_pitch', '按人仅音高映射', BASE / 'heldout_comparison/prepared_pitch.wav'),
    ('prepared_timbre', '按人谱包络（音色）候选', BASE / 'heldout_comparison/prepared_timbre.wav'),
    ('prepared_pitch_old_warp', '旧谱变形+按人音高', BASE / 'hybrid_comparison/prepared_pitch_old_warp.wav'),
    ('balanced_low_shelf', '低频架 4dB 衰减候选', BASE / 'low_shelf_comparison/balanced_old_fixed.wav'),
    ('balanced_spectral', '谱平衡候选', BASE / 'spectral_balance_comparison/balanced_old_fixed.wav'),
]


def main() -> None:
    started = time.time()
    evaluators = audit.Evaluators()

    # 目标质心：Track5～8，与 seed 审计同一口径（含 Track8，故对 Seed 偏高，对候选同样偏高，可比）。
    vectors = {}
    for name in audit.TARGET_TRACKS:
        label = 'target_' + name.split()[1].split('(')[0]
        vectors[label] = evaluators.wespeaker(audit.load16(audit.VOICE / name))[0]
    matrix = np.stack([vectors[k] for k in sorted(vectors)])
    centroid = matrix.mean(axis=0)
    centroid /= np.linalg.norm(centroid)
    pairwise = [float(matrix[i] @ matrix[j]) for i in range(len(matrix)) for j in range(i + 1, len(matrix))]

    source_window = audit.load16(BASE / 'holdout.wav', start=WINDOW_START, seconds=WINDOW_SECONDS)
    source_vector = evaluators.wespeaker(source_window)[0]
    target_window = audit.load16(audit.VOICE / audit.HELD_OUT_TRACK, start=11.0, seconds=WINDOW_SECONDS)

    records = []

    def add(label, role, audio, path=None, transcript=True):
        vector, segments = evaluators.wespeaker(audio)
        record = {
            'label': label, 'role': role,
            'path': str(path.relative_to(ROOT)).replace('\\', '/') if path else None,
            'sha256': audit.sha256(path) if path else None,
            'seconds': len(audio) / 16000, 'segments': segments,
            'identity_cosine_to_target_centroid': float(vector @ centroid),
            'leakage_cosine_to_source_window': float(vector @ source_vector),
            'utmos_predicted': evaluators.naturalness(audio),
        }
        record.update(audit.f0_stats(audio))
        if transcript:
            record['asr_text'] = evaluators.transcribe(audio)
        records.append(record)
        print(f"{label:<26} id={record['identity_cosine_to_target_centroid']:.4f} "
              f"leak={record['leakage_cosine_to_source_window']:.4f} "
              f"utmos={record['utmos_predicted']:.3f} "
              f"f0={record.get('f0_median_hz', float('nan')):.1f}Hz", flush=True)
        return record

    add('source_dev_window', 'source_speaker (本人)', source_window, transcript=True)
    add('target_track9_window', 'target held-out track', target_window, transcript=False)
    for label, role, path in CANDIDATES:
        if not path.exists():
            print(f'MISSING {path}', flush=True)
            continue
        add(label, role, audit.load16(path, start=WINDOW_START, seconds=WINDOW_SECONDS), path=path)
    add('seed30_window', 'Seed-VC 30步 (离线上限参考)',
        audit.load16(audit.SEED_OUTPUT, start=1.0, seconds=WINDOW_SECONDS), path=audit.SEED_OUTPUT)

    source_text = next(r for r in records if r['label'] == 'source_dev_window').get('asr_text')
    for record in records:
        if record.get('asr_text') and source_text:
            record['content_cer_vs_source'] = audit.cer(source_text, record['asr_text'])

    def pick(label):
        return next((r for r in records if r['label'] == label), None)

    old = pick('world_old_fixed')
    summary = {
        'target_pairwise_mean': float(np.mean(pairwise)),
        'target_pairwise_min': float(np.min(pairwise)),
        'best_candidate_by_identity': max(
            (r for r in records if r['role'] not in ('source_speaker (本人)', 'target held-out track')),
            key=lambda r: r['identity_cosine_to_target_centroid'])['label'],
    }
    if old:
        for key in ('prepared_pitch', 'prepared_timbre', 'prepared_pitch_old_warp',
                    'balanced_low_shelf', 'balanced_spectral', 'seed30_window'):
            row = pick(key)
            if row:
                summary[f'{key}_minus_world_old_identity'] = (
                    row['identity_cosine_to_target_centroid'] - old['identity_cosine_to_target_centroid'])
                summary[f'{key}_minus_world_old_leakage'] = (
                    row['leakage_cosine_to_source_window'] - old['leakage_cosine_to_source_window'])

    report = {
        'kind': 'parametric_candidate_identity_audit',
        'date': '2026-10-16', 'protocol': audit.PROTOCOL,
        'read_only': True, 'audio_generated': False, 'board_touched': False, 'played': False,
        'window': {'start_s': WINDOW_START, 'seconds': WINDOW_SECONDS, 'rate': 16000,
                   'note': '所有候选与源、目标用同一窗口口径，便于横向比较'},
        'summary': summary, 'files': records, 'elapsed_seconds': time.time() - started,
        'speaker_identity_accepted': False, 'naturalness_accepted': False,
        'content_verified': False, 'board_realtime_accepted': False,
        'limitations': [
            '目标质心包含 Track8，而历史候选的注册/拟合也用过 Track5～8，因此候选与目标的分数都偏乐观，只能横向比较。',
            '单个源说话人、单个开发句、非盲评；候选音频是历史版本，未重新生成。',
            'ASR 对照为转写对转写，不是内容真值；UTMOS 为域外预测自然度，不是身份。',
            '这些候选均非“现场在板上建模”的产物，不能作为脱机构型的验收证据。',
        ],
    }
    dest = ROOT / 'report/param_candidate_audit_20261016.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('COMPLETE ' + str(dest), flush=True)


if __name__ == '__main__':
    main()
