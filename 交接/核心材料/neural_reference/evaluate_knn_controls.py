from pathlib import Path
import subprocess,sys,json,shutil
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/kNN语音单位转换')
items=json.loads((OUT/'conversion_items.json').read_text(encoding='utf-8'))
if (OUT/'cascade_items.json').exists():items+=json.loads((OUT/'cascade_items.json').read_text(encoding='utf-8'))
sources=[];seen=set()
for r in items:
 if r['source_path'] in seen:continue
 seen.add(r['source_path'])
 sources.append(dict(label='knn_input_'+r['test_name'],group='knn_input_controls',test_name=r['test_name'],path=r['source_path'],
  sha256=r['source_sha256'],expected_text=r['expected_text'],text_origin=r['text_origin']))
p=OUT/'evaluation_items.json';p.write_text(json.dumps(items+sources,ensure_ascii=False,indent=2),encoding='utf-8')
for script,args,origin,dest in [
 ('cross_evaluate_voice.py',['--extra',str(p)],Path('D:/总进度/目标人物分析/中文交叉评估/中文交叉评估结果.json'),'knn_cross_eval.json'),
 ('automatic_voice_evaluation.py',['--items',str(p),'--name','knn_fixed_target'],Path('D:/总进度/目标人物分析/自动评估与改进/knn_fixed_target_评估记录.json'),'knn_content_eval.json')]:
 with (OUT/(script+'.console.log')).open('w',encoding='utf-8') as log:
  result=subprocess.run([sys.executable,'-B',str(BASE/script),*args],cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(script+' failed')
 shutil.copy2(origin,OUT/dest);print('FROZEN '+dest,flush=True)
