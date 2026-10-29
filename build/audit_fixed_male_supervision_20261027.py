"""Verify permitted source training files and existing paired supervision.

Reads only male recordings 1-3 and public training/validation pairs; no audio I/O.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    repo = Path(__file__).resolve().parents[1]
    frozen = json.loads((repo / 'report/fallback_one_to_one_assets_20261021.json').read_text(encoding='utf-8'))
    male = []
    for row in frozen['fixed_source']['files']:
        if row['role'] not in ('train1', 'train2', 'train3'):
            continue
        path = root / row['path']
        actual = sha(path)
        assert actual == row['sha256'] and path.stat().st_size == row['bytes'], path
        male.append({'role': row['role'], 'path': row['path'], 'sha256': actual,
                     'bytes': path.stat().st_size})
    corpus = root / '交接/核心材料/board_budget_20261005/full_train_corpus_16k'
    manifest_path = corpus / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert manifest['complete']
    splits = {}
    for split in ('train', 'validation'):
        rows = manifest[split]
        for row in rows:
            for role in ('src', 'tch'):
                path = corpus / role / (row['stem'] + '.f32')
                assert sha(path) == row[role + '_sha'], path
                assert path.stat().st_size == row['n'] * 4, path
        splits[split] = {'pairs': len(rows), 'seconds': sum(r['n'] for r in rows) / 16000,
                         'speaker_counts': dict(sorted(Counter(r['speaker'] for r in rows).items())),
                         'all_stems_public_ssb': all(r['stem'].startswith('SSB') for r in rows),
                         'fixed_male_labelled_rows': sum(r['speaker'] == 'Fixed-Male' for r in rows)}
    timing_path = root / '交接/核心材料/board_budget_20261005/teacher_content_timing/report.json'
    timing = json.loads(timing_path.read_text(encoding='utf-8'))
    timing_stems = {Path(r['filename']).stem for r in timing['records']}
    timing_overlap = {s: sum(r['stem'] in timing_stems for r in manifest[s])
                      for s in ('train', 'validation')}
    neural = root / '交接/核心材料/neural_reference'
    dependencies = ['CosyVoice_reference', 'cosyvoice3_assets/repository_metadata.json',
                    'cosyvoice3_assets/manifest.json']
    model_dir = 'cosyvoice3_assets/FunAudioLLM__Fun-CosyVoice3-0.5B-2512/'
    dependencies += [model_dir + name for name in ('cosyvoice3.yaml', 'campplus.onnx',
                     'speech_tokenizer_v3.onnx', 'llm.pt', 'flow.pt', 'hift.pt')]
    result = {
        'kind': 'fixed_male_supervision_inventory', 'task': 'PS-20261021-10',
        'script_sha256': sha(Path(__file__)), 'male_train_files': male,
        'corpus_manifest_sha256': sha(manifest_path), 'splits': splits,
        'verified_public_audio_files': 2 * sum(len(manifest[s]) for s in splits),
        'teacher_dependencies_at_historical_expected_locations':
            [{'relative_path': p, 'exists': (neural / p).exists()} for p in dependencies],
        'historical_timing_report_sha256': sha(timing_path),
        'historical_timing_rows': len(timing['records']),
        'historical_timing_filename_overlap': timing_overlap,
        'timing_limitation': 'Filename overlap is not waveform/hash or phoneme-alignment equivalence. '
                             'Historical report uses WAV hashes; current corpus uses resampled float32.',
        'membership_limitation': 'Verified manifest labels/stems, not an exhaustive decoded-audio '
                                'duplicate search. No fixed-male paired target was identified.',
        'recording4_used': False, 'recording5_used': False, 'target_track9_used': False,
        'training_run': False, 'playback': False, 'board_touched': False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
