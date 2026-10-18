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
OUT=Path('D:/总进度/目标人物分析/固定人物缓存与流式测量_2026-10-04');OUT.mkdir(exist_ok=True)
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
 fresh,fresh_seconds=timed(lambda:front.frontend_vc(SOURCE['path'],str(TARGET),model.sample_rate))
 cache={k:v.clone() for k,v in fresh.items() if not k.startswith('source_')}
 source_tokens,source_seconds=timed(lambda:front._extract_speech_token(SOURCE['path']))
 cached={**cache,'source_speech_token':source_tokens[0],'source_speech_token_len':source_tokens[1]}
 equal={k:torch.equal(fresh[k],cached[k]) for k in fresh}
 assert all(equal.values()),equal
 torch.save({k:v.cpu() for k,v in cache.items()},OUT/'fixed_target_condition.pt')
 text_full,text_front_seconds=timed(lambda:front.frontend_cross_lingual('You are a helpful assistant.<|endofprompt|>'+TEXT,str(TARGET),model.sample_rate,''))
 text_cache={k:v.clone() for k,v in text_full.items() if k not in ('text','text_len')}
 text_tokens,text_seconds=timed(lambda:front._extract_text_token('You are a helpful assistant.<|endofprompt|>'+TEXT))
 text_cached={**text_cache,'text':text_tokens[0],'text_len':text_tokens[1]}
 text_equal={k:torch.equal(text_full[k],text_cached[k]) for k in text_full}
 assert all(text_equal.values())
 meta=dict(load_seconds=load_seconds,torch_threads=4,tokenizer_providers=front.speech_tokenizer_session.get_providers(),full_vc_frontend_seconds=fresh_seconds,cached_source_tokenizer_seconds=source_seconds,cache_tensor_equality=equal,text_frontend_uncached_seconds=text_front_seconds,cached_text_tokenize_seconds=text_seconds,text_cache_tensor_equality=text_equal,condition_tensor_bytes=sum(v.numel()*v.element_size() for v in cache.values()),component_parameter_counts={k:sum(p.numel() for p in getattr(model.model,k).parameters()) for k in ['llm','flow','hift']})
 save(OUT/'frontend_and_resources.json',meta);rows=[];waves={}
 cases=[('native_uncached_whole',fresh,False,fresh_seconds),('native_cached_whole',cached,False,source_seconds),('native_cached_stream',cached,True,source_seconds),('actual_asr_cached_text_whole',text_cached,False,text_seconds),('actual_asr_cached_text_stream',text_cached,True,text_seconds)]
 for label,inputs,stream,frontend_seconds in cases:
  torch.manual_seed(20261004);np.random.seed(20261004);torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();model.model.token_hop_len=25
  chunks=[];events=[];sync();start=time.perf_counter()
  for item in model.model.tts(**inputs,stream=stream):
   sync();wave=item['tts_speech'].detach().cpu().float().numpy().reshape(-1)
   if len(wave):events.append(dict(time_seconds=time.perf_counter()-start,audio_seconds=len(wave)/model.sample_rate));chunks.append(wave)
  sync();elapsed=time.perf_counter()-start;x=np.concatenate(chunks);assert np.isfinite(x).all()
  gain=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8));x*=gain
  path=OUT/(label+'.wav');sf.write(path,x,model.sample_rate,subtype='PCM_24');waves[label]=sf.read(path,dtype='float32')[0]
  row=dict(label=label,path=str(path),sha256=sha(path),stream_output=stream,first_audio_render_seconds=events[0]['time_seconds'],first_audio_with_preprocessing_seconds=events[0]['time_seconds']+frontend_seconds,render_seconds=elapsed,frontend_seconds=frontend_seconds,total_processing_seconds=elapsed+frontend_seconds,audio_seconds=len(x)/model.sample_rate,processing_real_time_factor=(elapsed+frontend_seconds)/(len(x)/model.sample_rate),events=events,peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),gain_only=gain,subjective_acceptance=False,input_acquisition_time_included=False,asr_time_included=False,input_causal=False,board_deployed=False)
  if stream:
   available=0.;maxgap=0.
   for e in events:maxgap=max(maxgap,e['time_seconds']-(events[0]['time_seconds']+available));available+=e['audio_seconds']
   row['playout_lateness_after_immediate_start_seconds']=maxgap
  rows.append(row);save(OUT/'benchmark_results.json',rows);print('RESULT',label,row['first_audio_with_preprocessing_seconds'],elapsed,row['audio_seconds'],flush=True)
 a=waves['native_uncached_whole'];b=waves['native_cached_whole']
 reproducibility=dict(cache_whole_same_length=len(a)==len(b),cache_whole_max_sample_difference=float(np.max(np.abs(a-b))) if len(a)==len(b) else None)
 for label,oldname in [('native_cached_whole','cv3_native_fleurs1906'),('actual_asr_cached_text_whole','cv3_hanzi_asr_fleurs')]:
  old,sr=sf.read(QUALITY/(oldname+'.wav'),dtype='float32');new=waves[label]
  reproducibility[label]=dict(old_sha256=sha(QUALITY/(oldname+'.wav')),same_length=len(old)==len(new),max_sample_difference=float(np.max(np.abs(old-new))) if len(old)==len(new) else None)
 save(OUT/'cache_reproducibility.json',reproducibility)
 assert reproducibility['cache_whole_same_length'] and reproducibility['cache_whole_max_sample_difference']==0.,reproducibility
 assert not model.model.tts_speech_token_dict and not model.model.hift_cache_dict and not model.model.llm_end_dict
 save(OUT/'run_status.json',dict(status='complete',jobs=0,cache_validation_passed=True,output_streaming_measured=True,input_causal=False,board_deployed=False))
 print('BENCHMARK COMPLETE',reproducibility,flush=True)
if __name__=='__main__':main()
