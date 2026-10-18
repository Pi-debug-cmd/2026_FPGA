from pathlib import Path
import json,sys,time,os,hashlib
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;ROOT=BASE/'CosyVoice_reference'
sys.path[:0]=[str(ROOT),str(ROOT/'third_party/Matcha-TTS')]
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['MODELSCOPE_CACHE']=str(BASE/'cache/modelscope')
import torch,numpy as np,soundfile as sf
from transformers import Qwen2ForCausalLM,AutoConfig
from run_cosyvoice3_controls_20261004 import sha,read,save,MODEL,ASSETS
OUT=Path('D:/总进度/目标人物分析/官方拼音发音控制对照_2026-10-04');OUT.mkdir(exist_ok=True)
QUALITY=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
TARGET=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
SOURCE=read(Path('D:/总进度/目标人物分析/内容保持模块隔离_2026-10-04/source_manifest.json'))[0]
TEXT=next(r for r in read(QUALITY/'sensevoice_hanzi_screening.json')['files'] if r['label']=='fleurs1906')['text']
def sync():torch.cuda.synchronize()
def timed(fn):
 sync();start=time.perf_counter();v=fn();sync();return v,time.perf_counter()-start

def main():
 torch.set_num_threads(4);torch.cuda.init()
 save(OUT/'experiment_before_inference.json',dict(source=SOURCE,target_path=str(TARGET),target_sha256=sha(TARGET),actual_asr_text=TEXT,model_revision='29e01c4e8d000f4bcd70751be16fa94bf3d85a18',seed=20261004,source_enrollment=False,output_streaming_only=True,input_causal=False,board_deployed=False,human_acceptance=False))
 for r in read(ASSETS/'manifest.json')['files']:assert sha(r['path'])==r['sha256']
 original=Qwen2ForCausalLM.from_pretrained
 def config_only(path,*a,**k):
  config=AutoConfig.from_pretrained(path,local_files_only=True);dtype=torch.get_default_dtype()
  try:torch.set_default_dtype(torch.float16);return Qwen2ForCausalLM(config)
  finally:torch.set_default_dtype(dtype)
 Qwen2ForCausalLM.from_pretrained=staticmethod(config_only)
 from cosyvoice.cli.model import CosyVoice3Model
 upstream=CosyVoice3Model.__init__
 def small(self,llm,flow,hift,*a,**k):llm.half();flow.half();upstream(self,llm,flow,hift,*a,**k)
 CosyVoice3Model.__init__=small
 from cosyvoice.cli.cosyvoice import CosyVoice3
 model,load_seconds=timed(lambda:CosyVoice3(str(MODEL),fp16=True));Qwen2ForCausalLM.from_pretrained=original
 print('LOADED',load_seconds,flush=True)
 front=model.frontend
 mapping={'别':'[b][ié]','这':'[zh][è]','是':'[sh][ì]'}
 official=front.tokenizer.special_tokens['additional_special_tokens']
 for value in mapping.values():
  import re
  for token in re.findall(r'\[[^\]]+\]',value):
   assert token in official and len(front.tokenizer.encode(token))==1,token
 rows=[]
 male_text=next(r for r in read(QUALITY/'sensevoice_hanzi_screening.json')['files'] if r['label']=='public_male_bie')['text']
 cases=[('fleurs_bie_hint',TEXT,{'别':mapping['别']}),('fleurs_three_phone_hints',TEXT,mapping),('real_male_bie_hint',male_text,{'别':mapping['别']})]
 plan=[]
 for label,text,hints in cases:
  marked=''.join(hints.get(c,c) for c in text)
  assert len(text)==len(''.join(c for c in text))
  plan.append(dict(label=label,unmodified_actual_asr_text=text,phonetic_input=marked,hints=hints,text_semantics_unchanged=True,phonetic_dictionary_diagnostic_only=True,context_dependent_polyphone_handling_implemented=False))
 save(OUT/'experiment_before_inference.json',dict(cases=plan,reference_path=str(TARGET),reference_sha256=sha(TARGET),model_revision='29e01c4e8d000f4bcd70751be16fa94bf3d85a18',supported_format_source=str(ROOT/'example.py'),source_text_is_actual_hanzi_asr=True,source_enrollment=False,no_training=True,seed=20261004,not_general_realtime_solution=True))
 for case in plan:
  torch.manual_seed(20261004);np.random.seed(20261004);torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();chunks=[];start=time.perf_counter()
  for item in model.inference_cross_lingual('You are a helpful assistant.<|endofprompt|>'+case['phonetic_input'],str(TARGET),stream=False,text_frontend=False):chunks.append(item['tts_speech'].detach().cpu().float().numpy().reshape(-1))
  sync();elapsed=time.perf_counter()-start;x=np.concatenate(chunks);assert np.isfinite(x).all()
  gain=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8));x*=gain
  path=OUT/(case['label']+'.wav');sf.write(path,x,model.sample_rate,subtype='PCM_24')
  rows.append(dict(case,path=str(path),sha256=sha(path),seconds=len(x)/model.sample_rate,inference_seconds=elapsed,subjective_acceptance=False,automatic_phonetic_acceptance=False,board_deployed=False,reference_path=str(TARGET),reference_sha256=sha(TARGET)))
  save(OUT/'evaluation_items.json',rows);print('GENERATED',case['label'],len(x)/model.sample_rate,elapsed,flush=True)
 save(OUT/'run_status.json',dict(status='complete',jobs=0,candidate_promoted=False,automatic_phonetic_acceptance=False,board_deployed=False))
 print('PHONETIC CONTROL COMPLETE',flush=True)
if __name__=='__main__':main()
