from pathlib import Path
from math import gcd
import json,hashlib
from run_rvc_pilot import settings
settings()
import soundfile as sf,numpy as np,torch
from scipy.signal import resample_poly
from transformers import WhisperProcessor,WhisperForConditionalGeneration
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04');OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 model_dir=BASE/'cache/hf/hub/models--openai--whisper-small/snapshots/973afd24965f72e36ca33b3055d56a652f456b4d'
 processor=WhisperProcessor.from_pretrained(str(model_dir),local_files_only=True)
 model=WhisperForConditionalGeneration.from_pretrained(str(model_dir),local_files_only=True,torch_dtype=torch.float16).to('cuda').eval()
 paths=[('target_prompt',Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')),
  ('real_male_input',BASE/'public_chinese_validation/fleurs_test_row0_id1906.wav')]
 rows=[]
 for label,path in paths:
  x,sr=sf.read(path,dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
  if sr!=16000:x=resample_poly(x,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
  features=processor(x,sampling_rate=16000,return_tensors='pt').input_features.to('cuda',torch.float16)
  with torch.inference_mode():tokens=model.generate(features,language='zh',task='transcribe',max_new_tokens=180)
  text=processor.batch_decode(tokens,skip_special_tokens=True)[0].strip();print(label,text,flush=True)
  rows.append(dict(label=label,path=str(path),sha256=sha(path),seconds=len(x)/16000,asr_text=text,
    text_is_unverified_asr_not_manual_gold=True))
 record=dict(files=rows,asr_model='openai/whisper-small',asr_revision=model_dir.name,
  reference_same_as_old_seed=True,asr_requires_independent_content_validation=True,no_audio_uploaded=True)
 (OUT/'prompt_and_input_asr.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
 print('PROMPT PREPARED',flush=True)
if __name__=='__main__':main()
