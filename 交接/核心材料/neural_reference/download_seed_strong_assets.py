"""Download pinned stronger teacher weights using verified byte ranges."""
from pathlib import Path
import concurrent.futures,hashlib,json,time,urllib.request
from download_cross_evaluators import download,metadata
BASE=Path(__file__).resolve().parent
OUT=BASE/'Seed-VC/checkpoints/pinned'
def ranged(url,path,size,expected):
    if path.exists():
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=expected: raise RuntimeError('Existing hash mismatch')
        return dict(path=str(path),url=url,bytes=size,sha256=digest,cached=True)
    directory=path.parent/(path.name+'.ranges'); directory.mkdir(exist_ok=True)
    step=32*1024*1024; count=(size+step-1)//step
    def segment(index):
        start=index*step; end=min(size-1,start+step-1); piece=directory/f'{index:03}.bin'
        if piece.exists() and piece.stat().st_size==end-start+1: return piece
        for attempt in range(3):
            try:
                request=urllib.request.Request(url+f'?download=true&segment={index}',headers={'Range':f'bytes={start}-{end}','User-Agent':'Local-Voice-Model-Setup'})
                with urllib.request.urlopen(request,timeout=35) as response:
                    if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}': raise RuntimeError('Invalid range response')
                    temp=piece.with_suffix('.part'); copied=0
                    with temp.open('wb') as stream:
                        while data:=response.read(1024*1024): stream.write(data); copied+=len(data)
                    if copied!=end-start+1: raise RuntimeError('Incomplete range')
                    temp.replace(piece)
                print(f'{path.name}: segment {index+1}/{count}',flush=True)
                return piece
            except Exception:
                if attempt==2: raise
                time.sleep(1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: pieces=list(pool.map(segment,range(count)))
    temp=path.with_suffix(path.suffix+'.combined.part'); digest=hashlib.sha256()
    with temp.open('wb') as stream:
        for piece in pieces:
            with piece.open('rb') as source:
                while data:=source.read(1024*1024): stream.write(data); digest.update(data)
    if digest.hexdigest()!=expected: raise RuntimeError('Combined SHA256 mismatch')
    temp.replace(path)
    return dict(path=str(path),url=url,bytes=size,sha256=expected,cached=False)
def fetch(repo,names,revision=None):
    suffix=('/revision/'+revision) if revision else ''
    info=metadata('https://huggingface.co/api/models/'+repo+suffix+'?blobs=true')
    folder=OUT/repo.replace('/','__'); folder.mkdir(exist_ok=True)
    (folder/'strong_repository_metadata.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    files=[]
    for name in names:
        item=next(x for x in info['siblings'] if x['rfilename']==name)
        url='https://huggingface.co/'+repo+'/resolve/'+info['sha']+'/'+name
        expected=item.get('lfs',{}).get('sha256'); size=item.get('size',0)
        files.append(ranged(url,folder/name,size,expected) if size>100*1024*1024 and expected else download(url,folder/name,expected))
    return dict(repository=repo,revision=info['sha'],local=str(folder),files=files)
if __name__=='__main__':
    jobs=[('Plachta/Seed-VC',['DiT_seed_v2_uvit_whisper_small_wavenet_bigvgan_pruned.pth'],'257283f9f41585055e8f858fba4fd044e5caed6e'),
          ('nvidia/bigvgan_v2_22khz_80band_256x',['config.json','bigvgan_generator.pt'],None)]
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending=[pool.submit(fetch,*item) for item in jobs]
        for future in concurrent.futures.as_completed(pending):
            try: results.append(future.result())
            except Exception as error: results.append(dict(error=repr(error))); print(repr(error),flush=True)
            (OUT/'strong_manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    if any('error' in x for x in results): raise SystemExit(1)
    print('All stronger assets verified.',flush=True)
