"""New Mandarin gender coverage from Google's public test split, evaluation only."""
from pathlib import Path
import hashlib,io,json,urllib.request
import soundfile as sf
import pyarrow.parquet as pq
from download_seed_strong_assets import ranged
BASE=Path(__file__).resolve().parent; OUT=BASE/'public_chinese_validation'
meta=json.loads((OUT/'fleurs_repository_metadata.json').read_text(encoding='utf-8'))
item=next(x for x in meta['siblings'] if x['rfilename']=='cmn_hans_cn/test/0000.parquet')
url='https://huggingface.co/datasets/google/fleurs/resolve/'+meta['sha']+'/'+item['rfilename']
file=ranged(url,OUT/'fleurs_cmn_test.parquet',item['size'],item['lfs']['sha256'])
parquet=pq.ParquetFile(file['path']); rows=[]; counts={0:0,1:0}; offset=0
for batch in parquet.iter_batches(batch_size=16):
    for row in batch.to_pylist():
        index=offset; offset+=1; gender=row['gender']
        if counts.get(gender,99)>=(2 if gender==1 else 1): continue
        payload=row['audio']['bytes']; audio,sr=sf.read(io.BytesIO(payload),dtype='float32')
        seconds=len(audio)/sr
        if seconds<6 or seconds>20: continue
        name=f'fleurs_test_row{index}_id{row["id"]}.wav'; path=OUT/name; path.write_bytes(payload)
        rows.append(dict(label='validation_source_'+path.stem,path=str(path),dataset='google/fleurs',dataset_revision=meta['sha'],
            dataset_row_index=index,gender_metadata='female' if gender==1 else 'male',speaker_identity_metadata=None,
            expected_text=row['raw_transcription'],text_origin='FLEURS supplied transcript',
            sha256=hashlib.sha256(payload).hexdigest(),seconds=seconds,sample_rate=sr,
            usage='new input only; no target training or speaker enrollment',provenance='original audio bytes extracted from SHA256-verified public parquet'))
        counts[gender]+=1
    if counts=={0:1,1:2}: break
if counts!={0:1,1:2}: raise RuntimeError('Not enough requested clips')
# Preserve the newly fetched known AISHELL identity, whose mirror lacks female archives.
new_aishell=sorted(OUT.glob('BAC009S0004W*.wav')); transcripts={}
prefix='https://huggingface.co/datasets/AISHELL/AISHELL-1/resolve/bbe295d530192a4cd41644b711c9aecd087df653/'
with urllib.request.urlopen(prefix+'data_aishell/transcript/aishell_transcript_v0.8.txt',timeout=35) as response:
    wanted={p.stem for p in new_aishell}
    for line in response:
        key,*words=line.decode('utf-8').strip().split()
        if key in wanted:
            transcripts[key]=''.join(words)
            if len(transcripts)==len(wanted): break
for path in new_aishell:
    rows.append(dict(label='validation_source_'+path.stem,path=str(path),dataset='AISHELL/AISHELL-1',
        dataset_revision='bbe295d530192a4cd41644b711c9aecd087df653',gender_metadata='male',speaker_identity_metadata='S0004',
        expected_text=transcripts[path.stem],text_origin='AISHELL supplied transcript',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),usage='new input only, not training or enrollment'))
(OUT/'validation_manifest.json').write_text(json.dumps(dict(status='complete',files=rows,parquet=file,
    limitation='FLEURS gender labels are provided, but per-person identity is not; do not claim two distinct women.'),ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE '+str(len(rows))+' new source clips including female-labeled audio',flush=True)
