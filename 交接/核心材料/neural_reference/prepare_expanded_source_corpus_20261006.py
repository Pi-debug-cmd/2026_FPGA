"""Additional8 speakers + more original training speech; exclude all heldout.
Selection by fixed order/phone coverage before conversion, never model score.
"""
from pathlib import Path
import json,hashlib,requests,sys
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from run_rvc_pilot import settings
settings()
import soundfile as sf
BASE=Path(__file__).resolve().parent;META=BASE/'public_pronunciation_calibration';budget=BASE.parent/'board_budget_20261005';OUT=budget/'student_corpus_expanded'
OUT.mkdir(exist_ok=True);(OUT/'audio').mkdir(exist_ok=True)
old=json.loads((budget/'student_corpus/source_manifest.json').read_text(encoding='utf-8'));excluded=set(old['excluded_prior_test_speakers'])|set(old['speakers'])
existing_train={sid for sid,split in old['speakers'].items() if split=='train'}
repo=json.loads((META/'repository_metadata.json').read_text(encoding='utf-8'));available={r['rfilename'] for r in repo['siblings']};genders={}
for line in (META/'spk-info.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.startswith('#'):continue
    sid,age,gender,accent=line.split()
    if age in ['B','C','D'] and (sid not in excluded or sid in existing_train):genders[sid]=gender
candidates=defaultdict(list)
for line in (META/'content.txt').read_text(encoding='utf-8').splitlines():
    a=line.split();name=a[0];sid=name[:7];remote='train/wav/'+sid+'/'+name;chars=a[1::2];phones=a[2::2]
    if sid in genders and remote in available and 8<=len(chars)<=20:candidates[sid].append(dict(filename=name,speaker=sid,text=''.join(chars),pinyin=phones,remote=remote,gender=genders[sid],split='train',revision=repo['sha']))
rows=[];speakers={}
for gender in ['male','female']:
    ids=[sid for sid in sorted(candidates) if genders[sid]==gender and sid not in excluded and len(candidates[sid])>=12][:4];assert len(ids)==4
    ids+=sorted(sid for sid in existing_train if genders[sid]==gender)
    for sid in ids:
        speakers[sid]='train';prior=[r for r in old['files'] if r['speaker']==sid];seen=set(p for r in prior for p in r['pinyin']);used={r['filename'] for r in prior}
        pool=sorted([r for r in candidates[sid] if r['filename'] not in used],key=lambda r:r['filename']);number=8 if sid in existing_train else 12;assert len(pool)>=number
        for i in range(number):
            r=max(pool,key=lambda r:(len(set(r['pinyin'])-seen),-len(r['pinyin'])));pool.remove(r);seen.update(r['pinyin']);rows.append(r)
selection=dict(files=rows,speakers=speakers,excluded_speakers=sorted(excluded-existing_train),additional_speakers=sorted(set(speakers)-existing_train),selection_frozen_before_conversion=True,repository_revision=repo['sha'],license='Apache-2.0',source_enrollment=False,target_track9_training=False,test_audio_used=False)
(OUT/'selection_before_conversion.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
def fetch(r):
    path=OUT/'audio'/r['filename']
    if not path.exists():
        response=requests.get('https://hf-mirror.com/datasets/AISHELL/AISHELL-3/resolve/'+repo['sha']+'/'+r['remote'],timeout=45);response.raise_for_status();path.write_bytes(response.content)
    info=sf.info(path);assert info.frames>1000
    return dict(r,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),seconds=info.duration,sample_rate=info.samplerate)
results=[]
with ThreadPoolExecutor(max_workers=4) as pool:
    for row in pool.map(fetch,rows):
        results.append(row);print('EXPANSION_FETCHED',len(results),len(rows),row['speaker'],flush=True)
        (OUT/'download_progress.json').write_text(json.dumps(dict(complete=False,files=results),ensure_ascii=False,indent=2),encoding='utf-8')
selection.update(files=results,total_seconds=sum(r['seconds'] for r in results),complete=True)
(OUT/'source_manifest.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
teacher=(BASE/'make_board_student_pairs_20261005.py').read_text(encoding='utf-8').replace("OUT=BASE.parent/'board_budget_20261005/student_corpus'","OUT=BASE.parent/'board_budget_20261005/student_corpus_expanded'")
(BASE/'make_expanded_student_pairs_20261006.py').write_text(teacher,encoding='utf-8')
print('EXPANDED_SOURCES_READY',selection['total_seconds'],flush=True)
