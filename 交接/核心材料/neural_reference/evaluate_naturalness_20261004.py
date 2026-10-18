from pathlib import Path
import subprocess,sys,json,shutil,hashlib
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;OLD=Path('D:/总进度/目标人物分析/局部音色包络校正');OUT=Path('D:/总进度/目标人物分析/自然度与鼻音排查_2026-10-04')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=read(OLD/'smoothed_items.json');paths={r['test_name']:r['previous_path'] for r in read(OLD/'baseline_reproductions.json')}
raw=[dict(r,label='raw_v1_fp16_steps30_'+r['test_name'],group='raw_v1_fp16_steps30',path=paths[r['test_name']],
 sha256=sha(paths[r['test_name']]),amount=0,fp16=True,diffusion_steps=30,cepstral_correction_applied=False) for r in old]
items=raw+old+read(OUT/'conversion_items.json')
if (OUT/'extended_training_items.json').exists():items+=read(OUT/'extended_training_items.json')
sources={}
for r in items:
 sources[r['source_path']]=dict(label='naturalness_input_'+r['test_name'],group='input_controls',test_name=r['test_name'],
  path=r['source_path'],sha256=r['source_sha256'],expected_text=r['expected_text'],text_origin=r['text_origin'])
p=OUT/'evaluation_items.json';p.write_text(json.dumps(items+list(sources.values()),ensure_ascii=False,indent=2),encoding='utf-8')
for script,args,origin,dest in [
 ('cross_evaluate_voice.py',['--extra',str(p)],Path('D:/总进度/目标人物分析/中文交叉评估/中文交叉评估结果.json'),'naturalness_cross_eval.json'),
 ('automatic_voice_evaluation.py',['--items',str(p),'--name','naturalness_20261004'],Path('D:/总进度/目标人物分析/自动评估与改进/naturalness_20261004_评估记录.json'),'naturalness_content_eval.json')]:
 with (OUT/(script+'.console.log')).open('w',encoding='utf-8') as log:
  result=subprocess.run([sys.executable,'-B',str(BASE/script),*args],cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(script+' failed; inspect console')
 shutil.copy2(origin,OUT/dest);print('FROZEN '+dest,flush=True)
