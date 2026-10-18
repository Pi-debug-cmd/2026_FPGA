"""Literal-word supplements and a fixed0.49s crop sensitivity check."""
from pathlib import Path
import json,requests
from concurrent.futures import ThreadPoolExecutor
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,sha
from validate_public_pronunciation_20261004 import map_tokens,BODY
import soundfile as sf
BASE=Path(__file__).resolve().parent
DATA=BASE/'public_pronunciation_calibration'
OUT=Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04')
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def main():
 original=json.loads((OUT/'public_audio_manifest.json').read_text(encoding='utf8'))
 available={x['rfilename'] for x in json.loads((DATA/'repository_metadata.json').read_text(encoding='utf8'))['siblings']}
 speakers={a[0]:dict(age_group=a[1],gender=a[2],accent=a[3]) for l in (DATA/'spk-info.txt').read_text().splitlines() if l.strip() and not l.startswith('#') for a in [l.split()]}
 candidates=[]
 for line in (DATA/'content.txt').read_text(encoding='utf8').splitlines():
  a=line.split();filename=a[0];s=filename[:7];chars=a[1::2];phones=a[2::2]
  remote=f'train/wav/{s}/{filename}'
  if remote not in available or not 4<=len(chars)<=20 or speakers[s]['age_group'] not in ['B','C','D']:continue
  candidates.append(dict(filename=filename,speaker=s,chars=chars,pinyin=phones,remote_path=remote,text=''.join(chars),**speakers[s]))
 rows=[];revision=original['policy']['revision']
 for char,phone in [('是','shi4'),('戏','xi4'),('这','zhe4'),('借','jie4'),('别','bie2')]:
  for gender in ['male','female']:
   group=[r for r in candidates if r['gender']==gender and r['chars'].count(char)==1 and r['pinyin'][r['chars'].index(char)]==phone]
   assert group,(char,gender)
   # Extra selection responds to literal-word coverage, independent of recognition.
   r=min(group,key=lambda r:(len(r['chars']),r['filename']))
   rows.append(dict(r,id=r['filename'][:-4]+'_'+char,target_character=char,target_pinyin=phone,target_index=r['chars'].index(char),
      source_url=f'https://huggingface.co/datasets/AISHELL/AISHELL-3/resolve/{revision}/{r["remote_path"]}',revision=revision))
 save(OUT/'literal_selection_before_inference.json',dict(selection='One shortest available4-20-syllable natural utterance per exact character and sex, file-ID tie break; no recognition filtering.',files=rows))
 def fetch(r):
  p=DATA/'audio'/r['filename']
  if not p.exists():
   response=requests.get(r['source_url'].replace('huggingface.co','hf-mirror.com'),timeout=60);response.raise_for_status();p.write_bytes(response.content)
  info=sf.info(p)
  return dict(r,path=str(p),sha256=sha(p),sample_rate=info.samplerate,seconds=info.duration,channels=info.channels)
 with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,rows))
 checker=PinyinChecker();checks=[]
 for row in rows:
  result=checker.predict(row['path']);mapping,ed=map_tokens([BODY(t) for t in row['pinyin']],[BODY(t) for t in result['decoded']]);index=mapping[row['target_index']]
  predicted=BODY(result['decoded'][index]) if index is not None else None
  checks.append(dict(row,free_decoding=result,target_body_prediction=predicted,publisher_body_matched=predicted==BODY(row['target_pinyin']),
     not_added_to_formal_heldout_rate=True))
  print('LITERAL',row['target_character'],row['gender'],row['text'],predicted,flush=True)
 save(OUT/'literal_word_samples.json',dict(files=checks,model_frozen=True,source_labels='AISHELL-3 publisher character and pinyin annotations',not_voice_conversion_error_gold=True))
 initial=json.loads((OUT/'public_checker_results.json').read_text(encoding='utf8'))
 fixed=[]
 for r in initial['files']:
  if r['target_pinyin']!='bie2':continue
  peak=r['localization']['peak_seconds'];x,sr=sf.read(r['path'],dtype='float32');start=max(0,peak-.245);end=min(len(x)/sr,start+.49)
  p=OUT/'局部测试音频'/(r['id']+'_fixed049.wav');sf.write(p,x[int(start*sr):int(end*sr)],sr,subtype='PCM_24')
  result=checker.predict(p);nearest=min(result['emissions'],key=lambda e:abs(start+e['approximate_peak_seconds']-peak)) if result['emissions'] else None
  pred=BODY(nearest['pinyin']) if nearest else None
  fixed.append(dict(id=r['id'],text=r['text'],source_path=r['path'],source_sha256=r['sha256'],path=str(p),sha256=sha(p),
    start_seconds=start,end_seconds=end,free_decoding=result,target_body_prediction=pred,publisher_body_matched=pred=='bie',
    approximate_crop_not_human_verified=True,not_actual_wrong_pronunciation_gold=True))
  print('FIXED049',r['id'],pred,flush=True)
 save(OUT/'fixed049_bie_sensitivity.json',dict(files=fixed,correct_publisher_body=sum(r['publisher_body_matched'] for r in fixed),n=len(fixed),
  note='Same0.49s length as prior conversion probe, centered on approximate forced-CTC peak; boundary estimate is uncertain. Tests context sensitivity, not actual substitution.'))
 print('SUPPLEMENT COMPLETE',flush=True)
if __name__=='__main__':main()
