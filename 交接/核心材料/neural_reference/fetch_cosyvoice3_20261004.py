from pathlib import Path
import json,hashlib,urllib.request
from run_rvc_pilot import settings
settings()
from download_seed_strong_assets import ranged
BASE=Path(__file__).resolve().parent
OUT=BASE/'cosyvoice3_assets';MODEL=OUT/'FunAudioLLM__Fun-CosyVoice3-0.5B-2512';MODEL.mkdir(exist_ok=True)
def main():
 d=json.loads((OUT/'repository_metadata.json').read_text(encoding='utf8'));repo='FunAudioLLM/Fun-CosyVoice3-0.5B-2512';revision=d['sha']
 names=['cosyvoice3.yaml','config.json','configuration.json','README.md','campplus.onnx','speech_tokenizer_v3.onnx','llm.pt','flow.pt','hift.pt']
 names +=['CosyVoice-BlankEN/'+x for x in ['config.json','generation_config.json','merges.txt','tokenizer_config.json','vocab.json']]
 records=[]
 for name in names:
  r=next(r for r in d['siblings'] if r['rfilename']==name);size=r['size'];expected=r.get('lfs',{}).get('sha256')
  url=f'https://hf-mirror.com/{repo}/resolve/{revision}/{name}';path=MODEL/name;path.parent.mkdir(exist_ok=True,parents=True)
  if size>100*1024*1024 and expected:
   record=ranged(url,path,size,expected)
  else:
   if not path.exists():
    with urllib.request.urlopen(url,timeout=60) as response:path.write_bytes(response.read())
   assert path.stat().st_size==size
   digest=hashlib.sha256(path.read_bytes()).hexdigest()
   if expected:assert digest==expected
   record=dict(path=str(path),bytes=size,sha256=digest,url=url)
  records.append(dict(record,name=name,expected_lfs_sha256=expected))
  (OUT/'manifest.json').write_text(json.dumps(dict(repository=repo,revision=revision,files=records,
   blank_qwen_weights_not_downloaded='Initialize architecture from config then strictly load complete llm.pt; no learned weight may remain random.'),ensure_ascii=False,indent=2),encoding='utf8')
  print('VERIFIED',name,flush=True)
 print('COSYVOICE3 ASSETS COMPLETE',flush=True)
if __name__=='__main__':main()
