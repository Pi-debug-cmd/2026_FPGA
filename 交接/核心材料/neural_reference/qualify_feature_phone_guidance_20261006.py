"""Qualification on reused development speakers, not a blind final test."""
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker
from prepare_aligned_teacher_pilot_20261004 import read_audio
from fargan_feature_phone_model_20261006 import FeaturePhoneNet
from pathlib import Path
import numpy as np,torch,json
from check_phasefree_student_20261004 import distance
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';out=budget/'fargan_phone_guidance'
cp=torch.load(out/'feature_phone_step3000.pt',map_location='cpu',weights_only=False)
model=FeaturePhoneNet(cp['mean'],cp['std'],cp['classes']);model.load_state_dict(cp['model']);model.eval()
vocab=json.loads((out/'body_vocabulary.json').read_text(encoding='utf-8'));lookup=np.array(vocab['pinyin_to_body']);checker=PinyinChecker()
manifest=json.loads((budget/'fargan_corpus_expanded/manifest.json').read_text(encoding='utf-8'));rows=[]
for row in manifest['files']:
    if row['split']!='validation':continue
    x=read_audio(row['path']);x=x/max(float(np.max(np.abs(x))),1e-8)
    with torch.inference_mode():f,l=checker.frontend(torch.from_numpy(x)[None],torch.tensor([len(x)]))
    p,n=checker.session.run(['pinyin_log_probs','encoder_lens'],dict(feats=f.numpy().astype('float32'),feats_lens=l.numpy().astype('int32')))
    probs=np.exp(p[:int(n[0]),0]);body=np.zeros((len(probs),cp['classes']),dtype='float32')
    for k,b in enumerate(lookup):body[:,b]+=probs[:,k]
    records=[]
    for kind,path in [('source',row['source_features']),('teacher',row['teacher_features'])]:
        frames=np.fromfile(path,dtype='float32').reshape(-1,20);count=min(len(frames)//6,len(body))
        with torch.inference_mode():logits=model(torch.from_numpy(frames[:count*6])[None])[0]
        truth=body[:count];positive=truth[:,0]<.6;pred=logits.argmax(-1).numpy();gold=truth.argmax(-1)
        correct=int(np.count_nonzero(pred[positive]==gold[positive]));total=int(positive.sum())
        def collapse(ids):
            result=[];previous=0
            for k in ids:
                if k and k!=previous:result.append(int(k))
                previous=k
            return result
        expected=collapse(gold);decoded=collapse(pred)
        records.append(dict(kind=kind,correct=correct,total=total,positive_body_accuracy=correct/max(total,1),
                            body_sequence_edits=distance(decoded,expected),body_sequence_length=len(expected),
                            decoded_bodies=[vocab['tokens'][k] for k in decoded],
                            source_asr_bodies=[vocab['tokens'][k] for k in expected]))
    rows.append(dict(filename=row['filename'],gender=row['gender'],records=records));print('PHONE_QUALIFY',row['filename'],records,flush=True)
summary=[]
for kind in ('source','teacher'):
    selected=[r for row in rows for r in row['records'] if r['kind']==kind]
    correct=sum(r['correct'] for r in selected);total=sum(r['total'] for r in selected)
    edits=sum(r['body_sequence_edits'] for r in selected);length=sum(r['body_sequence_length'] for r in selected)
    summary.append(dict(kind=kind,correct=correct,total=total,accuracy=correct/max(total,1),
                        body_sequence_edits=edits,body_sequence_length=length,sequence_error_rate=edits/max(length,1)))
# These are predeclared engineering diagnostic thresholds, not published quality
# guarantees. Even passing does not authorize deployment or human acceptance.
passed=summary[0]['accuracy']>=.65 and summary[1]['accuracy']>=.55
report=dict(complete=True,rows=rows,summary=summary,diagnostic_gate_passed=passed,
            validation_used_only_for_diagnostic=True,test_audio_used=False,
            not_independent_of_asr_teacher=True,not_human_acceptance=True,
            thresholds=dict(source_accuracy=.65,teacher_accuracy=.55))
(out/'qualification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('PHONE_QUALIFICATION',json.dumps(report['summary']),passed,flush=True)
