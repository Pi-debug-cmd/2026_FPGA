from pathlib import Path
import sys,subprocess
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
for step in [100,300]:
 path=OUT/'personal_training'/f'personal_v2_step{step:03}.pth'
 with (OUT/f'personal_step{step}.console.log').open('w',encoding='utf-8') as log:
  result=subprocess.run([sys.executable,'-B',str(BASE/'run_seed_v2_controls.py'),'--cfm-only','--checkpoint',str(path)],stdout=log,stderr=subprocess.STDOUT,cwd=BASE)
 if result.returncode:raise RuntimeError('Inference failed '+str(step))
 print('PERSONAL V2 INFERENCE '+str(step)+' COMPLETE',flush=True)
result=subprocess.run([sys.executable,'-B',str(BASE/'evaluate_seed_v2.py')],cwd=BASE)
if result.returncode:raise RuntimeError('Evaluation failed')
