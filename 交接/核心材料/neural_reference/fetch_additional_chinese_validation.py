"""Fetch new Mandarin speakers for evaluation only, never target training."""
from pathlib import Path
import concurrent.futures,hashlib,json,tarfile,urllib.request
BASE=Path(__file__).resolve().parent
OUT=BASE/'public_chinese_validation'; OUT.mkdir(exist_ok=True)
REV='bbe295d530192a4cd41644b711c9aecd087df653'
PREFIX='https://huggingface.co/datasets/AISHELL/AISHELL-1/resolve/'+REV+'/'
genders=dict(line.split() for line in (BASE/'public_chinese_test/speaker.info').read_text(encoding='utf-8').splitlines() if line.strip())
def fetch(speaker):
    url=PREFIX+'data_aishell/wav/'+speaker+'.tar.gz'; rows=[]
    with urllib.request.urlopen(url,timeout=40) as response,tarfile.open(fileobj=response,mode='r|gz') as archive:
        for member in archive:
            if not member.isfile() or not member.name.lower().endswith('.wav'): continue
            if member.size>5_000_000: raise RuntimeError('Unexpected WAV size')
            name=Path(member.name).name
            if speaker not in name: raise RuntimeError('Wrong speaker archive member')
            with archive.extractfile(member) as source: data=source.read()
            if len(data)!=member.size: raise RuntimeError('Truncated archive member')
            path=OUT/name; path.write_bytes(data)
            rows.append(dict(label='validation_source_'+path.stem,path=str(path),speaker=speaker,gender_metadata=genders[speaker[1:]],
                sha256=hashlib.sha256(data).hexdigest(),archive_url=url,archive_member=member.name,usage='new diagnostic source; no target training or input enrollment'))
            if len(rows)==2: break
    print('Fetched '+speaker,flush=True)
    return rows
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: rows=sum(list(pool.map(fetch,['S0004','S0124','S0125'])),[])
    wanted={Path(x['path']).stem for x in rows}; texts={}
    transcript_url=PREFIX+'data_aishell/transcript/aishell_transcript_v0.8.txt'
    with urllib.request.urlopen(transcript_url,timeout=40) as response:
        for line in response:
            key,*words=line.decode('utf-8').strip().split()
            if key in wanted:
                texts[key]=''.join(words)
                if len(texts)==len(wanted): break
    for row in rows:
        row['expected_text']=texts[Path(row['path']).stem]; row['text_origin']='AISHELL supplied transcript'
    (OUT/'source_manifest.json').write_text(json.dumps(dict(dataset='AISHELL/AISHELL-1',revision=REV,transcript_url=transcript_url,files=rows),ensure_ascii=False,indent=2),encoding='utf-8')
    print('COMPLETE 6 clips, 3 new identities including two female-labeled speakers',flush=True)
