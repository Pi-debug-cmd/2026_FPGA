from pathlib import Path
from argparse import Namespace
import sys,json,time,hashlib
from run_rvc_pilot import settings
settings()
import numpy as np,soundfile as sf,torch
from scipy.signal import resample_poly
from math import gcd
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/独立中文发音检查验证_2026-10-04')
ROOT=BASE/'Allosaurus';sys.path.insert(0,str(ROOT));torch.set_num_threads(4)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def main():
 from allosaurus.app import read_recognizer
 config=Namespace(model='uni2005',device_id=0,lang='cmn',approximate=False,prior=None)
 model=read_recognizer(config)
 inventory=model.lm.inventory.get_unit('cmn')
 save(OUT/'allosaurus_load.json',dict(config=vars(config),inventory=str(inventory),
  parameters=sum(p.numel() for p in model.am.parameters()),
  no_language_model_word_decoding=True,no_phone_inventory_or_prior_changes=True,
  expected_text_not_provided_to_recognizer=True,model_source_unchanged=True))
 records=[]
 controls=read(OUT/'synthetic_controls.json')['files']
 for row in controls:
  assert sha(row['path'])==row['sha256']
  started=time.perf_counter()
  with torch.inference_mode():
   result=model.recognize(row['path'],'cmn',timestamp=True)
  record=dict(row,recognized_timed_phones=result,elapsed_seconds=time.perf_counter()-started)
  records.append(record)
  print(row['id']+' => '+result.replace('\n',' | '),flush=True)
  save(OUT/'allosaurus_synthetic_results.json',dict(status='running',files=records))
 save(OUT/'allosaurus_synthetic_results.json',dict(status='complete',files=records,
  controls_are_provisional_synthetic_labels=True,human_phone_gold_validation=False))
 # Existing speech used only as exploratory diagnostic, not calibration/training.
 diagnostic=read(Path('D:/总进度/目标人物分析/真实声母错误定位_2026-10-04/diagnostic_items.json'))
 ablation=read(Path('D:/总进度/目标人物分析/别字后处理拆分对照_2026-10-04/evaluation_items.json'))
 rows=diagnostic+[r for r in ablation if r['label']=='raw_vc_only_clarity2dB']
 prep=OUT/'real_inputs_pcm16';prep.mkdir(exist_ok=True)
 exploratory=[]
 for row in rows:
  assert sha(row['path'])==row['sha256']
  x,sr=sf.read(row['path'],dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
  x=resample_poly(x,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
  x*=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.9/max(float(np.max(np.abs(x))),1e-8))
  dest=prep/(row['label']+'.wav');sf.write(dest,x,16000,subtype='PCM_16')
  with torch.inference_mode():result=model.recognize(str(dest),'cmn',timestamp=True)
  exploratory.append(dict(label=row['label'],source_path=row['path'],source_sha256=row['sha256'],
   prepared_path=str(dest),prepared_sha256=sha(dest),recognized_timed_phones=result,
   ground_truth_phone_times=None,not_validated_verdict=True))
  print('REAL '+row['label']+' => '+result.replace('\n',' | '),flush=True)
 save(OUT/'allosaurus_real_exploratory.json',dict(files=exploratory,scope='Exploratory unvalidated phonetic output; never accept conversion from this alone.'))
 print('ALLOSAURUS VALIDATION INFERENCE COMPLETE',flush=True)

if __name__=='__main__':main()
