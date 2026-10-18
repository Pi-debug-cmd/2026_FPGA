from pathlib import Path
import json,urllib.request,zipfile,hashlib,concurrent.futures,time
from run_rvc_pilot import settings
settings()
from download_cross_evaluators import metadata,download
BASE=Path(__file__).resolve().parent;OUT=BASE/'knn_assets';OUT.mkdir(exist_ok=True)
ROOT=BASE/'kNN-VC';REV='c616845c4e309e24d5927f15adbdf277a3d65358'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def ranged_release(row,path):
 size=row['size'];step=32*1024*1024;url=row['browser_download_url']
 directory=OUT/(path.name+'.ranges');directory.mkdir(exist_ok=True)
 partial=path.with_suffix(path.suffix+'.part')
 if partial.exists():
  # Reuse complete prefix chunks from our interrupted original HTTPS transfer.
  with partial.open('rb') as f:
   for i in range(partial.stat().st_size//step):
    piece=directory/f'{i:03}.bin';b=f.read(step)
    if not piece.exists():piece.write_bytes(b)
 def segment(i):
  start=i*step;end=min(size-1,start+step-1);piece=directory/f'{i:03}.bin'
  if piece.exists() and piece.stat().st_size==end-start+1:return piece
  for attempt in range(3):
   try:
    req=urllib.request.Request(url+f'?segment={i}',headers={'Range':f'bytes={start}-{end}','User-Agent':'Local-Voice-Model-Setup'})
    with urllib.request.urlopen(req,timeout=35) as r:
     if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':raise RuntimeError('Wrong release byte range')
     temp=piece.with_suffix('.part');copied=0
     with temp.open('wb') as f:
      while b:=r.read(1024*1024):f.write(b);copied+=len(b)
     if copied!=end-start+1:raise RuntimeError('Incomplete release byte range')
     temp.replace(piece)
    print(f'{path.name}: {i+1}/{(size+step-1)//step}',flush=True);return piece
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:pieces=list(pool.map(segment,range((size+step-1)//step)))
 combined=path.with_suffix(path.suffix+'.combined.part')
 with combined.open('wb') as f:
  for piece in pieces:
   with piece.open('rb') as source:
    while b:=source.read(4*1024*1024):f.write(b)
 if combined.stat().st_size!=size:raise RuntimeError('Combined release size mismatch')
 combined.replace(path)
def asset(row):
 path=OUT/row['name'];url=row['browser_download_url']
 if path.exists():
  if path.stat().st_size!=row['size']:raise RuntimeError('Cached asset size mismatch')
 elif row['size']>100*1024*1024:ranged_release(row,path)
 else:
  # Download original release assets only; no unverifiable third-party mirror.
  temp=path.with_suffix(path.suffix+'.part')
  for attempt in range(3):
   try:
    req=urllib.request.Request(url+'?download=1',headers={'User-Agent':'Local-Voice-Conversion-Experiment'})
    with urllib.request.urlopen(req,timeout=45) as response,temp.open('wb') as f:
     copied=0
     while b:=response.read(4*1024*1024):f.write(b);copied+=len(b)
    if copied!=row['size']:raise RuntimeError('Release asset size mismatch')
    temp.replace(path);break
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 digest=sha(path)
 if row.get('digest') and row['digest']!='sha256:'+digest:raise RuntimeError('Publisher digest mismatch')
 print('ASSET '+row['name']+' complete',flush=True)
 return dict(name=row['name'],path=str(path),bytes=path.stat().st_size,sha256=digest,url=url,
  release_asset_id=row['id'],publisher_digest=row.get('digest'),
  integrity='HTTPS official release + API size + local SHA256; publisher did not supply independent digest' if not row.get('digest') else 'Publisher SHA256 verified')
def main():
 info=metadata('https://api.github.com/repos/bshall/knn-vc/commits/'+REV)
 release=metadata('https://api.github.com/repos/bshall/knn-vc/releases/tags/v0.1')
 (OUT/'release_metadata.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'source_metadata.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
 archive=OUT/'source.zip';entry=download('https://codeload.github.com/bshall/knn-vc/zip/'+REV,archive)
 ROOT.mkdir(exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  for item in z.infolist():
   if item.is_dir():continue
   relative=Path(*Path(item.filename).parts[1:]);target=(ROOT/relative).resolve()
   if not target.is_relative_to(ROOT.resolve()):raise RuntimeError('Unsafe archive path')
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
 names=['WavLM-Large.pt','prematch_g_02500000.pt']
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:files=list(pool.map(asset,[r for r in release['assets'] if r['name'] in names]))
 manifest=dict(repository='bshall/knn-vc',source_revision=REV,source_archive=entry,release_id=release['id'],files=files,
  audio_uploaded=False,board_deployed=False,license='Modified MIT with additional terms, not plain MIT; LICENSE retained')
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print('KNN ASSETS COMPLETE',flush=True)
if __name__=='__main__':main()
