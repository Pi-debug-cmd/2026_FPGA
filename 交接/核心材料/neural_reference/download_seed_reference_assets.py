"""Fetch exact public weights needed for the XLSR-tiny PC comparison."""
from pathlib import Path
import concurrent.futures,json
from download_cross_evaluators import download,metadata
BASE=Path(__file__).resolve().parent
OUT=BASE/'Seed-VC'/'checkpoints'/'pinned'
OUT.mkdir(parents=True,exist_ok=True)
JOBS={
 'Plachta/Seed-VC':['DiT_uvit_tat_xlsr_ema.pth'],
 'funasr/campplus':['campplus_cn_common.bin'],
 'FunAudioLLM/CosyVoice-300M':['hift.pt'],
 'facebook/wav2vec2-xls-r-300m':['config.json','preprocessor_config.json','pytorch_model.bin'],
}
def fetch(repo,files):
    data=metadata('https://huggingface.co/api/models/'+repo+'?blobs=true')
    folder=OUT/repo.replace('/','__'); folder.mkdir(exist_ok=True)
    (folder/'repository_metadata.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    records=[]
    for filename in files:
        entry=next(x for x in data['siblings'] if x['rfilename']==filename)
        records.append(download('https://huggingface.co/'+repo+'/resolve/'+data['sha']+'/'+filename,folder/filename,entry.get('lfs',{}).get('sha256')))
    result=dict(repository=repo,revision=data['sha'],local=str(folder),files=records)
    (folder/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('READY '+repo,flush=True)
    return result
if __name__=='__main__':
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        tasks=[pool.submit(fetch,repo,files) for repo,files in JOBS.items()]
        for task in concurrent.futures.as_completed(tasks):
            try: results.append(task.result())
            except Exception as error: results.append(dict(error=repr(error))); print(repr(error),flush=True)
            (OUT/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    if any('error' in x for x in results): raise SystemExit(1)
