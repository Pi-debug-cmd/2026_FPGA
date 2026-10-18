"""Unconstrained ASR/speaker screening, never a substitute for human hearing."""
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker, FRONT
from prepare_aligned_teacher_pilot_20261004 import read_audio,sha,hanzi
from check_phasefree_student_20261004 import distance
from pathlib import Path
import json,torch,numpy as np,sentencepiece as spm,onnxruntime as ort,argparse
import torchaudio.compliance.kaldi as kaldi
BASE=Path(__file__).resolve().parent
OUT=BASE.parent/'board_budget_20261005/small96_training'

def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--outname',default='small96_training');parser.add_argument('--validation-only',action='store_true');args=parser.parse_args()
    assert args.outname in ['small96_training','small96_identity_training']
    OUT=BASE.parent/'board_budget_20261005'/args.outname
    decision=json.loads((OUT/'decision.json').read_text(encoding='utf-8'))
    checker=PinyinChecker()
    sp=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
    weights=next(r for r in json.loads((BASE/'cross_evaluators/manifest.json').read_text(encoding='utf-8')) if r['evaluator'].startswith('WeSpeaker'))['weight']
    assert sha(weights['path'])==weights['sha256']
    opts=ort.SessionOptions();opts.intra_op_num_threads=4
    speaker=ort.InferenceSession(weights['path'],sess_options=opts,providers=['CPUExecutionProvider'])
    def embed(path):
        x=read_audio(path);x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
        features=kaldi.fbank(torch.from_numpy(x*32768)[None],num_mel_bins=80,frame_length=25,frame_shift=10,sample_frequency=16000,window_type='hamming',dither=0.)
        features=(features-features.mean(dim=0))[None].numpy().astype('float32')
        v=speaker.run(None,{'feats':features})[0][0];return v/max(float(np.linalg.norm(v)),1e-8)
    reference=embed('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
    def decode(path):
        x=read_audio(path);x=x/max(float(np.max(np.abs(x))),1e-8)
        with torch.inference_mode():f,l=checker.frontend(torch.from_numpy(x)[None],torch.tensor([len(x)]))
        h,p,n=checker.session.run(['hanzi_log_probs','pinyin_log_probs','encoder_lens'],dict(feats=f.numpy().astype('float32'),feats_lens=l.numpy().astype('int32')))
        outputs=[]
        for lp in [h,p]:
            ids=[];old=0
            for frame in lp[:int(n[0]),0]:
                token=int(frame.argmax())
                if token and token!=old:ids.append(token)
                old=token
            outputs.append(ids)
        return dict(text=sp.decode(outputs[0]),pinyin=[checker.id2token[t] for t in outputs[1]])
    cases=[]
    for row in decision['heldout_outputs']:
        if args.validation_only and row['split']!='validation':continue
        records=[]
        for kind,path in [('source',row['path']),('teacher',row['teacher_path']),('student',row['student_path'])]:
            decoded=decode(path);r=dict(kind=kind,path=path,sha256=sha(path),**decoded,
                hanzi_edits=distance(hanzi(decoded['text']),hanzi(row['text'])),
                target_cosine=float(embed(path)@reference),human_acceptance=False)
            records.append(r)
        source=records[0]
        for r in records[1:]:r['pinyin_edits_to_source']=distance(r['pinyin'],source['pinyin'])
        cases.append(dict(filename=row['filename'],speaker=row['speaker'],split=row['split'],publisher_text=row['text'],records=records))
        print('SCREENED',row['filename'],row['split'],[(r['kind'],r['hanzi_edits'],round(r['target_cosine'],3)) for r in records],flush=True)
        (OUT/'heldout_screening.json').write_text(json.dumps(dict(cases=cases,complete=False),ensure_ascii=False,indent=2),encoding='utf-8')
    summary=[]
    for split in (['validation'] if args.validation_only else ['validation','test']):
        for kind in ['source','teacher','student']:
            subset=[c for c in cases if c['split']==split];records=[r for c in subset for r in c['records'] if r['kind']==kind]
            chars=sum(len(hanzi(c['publisher_text'])) for c in subset)
            summary.append(dict(split=split,kind=kind,characters=chars,edits=sum(r['hanzi_edits'] for r in records),
                                mean_target_cosine=float(np.mean([r['target_cosine'] for r in records]))))
    report=dict(cases=cases,summary=summary,complete=True,subjective_acceptance=False,
                asr_is_not_pronunciation_approval=True,speaker_cosine_is_not_perceptual_similarity=True,
                no_test_checkpoint_selection=True,source_speaker_enrollment=False,
                auxiliary_speaker_loss_used=decision.get('auxiliary_speaker_loss_used',False),
                wespeaker_is_not_independent_after_training=decision.get('auxiliary_speaker_loss_used',False))
    (OUT/'heldout_screening.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SCREEN_DONE',json.dumps(summary),flush=True)
if __name__=='__main__':main()
