"""Preselect public natural audio using publisher labels, never recognizer results."""
from pathlib import Path
import json,hashlib,requests,time
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor
from run_rvc_pilot import settings
settings()
import soundfile as sf
BASE=Path(__file__).resolve().parent
OUT=BASE/'public_pronunciation_calibration'
REPORT=Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04')
REPORT.mkdir(exist_ok=True)
TARGETS=['shi4','xi4','zhe4','jie4','bie2','bi2','die2','bai2']
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 meta=json.loads((OUT/'repository_metadata.json').read_text(encoding='utf8'));revision=meta['sha']
 available={x['rfilename'] for x in meta['siblings']}
 speakers={}
 for l in (OUT/'spk-info.txt').read_text(encoding='utf8').splitlines():
  if not l.strip() or l.startswith('#'):continue
  a=l.split();speakers[a[0]]=dict(age_group=a[1],gender=a[2],accent=a[3])
 candidates=defaultdict(lambda:defaultdict(list))
 for line in (OUT/'content.txt').read_text(encoding='utf8').splitlines():
  a=line.split();filename=a[0];chars=a[1::2];phones=a[2::2];speaker=filename[:7]
  assert len(chars)==len(phones)
  remote=f'train/wav/{speaker}/{filename}'
  if remote not in available or not 4<=len(phones)<=20:continue
  for target in TARGETS:
   if phones.count(target)!=1:continue
   idx=phones.index(target)
   # Keep the requested literal bie2 character; other classes use natural words.
   if target=='bie2' and chars[idx]!='别':continue
   candidates[speaker][target].append(dict(filename=filename,remote_path=remote,
    speaker=speaker,chars=chars,pinyin=phones,text=''.join(chars),target_pinyin=target,
    target_character=chars[idx],target_index=idx,**speakers[speaker]))
 eligible=[s for s in sorted(candidates) if all(candidates[s][t] for t in TARGETS[:5])
           and speakers[s]['age_group'] in ['B','C','D']]
 chosen={g:[s for s in eligible if speakers[s]['gender']==g][:3] for g in ['male','female']}
 assert all(len(x)==3 for x in chosen.values()),chosen
 rows=[]
 for gender,ids in chosen.items():
  for n,speaker in enumerate(ids):
   for target in TARGETS[:5]:
    # Shortest labelled utterance; tie broken by original file name. Fixed before inference.
    r=min(candidates[speaker][target],key=lambda x:(len(x['pinyin']),x['filename']))
    r=dict(r,id=f'{speaker}_{target}',split='development' if n==0 else 'heldout_speaker',
      revision=revision,source_url=f'https://huggingface.co/datasets/AISHELL/AISHELL-3/resolve/{revision}/{r["remote_path"]}')
    rows.append(r)
 core_ids=sum(chosen.values(),[])
 for target in TARGETS[5:]:
  for gender in ['male','female']:
   ids=sorted([s for s in candidates if candidates[s][target] and speakers[s]['gender']==gender
      and speakers[s]['age_group'] in ['B','C','D']],key=lambda s:(s not in core_ids,s))[:3]
   assert len(ids)==3
   for speaker in ids:
    r=min(candidates[speaker][target],key=lambda x:(len(x['pinyin']),x['filename']))
    split='development' if speaker in [chosen['male'][0],chosen['female'][0]] else 'heldout_speaker'
    rows.append(dict(r,id=f'{speaker}_{target}',split=split,revision=revision,
      source_url=f'https://huggingface.co/datasets/AISHELL/AISHELL-3/resolve/{revision}/{r["remote_path"]}'))
 assert len(rows)==48 and all(sum(r['target_pinyin']==t for r in rows)==6 for t in TARGETS)
 policy=dict(corpus='AISHELL-3',official_description='https://www.openslr.org/93/',
  license='Apache-2.0',repository='https://huggingface.co/datasets/AISHELL/AISHELL-3',revision=revision,
  selection='First3 eligible adult speakers of each sex by ID covering5 core syllables;3 auxiliary classes each add3 per sex, preferring core speakers then ID order. Shortest4-20-syllable sentence with exactly1 target occurrence. No recognition results used.',
  target_classes=TARGETS,known_speakers=chosen,speakers_separated=True,
  label_source='Publisher Chinese and pinyin annotations; not this recognizer or TTS.',
  individual_phone_correctness_not_manually_reaudited=True,original_wavs_unmodified=True,
  not_used_for_target_voice_training=True,source_speaker_enrolment=False,
  model_weights_and_thresholds_frozen=True,
  content_sha256=sha(OUT/'content.txt'),speaker_info_sha256=sha(OUT/'spk-info.txt'))
 save(REPORT/'selection_before_inference.json',dict(policy=policy,files=rows))
 audio=OUT/'audio';audio.mkdir(exist_ok=True)
 def fetch(r):
  p=audio/r['filename'];url=r['source_url'].replace('https://huggingface.co','https://hf-mirror.com')
  if not p.exists():
   for attempt in range(3):
    try:
     response=requests.get(url,timeout=60);response.raise_for_status();p.write_bytes(response.content);break
    except requests.RequestException:
     if attempt==2:raise
     time.sleep(1)
  info=sf.info(p);assert info.frames>1000
  return dict(r,path=str(p),sha256=sha(p),sample_rate=info.samplerate,channels=info.channels,
   seconds=info.duration,bytes=p.stat().st_size)
 with ThreadPoolExecutor(max_workers=4) as pool:
  downloaded=list(pool.map(fetch,rows))
 for r in downloaded:print(r['id'],r['text'],round(r['seconds'],2),flush=True)
 save(REPORT/'public_audio_manifest.json',dict(policy=policy,files=downloaded,
  file_count=len(downloaded),speaker_count=len({r['speaker'] for r in downloaded}),total_seconds=sum(r['seconds'] for r in downloaded)))
 print('PUBLIC AUDIO COLLECTION COMPLETE',flush=True)
if __name__=='__main__':main()
