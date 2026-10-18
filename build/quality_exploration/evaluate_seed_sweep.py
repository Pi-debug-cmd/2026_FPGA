"""Evaluate all registered-prompt Seed teacher outputs with correctly aligned source windows."""
from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'build'))
import audit_seed_reference_20261016 as audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path,
                        default=ROOT / 'report/quality_exploration_seed_sweep_20261018.json')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'report/quality_exploration_seed_sweep_metrics_20261018.json')
    args = parser.parse_args()
    manifest_path = args.manifest
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    evaluators = audit.Evaluators()

    target_vectors = []
    for name in audit.TARGET_TRACKS:
        target_vectors.append(evaluators.wespeaker(audit.load16(audit.VOICE / name))[0])
    centroid = np.stack(target_vectors).mean(axis=0)
    centroid /= np.linalg.norm(centroid)

    source_start = 2.68
    candidate_start = 1.0
    seconds = 4.8
    source = audit.load16(audit.BASE / 'holdout.wav', start=source_start, seconds=seconds)
    source_vector = evaluators.wespeaker(source)[0]
    source_text = evaluators.transcribe(source)
    rows = []
    for item in manifest['outputs']:
        audio = audit.load16(ROOT / item['path'], start=candidate_start, seconds=seconds)
        vector, _ = evaluators.wespeaker(audio)
        text = evaluators.transcribe(audio)
        rows.append({
            'cfg': item['cfg'], 'path': item['path'], 'sha256': item['sha256'],
            'identity_cosine_to_target_centroid': float(vector @ centroid),
            'leakage_cosine_to_source_window': float(vector @ source_vector),
            'utmos_predicted': evaluators.naturalness(audio),
            'asr_text': text, 'content_cer_vs_source': audit.cer(source_text, text),
            **audit.f0_stats(audio),
        })
    report = {
        'kind': 'seed_registered_prompt_objective_evaluation', 'date': '2026-10-18',
        'protocol': {
            'candidate_window': {'start_s': candidate_start, 'seconds': seconds},
            'source_reference_window': {'start_s': source_start, 'seconds': seconds},
            'target_centroid_tracks': audit.TARGET_TRACKS,
            'source_asr_text': source_text,
        },
        'rows': rows,
        'historical_single_track8_prompt': {
            'cfg': .7, 'identity': .5509127618939071, 'leakage': .020488953208088606,
            'utmos': 2.7361302375793457, 'cer': .1111111111111111,
            'note': 'Historical aligned-window result; Track8 was both prompt and part of centroid, so identity is optimistic.',
        },
        'played': False, 'board_touched': False,
        'accepted': False,
        'limitations': [
            'Objective metrics on one existing development source do not establish multi-source generalization.',
            'AI-like artifacts require a separately authorized listening test.',
            'Target tracks 5-8 construct both registration prompt and evaluation centroid; Track9 remains held out from registration.',
        ],
    }
    output = args.output
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
