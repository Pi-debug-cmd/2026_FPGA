from pathlib import Path
import json,re,time,hashlib
from run_rvc_pilot import settings
settings()
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,FRONT
import torch,numpy as np,soundfile as sf,sentencepiece as spm
from scipy.signal import resample_poly
from math import gcd
from validate_public_pronunciation_20261004 import map_tokens
OUT=Path('D:/总进度/目标人物分析/固定人物多说话人中文回归_2026-10-04')
read=lambda p:json.loads(p.read_text(encoding='utf8'))
checker=PinyinChecker();sp=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
quality=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
cases=read(OUT/'evaluation_items.json')
rows=[]
for case in cases:
 path=case['path'];x,sr=sf.read(path,dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
 if sr!=16000:x=resample_poly(x,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
 x=x/(np.max(np.abs(x))+1e-8);torch.manual_seed(20261004)
 with torch.inference_mode():feat,lens=checker.frontend(torch.from_numpy(x).unsqueeze(0),torch.tensor([len(x)]))
 hp,pp,lengths=checker.session.run(['hanzi_log_probs','pinyin_log_probs','encoder_lens'],dict(feats=feat.numpy().astype('float32'),feats_lens=lens.numpy().astype('int32')))
 def collapse(probs):
  ts=[];last=0
  for p in probs[:int(lengths[0]),0]:
   i=int(np.argmax(p))
   if i and i!=last:ts.append(i)
   last=i
  return ts
 decoded=re.sub(r'<\|[^>]*\|>','',sp.decode(collapse(hp))).strip()
 pred=checker.predict(path)
 normalized=lambda s:re.sub(r'[^\u4e00-\u9fff]','',s)
 _,ed=map_tokens(list(normalized(case['unmodified_actual_asr_text'])),list(normalized(decoded)))
 rows.append(dict(label=case['label'],path=path,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),hanzi_text=decoded,character_edit_distance=ed,pinyin=pred,automatically_validated_pronunciation=False))
 print(case['label'],decoded,'ed',ed,flush=True)
(OUT/'free_hanzi_and_pinyin_screening.json').write_text(json.dumps(dict(files=rows,phonetic_acceptance=False,checker_has_known_human_bie_blindspot=True,expected_text_not_used_in_acoustic_decoding=True),ensure_ascii=False,indent=2),encoding='utf8')
