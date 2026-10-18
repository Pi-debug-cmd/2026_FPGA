"""New fixed corpus for a board-budget student; exclude all prior test speakers."""
from pathlib import Path
import json,hashlib,requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from run_rvc_pilot import settings
settings()
import soundfile as sf
BASE=Path(__file__).resolve().parent
META=BASE/'public_pronunciation_calibration'
OUT=BASE.parent/'board_budget_20261005/student_corpus'
OUT.mkdir(parents=True,exist_ok=True);(OUT/'audio').mkdir(exist_ok=True)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    excluded=set()
    report=Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04')
    for name in ['public_audio_manifest.json','literal_word_samples.json']:
        doc=json.loads((report/name).read_text(encoding='utf-8'))
        excluded.update(r['speaker'] for r in doc['files'])
    genders={}
    for line in (META/'spk-info.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):continue
        sid,age,gender,accent=line.split()
        if age in ['B','C','D'] and sid not in excluded:genders[sid]=gender
    repo=json.loads((META/'repository_metadata.json').read_text(encoding='utf-8'))
    available={r['rfilename'] for r in repo['siblings']};candidates=defaultdict(list)
    for line in (META/'content.txt').read_text(encoding='utf-8').splitlines():
        a=line.split();name=a[0];sid=name[:7];chars=a[1::2];phones=a[2::2]
        remote='train/wav/'+sid+'/'+name
        if sid in genders and remote in available and 8<=len(chars)<=20:
            candidates[sid].append(dict(filename=name,speaker=sid,text=''.join(chars),pinyin=phones,remote=remote,gender=genders[sid]))
    selected=[];splits={};rows=[]
    for gender in ['male','female']:
        ids=[sid for sid in sorted(candidates) if genders[sid]==gender and len(candidates[sid])>=4][:8]
        assert len(ids)==8
        for i,sid in enumerate(ids):
            split='train' if i<6 else ('validation' if i==6 else 'test')
            splits[sid]=split;selected.append(sid)
            # Greedy phone coverage; no recognizer/model outcomes influence selection.
            seen=set();pool=sorted(candidates[sid],key=lambda r:r['filename'])
            for j in range(4):
                row=max(pool,key=lambda r:(len(set(r['pinyin'])-seen),-len(r['pinyin'])))
                pool.remove(row);seen.update(row['pinyin'])
                rows.append(dict(row,split=split,revision=repo['sha']))
    assert not(set(selected)&excluded)
    selection=dict(files=rows,speakers=splits,excluded_prior_test_speakers=sorted(excluded),
        target_track9_training=False,source_speaker_enrollment=False,
        selection_frozen_before_conversion=True,license='Apache-2.0',
        repository_revision=repo['sha'],target_identity_reference_fixed=True)
    (OUT/'selection_before_conversion.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
    def fetch(row):
        p=OUT/'audio'/row['filename']
        url='https://hf-mirror.com/datasets/AISHELL/AISHELL-3/resolve/'+repo['sha']+'/'+row['remote']
        if not p.exists():
            response=requests.get(url,timeout=45);response.raise_for_status();p.write_bytes(response.content)
        info=sf.info(p);assert info.frames>1000
        return dict(row,path=str(p),sha256=sha(p),seconds=info.duration,sample_rate=info.samplerate)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=[]
        for row in pool.map(fetch,rows):
            results.append(row)
            print('FETCHED',len(results),len(rows),row['speaker'],row['split'],flush=True)
    selection['files']=results;selection['total_seconds']=sum(r['seconds'] for r in results)
    (OUT/'source_manifest.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CORPUS_READY',selection['total_seconds'],flush=True)
if __name__=='__main__':main()
