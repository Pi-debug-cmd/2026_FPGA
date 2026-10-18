"""Accelerate a large public weight download with validated byte ranges."""
from pathlib import Path
import concurrent.futures,hashlib,json,urllib.request,time
BASE=Path(__file__).resolve().parent/'Seed-VC/checkpoints/pinned/facebook__wav2vec2-xls-r-300m'
info=json.loads((BASE/'repository_metadata.json').read_text(encoding='utf-8'))
entry=next(x for x in info['siblings'] if x['rfilename']=='pytorch_model.bin')
size=entry['lfs']['size']; expected=entry['lfs']['sha256']; step=32*1024*1024
pieces=BASE/'ranges'; pieces.mkdir(exist_ok=True)
url='https://huggingface.co/facebook/wav2vec2-xls-r-300m/resolve/'+info['sha']+'/pytorch_model.bin'
def fetch(index):
    start=index*step; end=min(size-1,start+step-1); path=pieces/f'{index:03}.bin'
    if path.exists() and path.stat().st_size==end-start+1: return path
    for attempt in range(3):
        try:
            req=urllib.request.Request(url+f'?download=true&segment={index}',headers={'Range':f'bytes={start}-{end}','User-Agent':'Voice-Conversion-Reference-Download'})
            with urllib.request.urlopen(req,timeout=35) as response:
                if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':
                    raise RuntimeError('Server did not honor requested range')
                temp=path.with_suffix('.part')
                count=0
                with temp.open('wb') as out:
                    while data:=response.read(1024*1024): out.write(data); count+=len(data)
                if count!=end-start+1: raise RuntimeError('Incomplete range')
                temp.replace(path)
            print('Range ready '+str(index),flush=True)
            return path
        except Exception:
            if attempt==2: raise
            time.sleep(1)
count=(size+step-1)//step
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: paths=list(pool.map(fetch,range(count)))
temp=BASE/'pytorch_model.bin.ranged.part'; digest=hashlib.sha256()
with temp.open('wb') as out:
    for path in paths:
        with path.open('rb') as source:
            while data:=source.read(1024*1024): out.write(data); digest.update(data)
if digest.hexdigest()!=expected: raise RuntimeError('Combined SHA256 mismatch')
temp.replace(BASE/'pytorch_model.bin')
print('COMPLETE verified '+digest.hexdigest(),flush=True)
