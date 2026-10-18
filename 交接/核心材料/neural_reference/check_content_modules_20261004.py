"""Unconstrained pinyin diagnostics on controlled module interventions."""
from pathlib import Path
import json,subprocess,sys,shutil
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,sha
from validate_public_pronunciation_20261004 import map_tokens,BODY
import soundfile as sf
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/内容保持模块隔离_2026-10-04')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def main():
 sources=read(OUT/'source_manifest.json');items=read(OUT/'evaluation_items.json');checker=PinyinChecker();rows=[];refs={}
 for s in sources:
  assert sha(s['path'])==s['sha256'];result=checker.predict(s['prepared'])
  refs[s['label']]=result
  rows.append(dict(label=s['label']+'_source',role='genuine_input',source_metadata=s,**result))
  print('SOURCE',s['label'],' '.join(result['decoded']),flush=True)
 for item in items:
  assert sha(item['path'])==item['sha256'];result=checker.predict(item['path'])
  source=next(s for s in sources if s['label']==item['test_name'])
  source_body=[BODY(t) for t in refs[item['test_name']]['decoded']]
  mapping,distance=map_tokens(source_body,[BODY(t) for t in result['decoded']])
  row=dict(item,**result,body_edit_distance_from_source_free_decoding=distance,
   source_free_decoding_not_phone_gold=True,asr_agreement_cannot_approve=True)
  if source.get('pinyin'):
   _,ed=map_tokens([BODY(t) for t in source['pinyin']],[BODY(t) for t in result['decoded']])
   row['body_edit_distance_from_publisher_labels']=ed
  if item['test_name']=='fleurs1906':
   x,sr=sf.read(item['path'],dtype='float32');p=OUT/(item['label']+'_first4s.wav');sf.write(p,x[:4*sr],sr,subtype='PCM_24')
   row['first4s']=dict(path=str(p),sha256=sha(p),**checker.predict(p),
    fixed_window_not_phone_boundary=True,scope='Broad first sentence context, not half-second phone proof.')
  rows.append(row);print(item['label'],' '.join(result['decoded']),'source diff',distance,flush=True)
  save(OUT/'free_pinyin_results.json',dict(status='running',files=rows,automatic_phonetic_approval=False))
 save(OUT/'free_pinyin_results.json',dict(status='complete',files=rows,automatic_phonetic_approval=False,
  source_text_not_supplied_to_recognizer=True,no_phone_shortlist=True,source_enrollment=False))
 # Existing Mandarin identity/naturalness diagnostics, with human review gate intact.
 with (OUT/'cross_evaluate.console.log').open('w',encoding='utf8') as log:
  r=subprocess.run([sys.executable,'-B',str(BASE/'cross_evaluate_voice.py'),'--extra',str(OUT/'evaluation_items.json')],cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError('Cross evaluator failed; inspect its saved log.')
 shutil.copy2(Path('D:/总进度/目标人物分析/中文交叉评估/中文交叉评估结果.json'),OUT/'module_cross_eval.json')
 print('CONTENT MODULE CHECK COMPLETE',flush=True)
if __name__=='__main__':main()
