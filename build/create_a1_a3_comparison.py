#!/usr/bin/env python3
"""生成 A1 与 A3 的 18 秒三段对照（目标 / A1 闭环 / A3-0.561），供板上播放。

顺序固定：target → a1_closed_loop → a3_identity056
每段 4.8 秒、段间 1 秒、开头 1 秒静音；共同 RMS 归一，峰值上限 0.9；输出 32 kHz PCM16。
只读既有音频，不录音、不播放。
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/generated/seed_cpu_deps'))
sys.path.insert(0, str(ROOT))
from src.reference.audio_io import downsample_16k, read_pcm_wav, write_pcm16, file_sha256  # noqa: E402

SEGMENT = 76800          # 4.8 s @ 16 kHz
SOURCE_CROP = 2.68       # A1/A3 与源对齐窗
TARGET_CROP = 11.0       # Track9 目标窗
RATE_OUT = 32000

A1 = ROOT / 'build/generated/world_register_20261016/closed_loop_arm.wav'
A3 = ROOT / 'build/generated/a3_neural/output/content_speaker01.wav'
TARGET = ROOT / 'voice_src/src_1/Track 9(1).wav'
OUT = ROOT / 'data/registrations/source_20261015/speaker01/a1_a3_comparison'


def load_window(path: Path, start_s: float) -> np.ndarray:
    rate, signal = read_pcm_wav(path)
    signal = downsample_16k(rate, signal)
    begin = int(round(start_s * 16000))
    window = signal[begin:begin + SEGMENT]
    if len(window) != SEGMENT:
        raise SystemExit(f'{path.name}: 窗口不足 {len(window)}')
    return window


def main() -> None:
    segments = [load_window(TARGET, TARGET_CROP),
                load_window(A1, SOURCE_CROP),
                load_window(A3, SOURCE_CROP)]
    if any(not np.all(np.isfinite(x)) for x in segments):
        raise SystemExit('存在非有限样本')

    rms = [float(np.sqrt(np.mean(x * x))) for x in segments]
    if min(rms) <= 1e-10:
        raise SystemExit('存在静音段')
    common = min([0.08] + [0.85 * level / max(float(np.max(np.abs(x))), 1e-12)
                           for x, level in zip(segments, rms)])

    offset = np.arange(127) - 63
    kernel = 2 * 0.225 * np.sinc(2 * 0.225 * offset) * np.hamming(127)
    kernel *= 2 / kernel.sum()

    parts, gains = [], []
    for x, level in zip(segments, rms):
        gain = common / level
        expanded = np.zeros(SEGMENT * 2)
        expanded[::2] = x * gain
        parts.append(np.convolve(expanded, kernel, mode='same'))
        gains.append(gain)

    joined = np.concatenate([np.zeros(RATE_OUT)] +
                            [part for i, part in enumerate(parts)
                             for part in ([np.zeros(RATE_OUT), part] if i else [part])])
    if np.max(np.abs(joined)) >= 1 or not np.all(np.isfinite(joined)):
        raise SystemExit('合成波形非法')

    OUT.mkdir(parents=True, exist_ok=True)
    audio = OUT / 'voice_comparison.wav'
    packed = OUT / 'voice_comparison.wav.gz'
    write_pcm16(audio, joined, RATE_OUT)
    packed.write_bytes(gzip.compress(audio.read_bytes(), compresslevel=9, mtime=0))

    record = {
        'kind': 'a1_vs_a3_listening_gate',
        'date': '2026-10-18',
        'order': ['target_track9', 'a1_closed_loop', 'a3_identity056'],
        'description': {
            'target_track9': '目标本人原声（Track9 11.0s 起 4.8s）',
            'a1_closed_loop': '现役参数化闭环输出（身份 0.190 / UTMOS 2.035）',
            'a3_identity056': 'A3 内容条件候选（身份 0.561 / UTMOS 1.401 / 字错 0.056）',
        },
        'duration_s': len(joined) / RATE_OUT,
        'rate': RATE_OUT,
        'segment_seconds': SEGMENT / 16000,
        'gap_seconds': 1.0,
        'leading_silence_seconds': 1.0,
        'source_crop_start_s': SOURCE_CROP,
        'target_crop_start_s': TARGET_CROP,
        'gains': gains,
        'peak': float(np.max(np.abs(joined))),
        'clip_fraction': 0.0,
        'sources': {'target': str(TARGET.relative_to(ROOT)).replace('\\', '/'),
                    'a1': str(A1.relative_to(ROOT)).replace('\\', '/'),
                    'a3': str(A3.relative_to(ROOT)).replace('\\', '/')},
        'source_sha256': {'target': file_sha256(TARGET), 'a1': file_sha256(A1), 'a3': file_sha256(A3)},
        'wav_sha256': file_sha256(audio),
        'gzip_sha256': file_sha256(packed),
        'speaker_identity_accepted': False,
        'limitations': '同一开发句、单源单目标；A3 为离线 CPU 产物，非板端推理。逐听判断相对偏好，不做绝对音质结论。',
    }
    (OUT / 'comparison_manifest.json').write_text(json.dumps(record, ensure_ascii=False, indent=2),
                                                  encoding='utf-8')
    print(json.dumps({k: record[k] for k in ('order', 'duration_s', 'peak', 'wav_sha256', 'gzip_sha256')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
