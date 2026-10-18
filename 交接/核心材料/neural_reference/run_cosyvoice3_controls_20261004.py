"""New architecture control: native VC versus Chinese-text target synthesis."""
from pathlib import Path
import sys,os,json,hashlib,time,argparse
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;ROOT=BASE/'CosyVoice_reference'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'third_party/Matcha-TTS'))
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['MODELSCOPE_CACHE']=str(BASE/'cache/modelscope')
import torch,numpy as np,soundfile as sf
from transformers import Qwen2ForCausalLM,AutoConfig
OUT=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
ASSETS=BASE/'cosyvoice3_assets';MODEL=ASSETS/'FunAudioLLM__Fun-CosyVoice3-0.5B-2512'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--half-storage',action='store_true');parser.add_argument('--hanzi-only',action='store_true');args=parser.parse_args()
 torch.set_num_threads(4);torch.cuda.init()
 print('CUDA INITIALIZED EARLY',torch.cuda.mem_get_info(),flush=True)
 assets=read(ASSETS/'manifest.json')
 for r in assets['files']:assert sha(r['path'])==r['sha256']
 print('ALL ASSET HASHES VERIFIED',flush=True)
 # The complete llm.pt strictly overwrites all Qwen learned parameters. Initialize
 # the matching architecture only, avoiding redundant BlankEN1GB foundation weights.
 original=Qwen2ForCausalLM.from_pretrained
 def config_only(path,*a,**k):
  config=AutoConfig.from_pretrained(path,local_files_only=True)
  dtype=torch.get_default_dtype()
  try:
   if args.half_storage:torch.set_default_dtype(torch.float16)
   return Qwen2ForCausalLM(config)
  finally:torch.set_default_dtype(dtype)
 Qwen2ForCausalLM.from_pretrained=staticmethod(config_only)
 if args.half_storage:
  from cosyvoice.cli.model import CosyVoice3Model
  upstream_init=CosyVoice3Model.__init__
  def small_storage_init(self,llm,flow,hift,*a,**k):
   llm.half();flow.half();upstream_init(self,llm,flow,hift,*a,**k)
  CosyVoice3Model.__init__=small_storage_init
 from cosyvoice.cli.cosyvoice import CosyVoice3
 start=time.perf_counter();model=CosyVoice3(str(MODEL),fp16=True);Qwen2ForCausalLM.from_pretrained=original
 if args.half_storage:
  assert next(model.model.llm.parameters()).dtype==torch.float16
  assert next(model.model.hift.parameters()).dtype==torch.float32
 loaded=time.perf_counter()-start
 print('MODEL LOADED',loaded,'PARAMETERS',sum(p.numel() for p in model.model.llm.parameters()),flush=True)
 target=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
 source=read(Path('D:/总进度/目标人物分析/内容保持模块隔离_2026-10-04/source_manifest.json'))
 text=source[0]['text'];asr=read(OUT/'prompt_and_input_asr.json');actual=next(r for r in asr['files'] if r['label']=='real_male_input')['asr_text']
 cases=[dict(label='cv3_native_'+r['label'],method='native_voice_conversion',source_path=r['path'],source_sha256=r['sha256'],expected_text=r['text']) for r in source]
 cases +=[dict(label='cv3_correct_text_fleurs',method='text_to_target_voice_control',text=text,expected_text=text,
   text_source='Publisher transcript, explicitly controlled text; not ASR end-to-end proof.'),
  dict(label='cv3_actual_asr_fleurs',method='asr_to_target_voice_prerecorded',text=actual,expected_text=text,
    text_source='Actual Whisper-small transcription of genuine male; recognition errors retained, never secretly corrected.'),
  dict(label='cv3_same_target_text',method='same_target_text_diagnostic',text='我的校园很美，走近大门就能看见宽阔的操场。',
   expected_text='我的校园很美，走近大门就能看见宽阔的操场。',text_source='Previously ASR-derived Track9 first sentence, diagnostic only; not prompt or training.')]
 prefix='cv3_hanzi' if args.hanzi_only else 'cv3'
 if args.hanzi_only:
  actual_row=next(r for r in read(OUT/'sensevoice_hanzi_screening.json')['files'] if r['label']=='fleurs1906')
  cases=[dict(label='cv3_hanzi_asr_fleurs',method='sensevoice_hanzi_asr_to_target_prerecorded',text=actual_row['text'],expected_text=text,
    text_source='Actual unconstrained acoustic Hanzi CTC from genuine input; exact output, no oracle text or punctuation inserted.',
    asr_source_path=actual_row['path'],asr_source_sha256=sha(actual_row['path']))]
 save(OUT/(prefix+'_experiment_before_inference.json'),dict(cases=cases,assets_manifest=str(ASSETS/'manifest.json'),target_path=str(target),target_sha256=sha(target),
  reference_unchanged=True,constructor='Qwen config-only initialization then original strict llm.pt/flow.pt/hift.pt loading.',
  model_load_seconds=loaded,half_storage=args.half_storage,fp16_autocast=True,seed=20261004,
  source_speaker_registration=False,target9_not_conditioning=True,no_training=True,no_audio_uploaded=True,
  board_deployed=False,causal_end_to_end_streaming=False,output_chunk_streaming=False))
 rows=[]
 for case in cases:
  torch.manual_seed(20261004);np.random.seed(20261004);torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();chunks=[];times=[]
  start=time.perf_counter()
  if case['method']=='native_voice_conversion':
   assert sha(case['source_path'])==case['source_sha256']
   generator=model.inference_vc(case['source_path'],str(target),stream=False)
  else:
   generator=model.inference_cross_lingual('You are a helpful assistant.<|endofprompt|>'+case['text'],str(target),stream=False,text_frontend=False)
  for item in generator:
   chunks.append(item['tts_speech'].detach().cpu().float().numpy().reshape(-1));times.append(time.perf_counter()-start)
  torch.cuda.synchronize();elapsed=time.perf_counter()-start
  x=np.concatenate(chunks);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6
  gain=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8));x*=gain
  path=OUT/(case['label']+'.wav');sf.write(path,x,model.sample_rate,subtype='PCM_24')
  rows.append(dict(case,path=str(path),sha256=sha(path),group='cosyvoice3_'+case['method'],test_name=case['label'],
   reference_path=str(target),reference_sha256=sha(target),seconds=len(x)/model.sample_rate,
   inference_seconds=elapsed,first_output_seconds=times[0],output_chunk_times=times,gain_only_rms_normalization=gain,
   clipped_fraction=float(np.mean(np.abs(x)>=.999)),peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
   source_speaker_enrollment=False,subjective_acceptance=False,board_deployed=False,causal_streaming=False))
  save(OUT/(prefix+'_evaluation_items.json'),rows)
  print('GENERATED',case['label'],len(x)/model.sample_rate,elapsed,flush=True)
 save(OUT/(prefix+'_run_status.json'),dict(status='complete',files=len(rows),trained=False,active_jobs=0))
 print('COSYVOICE3 CONTROLS COMPLETE',flush=True)
if __name__=='__main__':main()
