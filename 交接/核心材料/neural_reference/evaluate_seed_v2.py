from pathlib import Path
import sys,subprocess,json,shutil
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def main():
 items=read(OUT/'conversion_items.json');sources={}
 for row in items:
  sources[row['source_path']]=dict(label='v2_input_'+row['test_name'],group='v2_input_controls',test_name=row['test_name'],
   path=row['source_path'],sha256=row['source_sha256'],expected_text=row['expected_text'],text_origin=row['text_origin'])
 items+=list(sources.values());p=OUT/'evaluation_items.json';p.write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
 for file,args,dest in [
  ('cross_evaluate_voice.py',['--extra',str(p)],'v2_cross_eval.json'),
  ('automatic_voice_evaluation.py',['--items',str(p),'--name','genuine_seed_v2'],'v2_content_eval.json')]:
  with (OUT/(file+'.console.log')).open('w',encoding='utf-8') as log:
   result=subprocess.run([sys.executable,'-B',str(BASE/file),*args],cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
  if result.returncode:raise RuntimeError(file+' failed; '+str(OUT/(file+'.console.log')))
  origin=Path('D:/总进度/目标人物分析/中文交叉评估/中文交叉评估结果.json') if file.startswith('cross') else Path('D:/总进度/目标人物分析/自动评估与改进/genuine_seed_v2_评估记录.json')
  shutil.copy2(origin,OUT/dest);print('FROZEN '+dest,flush=True)
if __name__=='__main__':main()
