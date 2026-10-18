from pathlib import Path
import subprocess,sys,json,shutil
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/V1音色来源排查')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
items=read(OUT/'conditioning_items.json');sources={}
for r in items:
 sources[r['source_path']]=dict(label='conditioning_input_'+r['test_name'],group='input_controls',test_name=r['test_name'],
  path=r['source_path'],sha256=r['source_sha256'],expected_text=r['expected_text'],text_origin=r['text_origin'])
cross_items=items+read(OUT/'roundtrip_evaluator_items.json')+list(sources.values())
save(OUT/'cross_items.json',cross_items);save(OUT/'content_items.json',items+list(sources.values()))
for file,args,origin,dest in [
 ('cross_evaluate_voice.py',['--extra',str(OUT/'cross_items.json')],Path('D:/总进度/目标人物分析/中文交叉评估/中文交叉评估结果.json'),'conditioning_cross_eval.json'),
 ('automatic_voice_evaluation.py',['--items',str(OUT/'content_items.json'),'--name','v1_conditioning'],Path('D:/总进度/目标人物分析/自动评估与改进/v1_conditioning_评估记录.json'),'conditioning_content_eval.json')]:
 with (OUT/(file+'.console.log')).open('w',encoding='utf-8') as log:
  result=subprocess.run([sys.executable,'-B',str(BASE/file),*args],cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(file+' failed')
 shutil.copy2(origin,OUT/dest);print('FROZEN '+dest,flush=True)
