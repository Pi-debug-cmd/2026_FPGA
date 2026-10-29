"""Compare source/teacher ASR on train1-3; source ASR is not gold text."""
import argparse
from math import gcd
import hashlib
import json
import os
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--generation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    document = json.loads(args.generation.read_text(encoding='utf-8'))
    assert document['complete']
    assert not any(document[k] for k in ('recording4_used', 'recording5_used', 'target_track9_used'))
    assert all(r['role'] in ('train1', 'train2', 'train3') for r in document['rows'])
    for dep in ('eval_opencc_deps_20261027', 'world_deps', 'llvc_cpu_deps',
                'seed_audio_deps', 'seed_cpu_deps'):
        sys.path.insert(0, str(root / 'build/generated' / dep))
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from evaluate_seed_fixed_male_strict_20261024 import cer
    torch.set_num_threads(4)
    snapshot = next((root / '交接/核心材料/neural_reference/cache/hf/hub/models--openai--whisper-small/snapshots').glob('*'))
    processor = WhisperProcessor.from_pretrained(snapshot, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(snapshot, local_files_only=True).eval()
    result = {'kind': 'fixed_male_training_teacher_content', 'generation_sha256': sha(args.generation),
              'script_sha256': sha(Path(__file__)), 'asr': 'offline Whisper-small',
              'normalization': 'existing CER punctuation rules and real OpenCC0.1.7 t2s',
              'reference': 'source ASR; not manually verified text or validation gate', 'rows': [],
              'training': False, 'playback': False, 'board_touched': False,
              'recording4_used': False, 'recording5_used': False, 'target_track9_used': False}
    for row in document['rows']:
        record = {'role': row['role']}
        for role in ('source', 'teacher'):
            path = root / row[role + '_path']
            assert sha(path) == row[role + '_sha256'], path
            signal, rate = sf.read(path, dtype='float32', always_2d=True)
            signal = signal.mean(axis=1)
            if rate != 16000:
                factor = gcd(rate, 16000)
                signal = resample_poly(signal, 16000 // factor, rate // factor)
            assert len(signal) and np.isfinite(signal).all() and len(signal) <= 30 * 16000
            inputs = processor(signal, sampling_rate=16000, return_tensors='pt')
            with torch.inference_mode():
                ids = model.generate(inputs.input_features, language='zh', task='transcribe', max_new_tokens=256)
            record[role] = {'sha256': sha(path), 'seconds': len(signal) / 16000,
                            'asr': processor.batch_decode(ids, skip_special_tokens=True)[0].strip()}
        record['teacher_against_source_asr'] = cer(record['source']['asr'], record['teacher']['asr'])
        result['rows'].append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    chars = sum(r['teacher_against_source_asr']['reference_chars'] for r in result['rows'])
    edits = sum(r['teacher_against_source_asr']['distance'] for r in result['rows'])
    assert chars
    result['summary'] = {'source_asr_characters': chars, 'edits': edits, 'micro_cer': edits / chars}
    result['complete'] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
