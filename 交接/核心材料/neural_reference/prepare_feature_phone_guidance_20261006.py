"""Offline unprompted source-pinyin posteriors for training-only content guidance.
No validation/test audio is read. No prescribed transcript is sent to ASR.
"""
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,MODEL
from prepare_aligned_teacher_pilot_20261004 import read_audio
from pathlib import Path
import torch,numpy as np,json,re,time,hashlib

base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';out=budget/'fargan_phone_guidance';out.mkdir(exist_ok=True)
corpus=json.loads((budget/'fargan_corpus_expanded/manifest.json').read_text(encoding='utf-8'))
checker=PinyinChecker();tokens=[checker.id2token[i] for i in range(len(checker.vocabulary))]
bodies=['<blank>']+sorted({re.sub(r'[0-5]$','',t) for t in tokens if t!='<blank>'})
lookup=np.array([bodies.index(re.sub(r'[0-5]$','',t)) for t in tokens],dtype='int64')
(out/'body_vocabulary.json').write_text(json.dumps(dict(tokens=bodies,source_pinyin_tokens=tokens,pinyin_to_body=lookup.tolist()),ensure_ascii=False,indent=2),encoding='utf-8')
items=[dict(r,case_id=Path(r['filename']).stem,kind='paired') for r in corpus['files'] if r['split']=='train']
items += [dict(r,case_id='target_'+str(i),kind='target',source_features=r['features']) for i,r in enumerate(corpus['target_training'])]
begin=time.monotonic();records=[]
for index,row in enumerate(items):
    path=out/(row['case_id']+'.npz');digest=hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()
    cached=False
    if path.exists():
        with np.load(path) as old:cached=str(old['source_sha256'])==digest
    if not cached:
        x=read_audio(row['path']);x=x/max(float(np.max(np.abs(x))),1e-8)
        with torch.inference_mode():features,lens=checker.frontend(torch.from_numpy(x)[None],torch.tensor([len(x)]))
        p,n=checker.session.run(['pinyin_log_probs','encoder_lens'],dict(feats=features.numpy().astype('float32'),feats_lens=lens.numpy().astype('int32')))
        assert int(n[0])==int(lens[0]),'Unexpected ASR timing contract'
        probs=np.exp(p[:int(n[0]),0]);body=np.zeros((len(probs),len(bodies)),dtype='float32')
        for k,b in enumerate(lookup):body[:,b]+=probs[:,k]
        assert np.isfinite(body).all() and np.max(np.abs(body.sum(1)-1))<1e-3
        np.savez_compressed(path,body_posteriors=body,source_sha256=digest,frame_period_seconds=.06)
    records.append(dict(row,posterior_path=str(path),source_sha256=digest))
    if (index+1)%10==0 or index==0 or index==len(items)-1:
        print('PHONE_LABELS',json.dumps(dict(completed=index+1,total=len(items),seconds=time.monotonic()-begin,cached=cached)),flush=True)
        (out/'progress.json').write_text(json.dumps(dict(complete=False,completed=index+1,total=len(items),seconds=time.monotonic()-begin),indent=2),encoding='utf-8')
report=dict(complete=True,files=records,body_classes=len(bodies),frame_period_seconds=.06,
            expected_text_supplied_to_asr=False,test_audio_used=False,validation_audio_used=False,
            source_enrollment=False,offline_training_only=True,asr_used_for_training_labels=True,
            source_ctc_peaks_not_syllable_boundaries=True,posterior_not_pronunciation_acceptance=True,
            model_sha256=hashlib.sha256((MODEL/'outputs/sensevoice_dual.onnx').read_bytes()).hexdigest())
(out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PHONE_LABELS_DONE',len(records),len(bodies),flush=True)
