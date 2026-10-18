from pathlib import Path
import subprocess, sys, shutil
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/真实输入轻度清晰度检查_2026-10-04')
p=OUT/'evaluation_items.json'
for script,args,origin,dest in [
 ('cross_evaluate_voice.py',['--extra',str(p)],Path('D:/总进度/目标人物分析/中文交叉评估/中文交叉评估结果.json'),'clarity_cross_eval.json'),
 ('automatic_voice_evaluation.py',['--items',str(p),'--name','gentle_clarity_20261004'],Path('D:/总进度/目标人物分析/自动评估与改进/gentle_clarity_20261004_评估记录.json'),'clarity_content_eval.json')]:
 with (OUT/(script+'.console.log')).open('w',encoding='utf-8') as log:
  result=subprocess.run([sys.executable,'-B',str(BASE/script),*args],cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode: raise RuntimeError(script+' failed')
 shutil.copy2(origin,OUT/dest)
 print('FROZEN '+dest,flush=True)
