from pathlib import Path
import concurrent.futures,json
from run_rvc_pilot import settings
settings()
from download_seed_strong_assets import fetch,OUT
JOBS=[
 ('Plachta/Seed-VC',['v2/cfm_small.pth','v2/ar_base.pth'],'257283f9f41585055e8f858fba4fd044e5caed6e'),
 ('Plachta/ASTRAL-quantization',['bsq32/bsq32_light.pth','bsq2048/bsq2048_light.pth'],'4a2e9679f76eb03753adc8c503e3c23bb9c22f26'),
 ('facebook/hubert-large-ll60k',['config.json','preprocessor_config.json','pytorch_model.bin'],'ff022d095678a2995f3c49bab18a96a9e553f782'),
 ('openai/whisper-small',['config.json','tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','normalizer.json','special_tokens_map.json','added_tokens.json'],'973afd24965f72e36ca33b3055d56a652f456b4d')]
if __name__=='__main__':
 for repo,names,revision in JOBS:
  for name in names:(OUT/repo.replace('/','__')/name).parent.mkdir(parents=True,exist_ok=True)
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for future in concurrent.futures.as_completed([pool.submit(fetch,*j) for j in JOBS]):
   try:results.append(future.result())
   except Exception as e:results.append({'error':repr(e)});print(repr(e),flush=True)
   (OUT/'v2_manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 if any('error' in x for x in results):raise SystemExit(1)
 print('V2 assets SHA256 verified',flush=True)
