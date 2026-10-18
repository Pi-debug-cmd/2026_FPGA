"""Fetch pinned public evaluators; never upload the user's audio."""
from pathlib import Path
import concurrent.futures, hashlib, json, os, urllib.request, zipfile

BASE=Path(__file__).resolve().parent
DEST=BASE/'cross_evaluators'
DEST.mkdir(exist_ok=True)
def request(url):
    return urllib.request.Request(url,headers={'User-Agent':'Voice-Conversion-Evaluator-Setup'})
def metadata(url):
    with urllib.request.urlopen(request(url),timeout=45) as response: return json.load(response)
def download(url,path,expected=None):
    if path.exists():
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if expected and digest!=expected: raise RuntimeError('Existing hash mismatch: '+str(path))
        return dict(path=str(path),url=url,sha256=digest,bytes=path.stat().st_size,cached=True)
    temp=path.with_suffix(path.suffix+'.part')
    digest=hashlib.sha256(); count=0; announce=20*1024*1024
    with urllib.request.urlopen(request(url),timeout=45) as response, temp.open('wb') as output:
        while data:=response.read(1024*1024):
            output.write(data); digest.update(data); count+=len(data)
            if count>=announce:
                print(f'{path.name}: {count//(1024*1024)} MiB',flush=True); announce+=20*1024*1024
    value=digest.hexdigest()
    if expected and value!=expected: raise RuntimeError('Downloaded hash mismatch: '+str(path))
    temp.replace(path)
    return dict(path=str(path),url=url,sha256=value,bytes=count,cached=False)
def wespeaker():
    repo='Wespeaker/wespeaker-cnceleb-resnet34-LM'
    info=metadata('https://huggingface.co/api/models/'+repo+'?blobs=true')
    (DEST/'wespeaker_model_metadata.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    filename='cnceleb_resnet34_LM.onnx'
    entry=next(x for x in info['siblings'] if x['rfilename']==filename)
    weight=download('https://huggingface.co/'+repo+'/resolve/'+info['sha']+'/'+filename,DEST/filename,entry.get('lfs',{}).get('sha256'))
    return dict(evaluator='WeSpeaker Chinese ResNet34-LM',repository=repo,revision=info['sha'],card=info.get('cardData'),weight=weight)
def utmos():
    repo='tarepan/SpeechMOS'; revision='ed25eacbfa42b99156c36ebec67a733b5dbb9b79'
    source=download('https://codeload.github.com/'+repo+'/zip/'+revision,DEST/'SpeechMOS_source.zip')
    source_dir=DEST/('SpeechMOS-'+revision)
    if not source_dir.exists():
        with zipfile.ZipFile(source['path']) as archive:
            for item in archive.infolist():
                target=(DEST/item.filename).resolve()
                if not target.is_relative_to(DEST.resolve()): raise RuntimeError('Unsafe archive path')
            archive.extractall(DEST)
    release=metadata('https://api.github.com/repos/'+repo+'/releases/tags/v1.0.0')
    asset=next(x for x in release['assets'] if x['name']=='utmos22_strong_step7459_v1.pt')
    (DEST/'utmos_release_metadata.json').write_text(json.dumps(asset,ensure_ascii=False,indent=2),encoding='utf-8')
    asset_digest=asset.get('digest') or ''
    weight=download(asset['browser_download_url'],DEST/asset['name'],asset_digest.removeprefix('sha256:') or None)
    return dict(evaluator='UTMOS22 Strong SpeechMOS implementation',repository=repo,revision=revision,source=source,source_directory=str(source_dir),weight=weight)
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(wespeaker),pool.submit(utmos)]
        records=[]
        for future in concurrent.futures.as_completed(futures):
            try:
                result=future.result(); records.append(result); print(json.dumps(result,ensure_ascii=False),flush=True)
            except Exception as error:
                records.append(dict(error=repr(error))); print(repr(error),flush=True)
            (DEST/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    if any('error' in x for x in records): raise SystemExit(1)
