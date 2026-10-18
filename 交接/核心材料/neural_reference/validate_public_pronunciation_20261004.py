"""Frozen public-corpus screening; cannot approve converted speech."""
from pathlib import Path
import json,re
from collections import Counter
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,sha
import numpy as np,soundfile as sf
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04')
BODY=lambda t:re.sub(r'\d','',t)
COUNTER={'shi':'xi','xi':'shi','zhe':'jie','jie':'zhe','bie':'bi','bi':'bie','die':'bie','bai':'bie'}
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def map_tokens(ref,hyp):
 n,m=len(ref),len(hyp);d=np.zeros((n+1,m+1),dtype=int);d[:,0]=np.arange(n+1);d[0,:]=np.arange(m+1)
 for i in range(1,n+1):
  for j in range(1,m+1):d[i,j]=min(d[i-1,j-1]+(ref[i-1]!=hyp[j-1]),d[i-1,j]+1,d[i,j-1]+1)
 i,j=n,m;mapping={}
 while i or j:
  if i and j and d[i,j]==d[i-1,j-1]+(ref[i-1]!=hyp[j-1]):mapping[i-1]=j-1;i-=1;j-=1
  elif i and d[i,j]==d[i-1,j]+1:mapping[i-1]=None;i-=1
  else:j-=1
 return mapping,int(d[n,m])
def locate_reference(logp,ids,target_index):
 # Standard CTC Viterbi used ONLY to estimate a crop, not to judge pronunciation.
 ext=np.zeros(2*len(ids)+1,dtype=int);ext[1::2]=ids
 tmax,smax=logp.shape[0],len(ext)
 prev=np.full(smax,-np.inf);prev[0]=logp[0,0];prev[1]=logp[0,ext[1]]
 back=np.zeros((tmax,smax),dtype=np.int16)
 for t in range(1,tmax):
  curr=np.full(smax,-np.inf)
  for s in range(smax):
   candidates=[s]
   if s:candidates.append(s-1)
   if s>=2 and ext[s]!=0 and ext[s]!=ext[s-2]:candidates.append(s-2)
   q=max(candidates,key=lambda q:prev[q]);curr[s]=prev[q]+logp[t,ext[s]];back[t,s]=q
  prev=curr
 s=max([smax-1,smax-2],key=lambda s:prev[s]);assert np.isfinite(prev[s])
 path=[]
 for t in range(tmax-1,-1,-1):path.append(s);s=int(back[t,s])
 path=np.array(path[::-1]);indices=np.flatnonzero(path==2*target_index+1)
 assert len(indices)>0
 return dict(start_seconds=float(indices[0]*.06),end_seconds=float((indices[-1]+1)*.06),
  peak_seconds=float(indices[np.argmax(logp[indices,ids[target_index]])]*.06),
  reference_forced_alignment_only_for_localization=True,boundaries_not_manually_verified=True)
def summarize(rows,field):
 stats=[]
 for split in ['development','heldout_speaker','all']:
  subset=[r for r in rows if split=='all' or r['split']==split]
  for cls in ['all','shi','xi','zhe','jie','bie','bi','die','bai']:
   group=[r for r in subset if cls=='all' or BODY(r['target_pinyin'])==cls]
   if not group:continue
   pred=[r[field] for r in group]
   stats.append(dict(split=split,syllable=cls,n=len(group),abstained_count=sum(p is None for p in pred),
    correct_label_count=sum(p==BODY(r['target_pinyin']) for r,p in zip(group,pred)),
    false_alarm_on_publisher_label_count=sum(p is not None and p!=BODY(r['target_pinyin']) for r,p in zip(group,pred)),
    deliberate_wrong_expected_label_detected_count=sum(p is not None and p!=COUNTER[BODY(r['target_pinyin'])] for r,p in zip(group,pred)),
    confused_predictions=dict(Counter(str(p) for p in pred))))
 return stats
def main():
 manifest=json.loads((OUT/'public_audio_manifest.json').read_text(encoding='utf8'))
 checker=PinyinChecker();rows=[];crops=OUT/'局部测试音频';crops.mkdir(exist_ok=True)
 post=OUT/'声学输出';post.mkdir(exist_ok=True)
 for item in manifest['files']:
  assert sha(item['path'])==item['sha256']
  r=checker.predict(item['path'],str(post/item['id']))
  mapping,distance=map_tokens([BODY(x) for x in item['pinyin']],[BODY(x) for x in r['decoded']])
  ix=mapping[item['target_index']];pred=BODY(r['decoded'][ix]) if ix is not None else None
  logp=np.load(post/(item['id']+'_pinyin_posteriors.npz'))['log_probs']
  unknown=[t for t in item['pinyin'] if t not in checker.vocabulary]
  row=dict(item,full_decoding=r,full_target_prediction=pred,full_body_edit_distance=distance,
    posthoc_alignment_not_recognizer_input=True,unknown_reference_tokens=unknown)
  # Publisher sandhi tones sometimes are absent in model vocabulary. Scoring ignores
  # tone; use a fixed same-body vocabulary fallback only for approximate cropping.
  align_tokens=[];fallbacks={}
  for token in item['pinyin']:
   if token in checker.vocabulary:align_tokens.append(token);continue
   choices=sorted(t for t in checker.vocabulary if BODY(t)==BODY(token))
   if not choices:break
   align_tokens.append(choices[0]);fallbacks[token]=choices[0]
  row['localization_tone_fallbacks']=fallbacks
  if len(align_tokens)!=len(item['pinyin']):
   row['localization_unavailable']=True;row['local15_prediction']=None;row['local30_prediction']=None
   rows.append(row);continue
  loc=locate_reference(logp,[checker.vocabulary[t] for t in align_tokens],item['target_index'])
  row['localization']=loc;audio,sr=sf.read(item['path'],dtype='float32');duration=len(audio)/sr
  for margin in [.15,.30]:
   name=f'local{int(margin*100):02d}';start=max(0,loc['start_seconds']-margin);end=min(duration,loc['end_seconds']+margin)
   wav=crops/f'{item["id"]}_{name}.wav';sf.write(wav,audio[int(start*sr):int(end*sr)],sr,subtype='PCM_24')
   result=checker.predict(wav);nearest=min(result['emissions'],key=lambda e:abs(start+e['approximate_peak_seconds']-loc['peak_seconds'])) if result['emissions'] else None
   row[name+'_prediction']=BODY(nearest['pinyin']) if nearest else None
   row[name]=dict(path=str(wav),sha256=sha(wav),start_seconds=start,end_seconds=end,
     decoding=result,selection='Unconstrained decoded emission nearest predetermined forced-alignment acoustic peak; no allowed-phone shortlist.')
  rows.append(row)
  print(item['id'],item['text'],'full',pred,'local15',row['local15_prediction'],'local30',row['local30_prediction'],flush=True)
  save(OUT/'public_checker_results.json',dict(status='running',files=rows))
 reports={name:summarize(rows,name+'_prediction') for name in ['full_target','local15','local30']}
 save(OUT/'public_checker_results.json',dict(status='complete',files=rows,summary=reports,
  model_weights_frozen=True,model_expected_text_input=False,syllable_tones_not_scored=True,
  negative_control_definition='Same natural utterance with deliberately incorrect expected contrasting syllable; checks class discrimination, not naturally mispronounced voice-conversion gold.',
  human_voice_conversion_errors_are_separate=True,automatic_pronunciation_approval=False))
 print('SUMMARY',json.dumps({k:[s for s in v if s['split']=='heldout_speaker' and s['syllable']=='all'] for k,v in reports.items()}),flush=True)
if __name__=='__main__':main()
