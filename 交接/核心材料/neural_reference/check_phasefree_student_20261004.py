"""Frozen free-ASR and speaker diagnostics on four held-out voices, no acceptance."""
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker, FRONT
from prepare_aligned_teacher_pilot_20261004 import read_audio,sha,hanzi
from pilot_phasefree_student_20261004 import OUT,BASE
import json,torch,numpy as np,sentencepiece as spm,onnxruntime as ort
import torchaudio.compliance.kaldi as kaldi

def distance(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        new=[i]
        for j,y in enumerate(b,1):new.append(min(new[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=new
    return row[-1]

def main():
    d=json.loads((OUT/'decision.json').read_text(encoding='utf8'));checker=PinyinChecker()
    sp=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
    manifest=json.loads((BASE/'cross_evaluators/manifest.json').read_text(encoding='utf8'))
    weights=next(r for r in manifest if r['evaluator'].startswith('WeSpeaker'))['weight']
    assert sha(weights['path'])==weights['sha256']
    opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
    speaker=ort.InferenceSession(weights['path'],sess_options=opts,providers=['CPUExecutionProvider'])
    def embed(path):
        x=read_audio(path);vectors=[];sizes=[]
        for start in range(0,len(x),96000):
            part=x[start:start+96000]
            if len(part)<24000:continue
            part=part*.04/max(float(np.sqrt(np.mean(part*part))),1e-8)
            feats=kaldi.fbank(torch.from_numpy(part*32768)[None],num_mel_bins=80,frame_length=25,frame_shift=10,sample_frequency=16000,window_type='hamming',dither=0.)
            feats=(feats-feats.mean(dim=0))[None].numpy().astype('float32')
            v=speaker.run(None,{'feats':feats})[0][0];v=v/max(float(np.linalg.norm(v)),1e-8)
            vectors.append(v);sizes.append(len(part))
        v=np.average(vectors,axis=0,weights=sizes);return v/np.linalg.norm(v)
    reference=np.mean([embed(f'D:/总进度/目标人物语音/Track {n}.wav') for n in [5,6,7,8]],axis=0)
    reference/=np.linalg.norm(reference)
    def decode(path):
        x=read_audio(path);x=x/(float(np.max(np.abs(x)))+1e-8);torch.manual_seed(20261004)
        with torch.inference_mode():f,l=checker.frontend(torch.from_numpy(x)[None],torch.tensor([len(x)]))
        hp,pp,lengths=checker.session.run(['hanzi_log_probs','pinyin_log_probs','encoder_lens'],dict(feats=f.numpy().astype('float32'),feats_lens=l.numpy().astype('int32')))
        outputs=[]
        for lp in [hp,pp]:
            ids=[];previous=0
            for frame in lp[:int(lengths[0]),0]:
                token=int(frame.argmax())
                if token and token!=previous:ids.append(token)
                previous=token
            outputs.append(ids)
        return dict(raw_hanzi=sp.decode(outputs[0]),pinyin=[checker.id2token[t] for t in outputs[1]])
    rows=[]
    for case in d['heldout_streaming_evaluation']:
        inputs=[dict(kind='genuine_source',path=case['source_path'],sha256=case['source_sha256'])]+case['streaming_outputs']
        checked=[]
        for r in inputs:
            assert sha(r['path'])==r['sha256'];free=decode(r['path']);v=embed(r['path'])
            checked.append(dict(r,**free,hanzi_edits_to_publisher=distance(hanzi(free['raw_hanzi']),hanzi(case['publisher_text'])),
                wespeaker_raw_cosine_to_target=float(v@reference),phonetic_approval=False,human_acceptance=False))
        for r in checked[1:]:r['pinyin_edit_distance_to_source']=distance(r['pinyin'],checked[0]['pinyin'])
        rows.append(dict(label=case['label'],expected_text=case['publisher_text'],outputs=checked))
        print('CHECKED',case['label'],[(r['kind'],r['hanzi_edits_to_publisher'],round(r['wespeaker_raw_cosine_to_target'],4)) for r in checked],flush=True)
    summaries=[]
    for kind in ['genuine_source','baseline','candidate']:
        records=[r for c in rows for r in c['outputs'] if r['kind']==kind]
        summaries.append(dict(kind=kind,hanzi_edits=sum(r['hanzi_edits_to_publisher'] for r in records),
            mean_target_cosine=float(np.mean([r['wespeaker_raw_cosine_to_target'] for r in records])),
            pinyin_edits_to_source=sum(r.get('pinyin_edit_distance_to_source',0) for r in records)))
    report=dict(status='frozen_heldout_screening_complete',cases=rows,summary=summaries,
        checkpoint_sha256=d['checkpoint_sha256'],no_hyperparameter_or_checkpoint_selection_on_heldout=True,
        speaker_score_not_perceptual_similarity_acceptance=True,asr_agreement_not_pronunciation_acceptance=True,
        validated_automatic_phone_checker=False,no_audition_promoted=True,board_deployed=False)
    (OUT/'heldout_screening.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('HELDOUT SCREENING COMPLETE',summaries,flush=True)

if __name__=='__main__':main()
