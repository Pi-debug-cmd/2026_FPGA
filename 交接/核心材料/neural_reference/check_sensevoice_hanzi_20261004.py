"""Decode existing dual-head acoustic Hanzi output, no oracle correction."""
from pathlib import Path
import requests,json,re,hashlib,time
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,FRONT
from validate_public_pronunciation_20261004 import map_tokens
from run_rvc_pilot import settings
settings()
import soundfile as sf,numpy as np,torch,sentencepiece as spm
from math import gcd
from scipy.signal import resample_poly
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def main():
 metadata=json.loads((FRONT/'repository_metadata.json').read_text(encoding='utf8'));name='chn_jpn_yue_eng_ko_spectok.bpe.model'
 item=next(r for r in metadata['siblings'] if r['rfilename']==name);path=FRONT/name
 if not path.exists():
  response=requests.get(f'https://hf-mirror.com/FunAudioLLM/SenseVoiceSmall/resolve/{metadata["sha"]}/{name}',timeout=60);response.raise_for_status();path.write_bytes(response.content)
 digest=hashlib.sha256(path.read_bytes()).hexdigest();expected=item.get('lfs',{}).get('sha256')
 if expected:assert expected==digest
 sp=spm.SentencePieceProcessor(model_file=str(path));checker=PinyinChecker()
 assert sp.get_piece_size()==25055
 def predict(path):
  x,sr=sf.read(path,dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
  if sr!=16000:x=resample_poly(x,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
  x=x/(np.max(np.abs(x))+1e-8);torch.manual_seed(20261004)
  with torch.inference_mode():features,lens=checker.frontend(torch.from_numpy(x).unsqueeze(0),torch.tensor([len(x)]))
  start=time.perf_counter();probs,lengths=checker.session.run(['hanzi_log_probs','encoder_lens'],dict(feats=features.numpy().astype('float32'),feats_lens=lens.numpy().astype('int32')))
  tokens=[];previous=0
  for row in probs[:int(lengths[0]),0]:
   token=int(np.argmax(row))
   if token and token!=previous:tokens.append(token)
   previous=token
  raw=sp.decode(tokens);text=re.sub(r'<\|[^>]*\|>','',raw).strip()
  return dict(raw_decoding=raw,text=text,token_ids=tokens,inference_seconds=time.perf_counter()-start)
 sources=json.loads((Path('D:/总进度/目标人物分析/内容保持模块隔离_2026-10-04')/'source_manifest.json').read_text(encoding='utf8'))
 public=json.loads(Path('D:/总进度/目标人物分析/公开真人发音校准_2026-10-04/public_audio_manifest.json').read_text(encoding='utf8'))['files']
 cases=[dict(label=r['label'],path=r['path'],expected_text=r['text'],role='genuine_source') for r in sources]
 seen={r['path'] for r in cases}
 # Original frozen selection; retain all remaining natural utterances, no result filtering.
 for r in public:
  if r['path'] in seen:continue
  cases.append(dict(label=r['id'],path=r['path'],expected_text=r['text'],role='publisher_labelled_calibration',split=r['split']));seen.add(r['path'])
 rows=[];norm=lambda x:re.sub(r'[^\u4e00-\u9fff]','',x)
 for r in cases:
  z=predict(r['path']);_,distance=map_tokens(list(norm(r['expected_text'])),list(norm(z['text'])))
  rows.append(dict(r,**z,character_edit_distance=distance,reference_character_count=len(norm(r['expected_text']))))
  print(r['label'],z['text'],'CER numerator',distance,flush=True)
 save(OUT/'sensevoice_hanzi_screening.json',dict(files=rows,tokenizer_sha256=digest,tokenizer_revision=metadata['sha'],
  weights_unchanged=True,unconstrained_greedy_acoustic_decoding=True,expected_text_not_input=True,
  postprocessing='Only remove task tags and evaluation punctuation; no text rewriting or lexicon override.',
  pronunciation_validator=False,board_deployed=False))
 print('HANZI SCREENING COMPLETE',flush=True)
if __name__=='__main__':main()
