"""Audit source/teacher content on the eight declared public validation pairs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import sys


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    generated = root / 'build/generated'
    for dep in ('eval_opencc_deps_20261027', 'world_deps', 'llvc_cpu_deps',
                'seed_audio_deps', 'seed_cpu_deps'):
        sys.path.insert(0, str(generated / dep))
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import numpy as np
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from evaluate_seed_fixed_male_strict_20261024 import cer

    torch.set_num_threads(4)
    corpus = root / '交接/核心材料/board_budget_20261005/full_train_corpus_16k'
    manifest_path = corpus / 'manifest.json'
    document = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert document['complete'] and not document.get('target_track9_used', False)
    rows = document['validation']
    assert len(rows) == 8
    assert not ({row['speaker'] for row in rows} & {row['speaker'] for row in document['train']})
    snapshot = next((root / '交接/核心材料/neural_reference/cache/hf/hub/models--openai--whisper-small/snapshots').glob('*'))
    processor = WhisperProcessor.from_pretrained(snapshot, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(snapshot, local_files_only=True).eval()

    def transcribe(signal):
        inputs = processor(signal, sampling_rate=16000, return_tensors='pt')
        with torch.inference_mode():
            ids = model.generate(inputs.input_features, language='zh', task='transcribe', max_new_tokens=256)
        return processor.batch_decode(ids, skip_special_tokens=True)[0].strip()

    result = {'task': 'PS-20261021-10', 'kind': 'public_validation_teacher_content_audit',
              'manifest_sha256': sha(manifest_path), 'asr': 'offline Whisper-small',
              'normalization': 'OpenCC0.1.7 t2s and existing evaluator punctuation rules',
              'reference': 'declared corpus text; not independently manually verified',
              'recording4_used': False, 'recording5_used': False, 'track9_used': False,
              'training': False, 'played': False, 'board_touched': False, 'rows': []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for row in rows:
        record = {'stem': row['stem'], 'speaker': row['speaker'], 'declared_text': row['text']}
        for role, directory, key in (('source', 'src', 'src'), ('teacher', 'tch', 'tch')):
            path = corpus / directory / PureWindowsPath(row[key]).name
            assert sha(path) == row[key + '_sha']
            signal = np.fromfile(path, dtype='<f4')
            assert len(signal) == row['n'] and np.isfinite(signal).all()
            text = transcribe(signal)
            record[role] = {'sha256': sha(path), 'samples': len(signal), 'asr': text,
                            'cer_against_declared': cer(row['text'], text)}
        record['teacher_cer_against_source_asr'] = cer(record['source']['asr'], record['teacher']['asr'])
        result['rows'].append(record)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(record, ensure_ascii=False), flush=True)
    result['summary'] = {}
    for role in ('source', 'teacher'):
        chars = sum(row[role]['cer_against_declared']['reference_chars'] for row in result['rows'])
        distance = sum(row[role]['cer_against_declared']['distance'] for row in result['rows'])
        result['summary'][role] = {'reference_chars': chars, 'distance': distance, 'micro_cer': distance / chars}
    result['complete'] = True
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['summary']), flush=True)


if __name__ == '__main__':
    main()
