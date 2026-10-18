"""Exact C features for expanded train-only pairs; keep original heldout unchanged."""
from train_board_student_20261005 import BASE,read
from pathlib import Path
import json,numpy as np,subprocess
budget=BASE.parent/'board_budget_20261005';native=BASE.parent/'board_support/native_llvc_20261005';out=budget/'fargan_corpus_expanded';out.mkdir(exist_ok=True)
original=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'));extra=json.loads((budget/'student_corpus_expanded/paired_manifest.json').read_text(encoding='utf-8'));assert extra['complete']
heldout={r['speaker'] for r in original['files'] if r['split']!='train'};excluded=set(extra['excluded_speakers']);rows=list(original['files']);rejected=[]
def extract(path,stem):
    wave=read(path);pcm=np.rint(np.clip(wave,-1,32767/32768)*32768).astype('<i2');raw=out/(stem+'.pcm');pcm.tofile(raw);feature=out/(stem+'.features.f32')
    subprocess.run([str(native/'fargan_probe_host.exe'),'--features',str(raw),str(feature),str(out/(stem+'.json'))],check=True)
    f=np.fromfile(feature,dtype='float32');assert np.isfinite(f).all();return str(feature),len(wave)
for row in extra['files']:
    assert row['split']=='train' and row['speaker'] not in heldout and row['speaker'] not in excluded
    if abs(row['duration_difference_samples'])>1600:rejected.append(dict(filename=row['filename'],reason='teacher/source length difference exceeds100ms'));continue
    stem=Path(row['filename']).stem;source,n=extract(row['path'],stem+'_source');teacher,tn=extract(row['teacher_path'],stem+'_teacher')
    rows.append(dict(row,source_features=source,teacher_features=teacher,source_samples=n,teacher_samples=tn));print('EXPANDED_FEATURES',len(rows)-len(original['files']),flush=True)
report=dict(original,files=rows,rejected=rejected,complete=True,expanded_train_speakers=sorted({r['speaker'] for r in rows if r['split']=='train'}),expanded_train_seconds=sum(r['seconds'] for r in rows if r['split']=='train'),original_validation_unchanged=True,test_audio_used=False,target_track9_used=False)
(out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('EXPANDED_FEATURES_READY',report['expanded_train_seconds'],flush=True)
