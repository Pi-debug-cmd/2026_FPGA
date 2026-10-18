from pathlib import Path
import json,urllib.request,hashlib
from download_seed_strong_assets import ranged
BASE=Path(__file__).resolve().parent
OUT=BASE/'sensevoice_pinyin_assets';OUT.mkdir(exist_ok=True)
def fetch(repo,revision,names):
 url=f'https://hf-mirror.com/api/models/{repo}/revision/{revision}?blobs=true'
 with urllib.request.urlopen(url,timeout=35) as r:info=json.load(r)
 assert info['sha']==revision
 local=OUT/repo.replace('/','__');local.mkdir(exist_ok=True)
 files=[]
 for name in names:
  meta=next(r for r in info['siblings'] if r['rfilename']==name)
  expected=meta.get('lfs',{}).get('sha256');size=meta.get('size',0)
  url=f'https://hf-mirror.com/{repo}/resolve/{revision}/{name}'
  path=local/name;path.parent.mkdir(parents=True,exist_ok=True)
  if size>100*1024*1024 and expected: record=ranged(url,path,size,expected)
  else:
   if not path.exists():
    with urllib.request.urlopen(url,timeout=35) as r:path.write_bytes(r.read())
   digest=hashlib.sha256(path.read_bytes()).hexdigest()
   if expected:assert digest==expected
   record=dict(path=str(path),url=url,sha256=digest,bytes=path.stat().st_size)
  files.append(record);print('FETCHED '+name,flush=True)
  (local/'download_manifest.json').write_text(json.dumps(dict(repository=repo,revision=revision,files=files),ensure_ascii=False,indent=2),encoding='utf-8')
 return dict(repository=repo,revision=revision,files=files)
if __name__=='__main__':
 result=fetch('robinsonphan/sensevoice-small-zh-pinyin-dual-ctc','ea81ad8cd1ec56983565a09ad6ff72993dc84d26',[
  'sensevoice_dual/test_onnx.py','sensevoice_dual/src/model.py','sensevoice_dual/conf/dual_ctc.yaml',
  'sensevoice_dual/data/vocab_pinyin.json','sensevoice_dual/export/export_onnx.py',
  'sensevoice_dual/outputs/sensevoice_dual.onnx'])
 with urllib.request.urlopen('https://hf-mirror.com/api/models/FunAudioLLM/SenseVoiceSmall',timeout=35) as r:info=json.load(r)
 base=fetch('FunAudioLLM/SenseVoiceSmall',info['sha'],['config.yaml','am.mvn'])
 (OUT/'manifest.json').write_text(json.dumps([result,base],ensure_ascii=False,indent=2),encoding='utf-8')
 print('PINYIN MODEL ASSETS COMPLETE',flush=True)
