"""Remove sentence context in exploratory fixed crops. Not gold boundaries."""
from pathlib import Path
import numpy as np,soundfile as sf,torch,re
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,OUT,read,save,sha
def main():
 checker=PinyinChecker()
 folder=OUT/'fixed_local_crops';folder.mkdir(exist_ok=True)
 windows=[('zhe',1.72,2.14,['zhe','jie']),('shi',2.39,2.68,['shi','xi']),
          ('bie',2.91,3.40,['bie','bi','bei','bai','pie','die'])]
 records=[]
 for row in read(OUT/'sensevoice_real_exploratory.json')['files']:
  assert sha(row['path'])==row['sha256']
  x,sr=sf.read(row['path']);x=x.mean(axis=1) if x.ndim==2 else x
  for syllable,start,end,bodies in windows:
   path=folder/(row['label']+'_'+syllable+'.wav')
   sf.write(path,x[int(start*sr):int(end*sr)],sr,subtype='PCM_16')
   name='local_'+row['label']+'_'+syllable
   result=checker.predict(path,name)
   logp=np.load(OUT/(name+'_pinyin_posteriors.npz'))['log_probs']
   tensor=torch.from_numpy(logp).unsqueeze(1)
   scores=[]
   for body in bodies:
    options=[]
    for tone in range(1,6):
     token=body+str(tone)
     if token not in checker.vocabulary:continue
     target=torch.tensor([checker.vocabulary[token]],dtype=torch.long)
     value=-float(torch.nn.functional.ctc_loss(tensor,target,
       torch.tensor([len(logp)]),torch.tensor([1]),blank=0,reduction='sum'))
     options.append(dict(token=token,ctc_log_likelihood=value))
    scores.append(max(options,key=lambda r:r['ctc_log_likelihood']))
   scores.sort(key=lambda r:r['ctc_log_likelihood'],reverse=True)
   record=dict(source_label=row['label'],parent_path=row['path'],parent_sha256=row['sha256'],
    path=str(path),sha256=sha(path),word=syllable,start_seconds=start,end_seconds=end,
    recognized=result,counter_hypotheses=scores,
    expected_spelling_not_given_to_predictor=True,not_human_confirmed_phone_boundaries=True,
    ctc_likelihood_not_calibrated_phone_correctness=True,automatic_approval=False)
   records.append(record)
   print(row['label']+' '+syllable+' => '+' '.join(result['decoded'])+' | best '+scores[0]['token'],flush=True)
 save(OUT/'fixed_local_probe.json',dict(status='complete',windows=windows,files=records,
  windows_fixed_before_results=True,not_grid_search=True,
  scope='Crops based on approximate whole-speech peaks and phone diagnostics, may include incomplete syllables; test context sensitivity only.'))
 print('LOCAL EXPLORATORY PROBE COMPLETE',flush=True)
if __name__=='__main__':main()
