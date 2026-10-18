"""Mandarin identity and predicted naturalness diagnostics, never acceptance."""
from pathlib import Path
import hashlib, json, os, sys, time
import numpy as np
import soundfile as sf
import torch
import torchaudio
import onnxruntime as ort
import run_rvc_pilot as pilot
import argparse
from pronunciation_review_gate import annotate_report
pilot.settings()
BASE=Path(__file__).resolve().parent
ASSETS=BASE/'cross_evaluators'
PRIOR=Path('D:/总进度/目标人物分析/自动评估与改进')
OUT=Path('D:/总进度/目标人物分析/中文交叉评估')
OUT.mkdir(exist_ok=True)
CACHE=OUT/'cache'; CACHE.mkdir(exist_ok=True)
MANIFEST=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))
torch.set_num_threads(4)
SAME=Path('D:/总进度/目标人物分析/素材同文本普通声转换对比')
TARGET=Path('D:/总进度/目标人物语音')

def read(path):
    x,sr=sf.read(path,dtype='float32')
    if x.ndim==2: x=x.mean(axis=1)
    if not np.isfinite(x).all() or float(np.sqrt(np.mean(x*x)))<1e-6: raise RuntimeError('Invalid audio: '+str(path))
    tensor=torch.from_numpy(x.copy()).unsqueeze(0)
    if sr!=16000: tensor=torchaudio.functional.resample(tensor,sr,16000)
    return tensor[0].numpy()

def chunks(x):
    for start in range(0,len(x),96000):
        clip=x[start:start+96000]
        if len(clip)>=24000 and np.sqrt(np.mean(clip*clip))>=.001: yield start,clip

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--extra',type=Path)
    args=parser.parse_args()
    start_time=time.time()
    metadata={x['evaluator']:x for x in MANIFEST}
    wes=next(x for x in MANIFEST if x['evaluator'].startswith('WeSpeaker'))
    ut=next(x for x in MANIFEST if x['evaluator'].startswith('UTMOS'))
    session_options=ort.SessionOptions(); session_options.intra_op_num_threads=4; session_options.inter_op_num_threads=1
    session=ort.InferenceSession(wes['weight']['path'],sess_options=session_options,providers=['CPUExecutionProvider'])
    sys.path.insert(0,ut['source_directory'])
    from speechmos.utmos22.strong.model import UTMOS22Strong
    model=UTMOS22Strong()
    model.load_state_dict(torch.load(ut['weight']['path'],map_location='cpu',weights_only=True))
    model=model.to('cuda').eval()
    source_hash=hashlib.sha256((Path(ut['source_directory'])/'speechmos/utmos22/strong/model.py').read_bytes()).hexdigest()
    protocol='mono16k-6s-nonoverlap-tail1.5s-fbank80hamming-cmn-noVAD-rms0.04-utmosFP32-v1'
    cache_key=hashlib.sha256((protocol+wes['weight']['sha256']+ut['weight']['sha256']+source_hash).encode()).hexdigest()[:16]
    def evaluate(path):
        digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        dest=CACHE/(cache_key+'_'+digest+'.npz')
        if dest.exists():
            loaded=np.load(dest)
            return loaded['vector'],json.loads(str(loaded['stats']))
        x=read(path); embeddings=[]; scores=[]; weights=[]; segment_records=[]
        for position,clip in chunks(x):
            # Common level for both evaluators; no change to original WAVs.
            normalized=clip*.04/max(float(np.sqrt(np.mean(clip*clip))),1e-8)
            feat=torchaudio.compliance.kaldi.fbank(torch.from_numpy(normalized*32768).unsqueeze(0),
                num_mel_bins=80,frame_length=25,frame_shift=10,sample_frequency=16000,
                window_type='hamming',dither=0.0)
            feat=(feat-feat.mean(dim=0)).unsqueeze(0).numpy().astype('float32')
            vector=session.run(None,{'feats':feat})[0][0]
            vector=vector/max(float(np.linalg.norm(vector)),1e-9)
            with torch.inference_mode():
                score=float(model(torch.from_numpy(normalized).unsqueeze(0).to('cuda'),16000).item())
            if not np.isfinite(vector).all() or not np.isfinite(score): raise RuntimeError('Nonfinite evaluator output')
            embeddings.append(vector); scores.append(score); weights.append(len(clip))
            segment_records.append(dict(start_seconds=position/16000,seconds=len(clip)/16000,utmos_predicted=score))
        if not embeddings: raise RuntimeError('No valid segments: '+str(path))
        vector=np.average(embeddings,axis=0,weights=weights).astype('float32')
        vector/=np.linalg.norm(vector)
        stats=dict(sha256=digest,seconds=len(x)/16000,utmos_predicted=float(np.average(scores,weights=weights)),
                   utmos_segment_std=float(np.std(scores)),segments=segment_records)
        np.savez(dest,vector=vector,stats=json.dumps(stats))
        return vector,stats
    targets=[]
    for number in range(5,10):
        path=TARGET/f'Track {number}.wav'
        vector,stats=evaluate(path)
        targets.append(dict(label=f'target_track{number}',path=str(path),role='target_reference' if number<9 else 'reused_target_diagnostic',vector=vector,stats=stats))
        print('Reference '+str(number)+' MOS '+str(round(stats['utmos_predicted'],3)),flush=True)
    references=np.stack([x['vector'] for x in targets[:4]])
    centroid=references.mean(axis=0); centroid/=np.linalg.norm(centroid)
    items=json.loads((PRIOR/'candidate_items.json').read_text(encoding='utf-8'))
    if args.extra: items.extend(json.loads(args.extra.read_text(encoding='utf-8')))
    baseline=json.loads((PRIOR/'baseline_评估记录.json').read_text(encoding='utf-8'))
    for label,name,role in [('ordinary_same_text','普通声_转换前.wav','different_identity_tts'),
                            ('user_rejected_e60_same_text','普通声_转换成目标人物.wav','user_rejected_conversion'),
                            ('target9_same_text','目标人物原声_试听.wav','reused_target_diagnostic')]:
        items.insert(0,dict(label=label,path=str(SAME/name),role=role))
    for row in baseline['files']:
        if row['label'].startswith('source_'):
            items.insert(0,dict(label=row['label'],path=row['path'],role='different_identity_real'))
    records=[]
    for row in targets:
        vector=row['vector']; record={k:v for k,v in row.items() if k not in ['vector','stats']}
        # Reference membership makes centroid score optimistic; cross-reference score is separate.
        others=[x['vector'] for x in targets[:4] if x['label']!=row['label']]
        record.update(row['stats'],wespeaker_raw_cosine_to_centroid=float(vector@centroid),
                      wespeaker_cli_scaled_cosine=float((vector@centroid+1)/2),
                      mean_cosine_to_other_target_tracks=float(np.mean([vector@v for v in others])))
        records.append(record)
    for item in items:
        vector,stats=evaluate(item['path']); cosine=float(vector@centroid)
        record={**item,**stats,'wespeaker_raw_cosine_to_centroid':cosine,
                'wespeaker_cli_scaled_cosine':(cosine+1)/2,
                'mean_cosine_to_target_tracks':float(np.mean(references@vector))}
        records.append(record)
        print(f'{item["label"]}: cosine={cosine:.4f}, predictedMOS={stats["utmos_predicted"]:.3f}',flush=True)
        intermediate=dict(status='running',files=records,protocol=protocol)
        (OUT/'运行中记录.json').write_text(json.dumps(intermediate,ensure_ascii=False,indent=2),encoding='utf-8')
    groups=[]
    for group in sorted({x['group'] for x in records if x.get('group')}):
        rows=[x for x in records if x.get('group')==group]
        groups.append(dict(group=group,inputs=len(rows),mean_wespeaker_cosine=float(np.mean([x['wespeaker_raw_cosine_to_centroid'] for x in rows])),
                    minimum_wespeaker_cosine=min(x['wespeaker_raw_cosine_to_centroid'] for x in rows),
                    mean_utmos=float(np.mean([x['utmos_predicted'] for x in rows])),minimum_utmos=min(x['utmos_predicted'] for x in rows)))
    same=[float(references[i]@references[j]) for i in range(4) for j in range(i+1,4)]
    report=dict(status='complete',models=MANIFEST,protocol=protocol,utmos_source_sha256=source_hash,
        audio_uploaded=False,board_deployed=False,subjective_acceptance=False,
        elapsed_seconds=time.time()-start_time,target_pairwise_raw_cosines=same,
        target_pairwise_mean=float(np.mean(same)),target_pairwise_min=float(np.min(same)),
        limitations=['Scores are diagnostics, not percent likeness or acceptance.',
          'UTMOS is predicted naturalness, not identity; Mandarin domain suitability is uncalibrated.',
          'Target membership inflates centroid self scores; use pairwise/heldout diagnostics.',
          'Track9 has already been repeatedly used for diagnostics; it is not a clean final test.',
          'Two real source identities and one TTS voice do not establish arbitrary-speaker conversion.',
          'Chunking, level normalization and no-VAD choices differ from whole-utterance CLI.'],
        groups=groups,files=records)
    annotate_report(report)
    dest=OUT/'中文交叉评估结果.json'
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'运行中记录.json').write_text(json.dumps(dict(status='complete',final_report=str(dest)),ensure_ascii=False,indent=2),encoding='utf-8')
    print('COMPLETE '+str(dest),flush=True)

if __name__=='__main__': main()
