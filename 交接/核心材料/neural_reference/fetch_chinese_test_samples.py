"""Read first three WAVs from two AISHELL speaker archives as streaming tests.
Does not download the complete corpus or add test audio to target training.
"""
from pathlib import Path
import json,hashlib,tarfile,urllib.request

BASE=Path(__file__).resolve().parent
OUT=BASE/'public_chinese_test'
REPO='AISHELL/AISHELL-1'
REV='bbe295d530192a4cd41644b711c9aecd087df653'
PREFIX='https://huggingface.co/datasets/'+REPO+'/resolve/'+REV+'/'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(PREFIX+'resource_aishell/speaker.info',timeout=60) as r:
        speakers=r.read().decode('utf-8')
    (OUT/'speaker.info').write_text(speakers,encoding='utf-8')
    genders=dict(line.split() for line in speakers.splitlines() if line.strip())
    records=[]
    for speaker in ['S0002','S0003']:
        url=PREFIX+'data_aishell/wav/'+speaker+'.tar.gz'
        with urllib.request.urlopen(url,timeout=120) as response:
            with tarfile.open(fileobj=response,mode='r|gz') as archive:
                count=0
                for member in archive:
                    if not member.isfile() or not member.name.lower().endswith('.wav'):
                        continue
                    if member.size>5_000_000:
                        raise RuntimeError('Unexpected individual WAV size')
                    filename=Path(member.name).name
                    path=OUT/filename
                    with archive.extractfile(member) as f:
                        payload=f.read()
                    if len(payload)!=member.size: raise RuntimeError('Truncated sample')
                    path.write_bytes(payload)
                    records.append(dict(speaker=speaker,gender_metadata=genders[speaker[1:]],
                                        path=str(path),archive_member=member.name,archive_url=url,
                                        bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()))
                    count+=1
                    print('Fetched '+filename,flush=True)
                    if count==3: break
    (OUT/'source_manifest.json').write_text(json.dumps(dict(
        dataset=REPO,revision=REV,files=records,usage='evaluation only, not target training'),
        ensure_ascii=False,indent=2),encoding='utf-8')
    print('Fetched 6 natural Mandarin clips from two corpus speakers.',flush=True)

if __name__=='__main__': main()
