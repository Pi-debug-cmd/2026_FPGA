from pathlib import Path
import json,requests,hashlib,time
OUT=Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/neural_reference/llvc_pretrained_audit');d=json.loads((OUT/'repository_metadata.json').read_text(encoding='utf8'))
files=['models/checkpoints/llvc/G_500000.pth','README.md'];records=[]
for name in files:
 item=next(x for x in d['siblings'] if x['rfilename']==name);p=OUT/Path(name).name
 url='https://hf-mirror.com/KoeAI/llvc/resolve/'+d['sha']+'/'+name
 with requests.get(url,stream=True,timeout=(15,45)) as r:
  r.raise_for_status();h=hashlib.sha256();size=0
  with p.open('wb') as f:
   for b in r.iter_content(1024*1024):f.write(b);h.update(b);size+=len(b)
 expected=item.get('lfs',{}).get('sha256');digest=h.hexdigest()
 if expected:assert digest==expected and size==item['lfs']['size']
 records.append(dict(path=str(p),remote_path=name,sha256=digest,bytes=size,lfs_sha256_verified=bool(expected),url=url))
 print('DOWNLOADED',name,size,digest,flush=True)
(OUT/'manifest.json').write_text(json.dumps(dict(repo='KoeAI/llvc',revision=d['sha'],files=records,target_voice_is_not_user_target=True,purpose='Causal streaming and quantization geometry audit, not target identity acceptance.'),ensure_ascii=False,indent=2),encoding='utf8')
