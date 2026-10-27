"""Generate and transcribe a frozen public-validation content chain; no training."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('generate', 'evaluate'))
    parser.add_argument('--asset-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    generated = root / 'build/generated'
    args.output.mkdir(parents=True, exist_ok=True)
    if args.stage == 'generate':
        import torch
    for name in reversed(('eval_opencc_deps_20261027', 'llvc_cpu_deps',
                          'seed_audio_deps', 'seed_cpu_deps', 'world_deps')):
        sys.path.insert(0, str(generated / name))
    import numpy as np
    import soundfile as sf
    import torch
    torch.set_num_threads(4)
    if args.stage == 'evaluate':
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        from evaluate_seed_fixed_male_strict_20261024 import cer
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        snapshot = next((root / '交接/核心材料/neural_reference/cache/hf/hub/models--openai--whisper-small/snapshots').glob('*'))
        processor = WhisperProcessor.from_pretrained(snapshot, local_files_only=True)
        model = WhisperForConditionalGeneration.from_pretrained(snapshot, local_files_only=True).eval()
        result = json.loads((args.output / 'generation.json').read_text(encoding='utf-8'))
        previous = json.loads((generated / 'paired_teacher_audit_20261027/teacher_content_audit.json').read_text(encoding='utf-8'))
        assert previous['complete']
        old = {row['stem']: row for row in previous['rows']}
        for row in result['rows']:
            assert row['source_sha256'] == old[row['stem']]['source']['sha256']
            assert row['teacher_sha256'] == old[row['stem']]['teacher']['sha256']
            row['source'] = old[row['stem']]['source']
            row['teacher'] = old[row['stem']]['teacher']
            for variant in row['variants']:
                path = args.output / variant['file']
                assert sha(path) == variant['sha256']
                signal, rate = sf.read(path, dtype='float32')
                assert rate == 16000 and signal.ndim == 1 and np.isfinite(signal).all()
                inputs = processor(signal, sampling_rate=16000, return_tensors='pt')
                with torch.inference_mode():
                    ids = model.generate(inputs.input_features, language='zh', task='transcribe', max_new_tokens=256)
                text = processor.batch_decode(ids, skip_special_tokens=True)[0].strip()
                variant.update(asr=text, cer_against_declared=cer(row['text'], text),
                               cer_against_teacher_asr=cer(row['teacher']['asr'], text))
            print(json.dumps({'stem': row['stem'], 'edits': {
                v['kind']: v['cer_against_declared']['distance'] for v in row['variants']}}), flush=True)
            (args.output / 'evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        summary = {}
        for kind in ('source', 'teacher', 'world5', 'world20', 'student_gain1_6'):
            values = [(row[kind] if kind in ('source', 'teacher') else
                       next(v for v in row['variants'] if v['kind'] == kind))['cer_against_declared']
                      for row in result['rows']]
            chars = sum(v['reference_chars'] for v in values)
            distance = sum(v['distance'] for v in values)
            summary[kind] = {'reference_chars': chars, 'distance': distance, 'micro_cer': distance/chars}
        result.update(summary=summary, complete=True,
                      reference='declared corpus text; not independently manually verified',
                      asr='offline Whisper-small, existing CER with OpenCC0.1.7 t2s')
        (args.output / 'evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(summary), flush=True)
        return

    schema = torch.library.Library('torchvision', 'DEF')
    schema.define('nms(Tensor boxes, Tensor scores, float iou_threshold) -> Tensor')
    runtime = generated / 'hubert_world_round88_20261027/runtime/build'
    sys.path.insert(0, str(runtime))
    import train_hubert_world_teacher_round20_20261025 as base
    import train_paired_hubert_world_gru_round26_20261025 as paired
    import audit_source_prosody_round32_20261025 as prosody
    from apply_world_temporal_postfilter_round47_20261026 import interpolate, NON_F0
    checkpoint = generated / 'hubert_world_round88_20261027/paired_causal_gru.pt'
    assert sha(checkpoint) == 'e21d8175cb56a5aa3f3e7ac75578705b5deb8cb40fea07a5a73ef87d38586faa'
    cp = torch.load(checkpoint, map_location='cpu', weights_only=False)
    model = paired.ProsodyCausalWorldGRU().eval()
    model.load_state_dict(cp['model'])
    corpus = root / '交接/核心材料/board_budget_20261005/full_train_corpus_16k'
    declaration_path = corpus / 'manifest.json'
    declaration = json.loads(declaration_path.read_text(encoding='utf-8'))
    cache_root = generated / 'hubert_world_round25_20261025'
    cache_manifest_path = cache_root / 'cache_manifest.json'
    assert sha(cache_manifest_path) == cp['round25_manifest_sha256']
    cache_manifest = json.loads(cache_manifest_path.read_text(encoding='utf-8'))
    records = {r['stem']: r for r in cache_manifest['records'] if r['split'] == 'validation'}
    anchor_worlds = [base.analyze_world(base.read_16k(root/f'人物音频资料/女声/Track {n}.wav')) for n in (5,6,7,8)]
    anchor_y = np.concatenate([w['output'] for w in anchor_worlds])
    clip_lo, clip_hi = np.percentile(anchor_y, [0.1, 99.9], axis=0)
    log_sp = np.log(np.maximum(np.concatenate([w['spectrum'] for w in anchor_worlds]), 1e-8))
    voiced = anchor_y[:, paired.VUV_INDEX] > 0.5
    stats = {'log_f0_lo': float(np.percentile(anchor_y[voiced,base.SP_DIM],0.5)),
             'log_f0_hi': float(np.percentile(anchor_y[voiced,base.SP_DIM],99.5)),
             'log_sp_lo': float(np.percentile(log_sp,0.05)), 'log_sp_hi': float(np.percentile(log_sp,99.95))}
    result = {'task':'PS-20261021-10', 'kind':'public_validation_content_chain',
              'checkpoint_sha256':sha(checkpoint), 'corpus_manifest_sha256':sha(declaration_path),
              'cache_manifest_sha256':sha(cache_manifest_path), 'gain':1.6,
              'recording4_used':False, 'recording5_used':False, 'track9_used':False,
              'training':False, 'played':False, 'board_touched':False, 'rows':[]}
    for row in declaration['validation']:
        record = records[row['stem']]
        signals = {}
        for key, directory in (('src','src'),('tch','tch')):
            path = corpus/directory/PureWindowsPath(row[key]).name
            assert sha(path) == row[key+'_sha']
            signals[key] = np.fromfile(path,dtype='<f4').astype(np.float64)
        cache_path = cache_root/'cache'/record['cache']
        assert sha(cache_path) == record['cache_sha256']
        data = np.load(cache_path)
        content = data['content'].astype(np.float32)
        truth = base.analyze_world(signals['tch'])
        # Broad reconstruction bounds: isolate representation/time compression,
        # rather than introduce target-anchor clipping in the oracle branches.
        reconstruct_stats = {'log_f0_lo':float(truth['output'][:,base.SP_DIM].min()-1),
                             'log_f0_hi':float(truth['output'][:,base.SP_DIM].max()+1),
                             'log_sp_lo':-100.0,'log_sp_hi':100.0}
        oracle5 = truth['output'].copy()
        oracle20 = interpolate(data['target'].astype(np.float32),len(oracle5))
        for value in (oracle5,oracle20):
            value[:,paired.VUV_INDEX]=(value[:,paired.VUV_INDEX]-0.5)*8
        x = (((content-cp['pca_mean'])@cp['pca_projection']-cp['x_mean'])/cp['x_std']).astype(np.float32)
        p = prosody.resample_rows(prosody.source_prosody(signals['src']),len(x))
        x = np.concatenate((x, (p-cp['prosody_mean'])/cp['prosody_std']),axis=1).astype(np.float32)
        with torch.inference_mode():
            raw = model(torch.from_numpy(x[None]))[0].numpy()
        continuous = raw*cp['y_std']+cp['y_mean']
        for group in NON_F0:
            center = continuous[:,group].mean(axis=0,keepdims=True)
            continuous[:,group] = center+1.6*(continuous[:,group]-center)
        prediction = np.clip(interpolate(continuous,len(oracle5)),clip_lo,clip_hi)
        probability = 1/(1+np.exp(-np.clip(raw[:,paired.VUV_INDEX],-20,20)))
        prediction[:,paired.VUV_INDEX]=(interpolate(probability[:,None],len(oracle5))[:,0]-0.5)*8
        out = {'stem':row['stem'],'speaker':row['speaker'],'text':row['text'],
               'source_sha256':row['src_sha'],'teacher_sha256':row['tch_sha'],'variants':[]}
        for kind,value,bounds in (('world5',oracle5,reconstruct_stats),('world20',oracle20,reconstruct_stats),('student_gain1_6',prediction,stats)):
            wave, synthesis = base.synthesize(value,bounds)
            assert np.isfinite(wave).all()
            path = args.output/f'{row["stem"]}_{kind}.wav'
            sf.write(path,wave,16000,subtype='PCM_16')
            out['variants'].append({'kind':kind,'file':path.name,'sha256':sha(path),
                                    'samples':len(wave),'synthesis':synthesis})
        result['rows'].append(out)
        print(row['stem'],flush=True)
    (args.output/'generation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
