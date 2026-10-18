"""Pinned genuine V2 CFM/AR contrast; offline PC quality experiment only."""
from pathlib import Path
import os,sys,json,hashlib,time,argparse,types
from run_rvc_pilot import settings
settings()
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
BASE=Path(__file__).resolve().parent;ROOT=BASE/'Seed-VC';PIN=ROOT/'checkpoints/pinned'
OUT=Path('D:/总进度/目标人物分析/SeedVC完整V2对照');OUT.mkdir(parents=True,exist_ok=True)
REVIEW=Path('D:/总进度/目标人物分析/音色与自然度复查')
os.chdir(ROOT);sys.path.insert(0,str(ROOT))
import torch,numpy as np,soundfile as sf,yaml
from hydra.utils import instantiate
from omegaconf import OmegaConf
torch.set_num_threads(4)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def load_models(personal_checkpoint=None):
 assets=[]
 for name in ['manifest.json','strong_manifest.json','v2_manifest.json']:assets+=read(PIN/name)
 paths={}
 for repo in assets:
  if 'error' in repo:raise RuntimeError(repo)
  for f in repo['files']:
   if sha(f['path'])!=f['sha256']:raise RuntimeError('Asset SHA256 mismatch')
   paths[(repo['repository'],f['url'].split('/resolve/'+repo['revision']+'/')[-1])]=f['path']
 config=yaml.safe_load((ROOT/'configs/v2/vc_wrapper.yaml').read_text(encoding='utf-8'))
 for name in ['content_extractor_narrow','content_extractor_wide']:
  config[name]['tokenizer_name']=str(PIN/'openai__whisper-small')
  config[name]['ssl_model_name']=str(PIN/'facebook__hubert-large-ll60k')
 config['vocoder']['pretrained_model_name_or_path']=str(PIN/'nvidia__bigvgan_v2_22khz_80band_256x')
 save(OUT/'resolved_config.json',config)
 # Verify full HF loading information before the official feature-layer truncation.
 from transformers import AutoModel
 original=AutoModel.from_pretrained;hf_checks=[]
 def checked_hf(path,*a,**kw):
  model,info=original(path,*a,output_loading_info=True,**kw)
  learned=set(dict(model.named_parameters()))
  missing=learned.intersection(info.get('missing_keys',[]))
  if missing or info.get('mismatched_keys') or info.get('error_msgs'):raise RuntimeError(info)
  hf_checks.append(dict(path=str(path),loading_info=info,all_learned_parameters_loaded=True))
  return model
 AutoModel.from_pretrained=checked_hf
 try:model=instantiate(OmegaConf.create(config))
 finally:AutoModel.from_pretrained=original
 checked=[]
 def load(name,state,excluded=()):
  network=getattr(model,name);state={k.removeprefix('module.'):v for k,v in state.items()}
  if name=='style_encoder':
   state={k.replace('xvector.dense','dense').replace('xvector.stats','stats'):v for k,v in state.items()}
  for k,p in network.named_parameters():
   if any(k.startswith(x) for x in excluded):continue
   if k not in state or state[k].shape!=p.shape:raise RuntimeError('Missing/mismatched learned parameter '+name+'/'+k)
  result=torch.nn.Module.load_state_dict(network,state,strict=False)
  checked.append(dict(module=name,parameters=sum(p.numel() for p in network.parameters()),
   missing_buffers_or_separately_loaded=list(result.missing_keys),unexpected=list(result.unexpected_keys),
   all_learned_parameters_loaded=True,excluded_separately_verified=list(excluded)))
 cfm=torch.load(paths[('Plachta/Seed-VC','v2/cfm_small.pth')],map_location='cpu',weights_only=True)['net']
 load('cfm',cfm['cfm']);load('cfm_length_regulator',cfm['length_regulator']);del cfm
 ar=torch.load(paths[('Plachta/Seed-VC','v2/ar_base.pth')],map_location='cpu',weights_only=True)['net']
 load('ar',ar['ar']);load('ar_length_regulator',ar['length_regulator']);del ar
 for name,file in [('content_extractor_narrow','bsq32/bsq32_light.pth'),('content_extractor_wide','bsq2048/bsq2048_light.pth')]:
  load(name,torch.load(paths[('Plachta/ASTRAL-quantization',file)],map_location='cpu',weights_only=True),('ssl_model.',))
 load('style_encoder',torch.load(paths[('funasr/campplus','campplus_cn_common.bin')],map_location='cpu',weights_only=True))
 if personal_checkpoint:
  personal=torch.load(personal_checkpoint,map_location='cpu',weights_only=True)['net']
  load('cfm',personal['cfm']);load('cfm_length_regulator',personal['length_regulator'])
 # BigVGAN.from_pretrained already loads the full generator with strict=True.
 audit_name='model_load_validation.json' if not personal_checkpoint else Path(personal_checkpoint).stem+'_load_validation.json'
 save(OUT/audit_name,dict(assets=assets,hf_checks=hf_checks,modules=checked,
  personal_checkpoint=str(personal_checkpoint) if personal_checkpoint else None,
  personal_checkpoint_sha256=sha(personal_checkpoint) if personal_checkpoint else None,
  full_parameter_count=sum(p.numel() for p in model.parameters()),source_revision='51383efd921027683c89e5348211d93ff12ac2a8',
  adaptations=['Local verified asset paths','No model compilation',
   'Capture upstream non-streaming final PCM through helper; generator otherwise discards it',
   'Cast vocoder mel input to FP32 (same learned weights, no waveform postfilter)'],
  board_deployed=False,causal_streaming=False,audio_uploaded=False))
 # Official non-streaming generator never yields its helper's final PCM. Capture it directly.
 original_chunks=model._stream_wave_chunks;capture={}
 def chunks(*a,**kw):
  result=original_chunks(*a,**kw)
  if result[4] is not None:capture['audio']=result[4]
  return result
 model._stream_wave_chunks=chunks
 model.vocoder.register_forward_pre_hook(lambda module,args:(args[0].float(),))
 model.to('cuda').eval();model.setup_ar_caches(max_batch_size=1,max_seq_len=4096,dtype=torch.float16,device=torch.device('cuda'))
 return model,capture
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--extra-reference',action='store_true');parser.add_argument('--checkpoint',type=Path)
 parser.add_argument('--cfm-only',action='store_true');args=parser.parse_args()
 model,capture=load_models(args.checkpoint);inputs=read(REVIEW/'neural_control_manifest.json')['files']
 fresh=read(BASE/'public_chinese_validation/validation_manifest.json')['files']
 inputs += [r for r in fresh if r['label'] in ['validation_source_BAC009S0004W0121','validation_source_fleurs_test_row3_id1852']]
 reference=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
 references=[('t6_8s',reference)]
 if args.extra_reference:
  x,sr=sf.read('D:/总进度/目标人物语音/Track 5.wav',dtype='float32');x=x[:15*sr].mean(axis=1)
  x*=.04/max(float(np.sqrt(np.mean(x*x))),1e-8);p=OUT/'target_t5_15s.wav';sf.write(p,x,sr,subtype='PCM_24')
  references=[('t5_15s',p)]
 records=read(OUT/'conversion_items.json') if (OUT/'conversion_items.json').exists() else []
 for ref_name,reference in references:
  for style in ([False] if args.cfm_only else [False,True]):
   group='seed_v2_'+((args.checkpoint.stem+'_') if args.checkpoint else '')+('ar_cfm' if style else 'cfm')+'_'+ref_name
   for row in inputs:
    name=row.get('voice',row['label'].removeprefix('validation_source_'));label=group+'_'+name
    if any(r['label']==label and sha(r['path'])==r['sha256'] for r in records):continue
    if sha(row['path'])!=row['sha256']:raise RuntimeError('Source modified')
    x,sr=sf.read(row['path'],dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
    x*=.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
    folder=OUT/'inputs';folder.mkdir(exist_ok=True);source=folder/(name+'.wav');sf.write(source,x,sr,subtype='PCM_24')
    torch.manual_seed(20261003);capture.clear();torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
    print('CONVERT '+label,flush=True)
    for _ in model.convert_voice_with_streaming(str(source),str(reference),diffusion_steps=30,length_adjust=1.,
     intelligebility_cfg_rate=.7,similarity_cfg_rate=.7,top_p=.9,temperature=1.,repetition_penalty=1.,convert_style=style,
     device=torch.device('cuda'),dtype=torch.float16,stream_output=False):pass
    torch.cuda.synchronize();elapsed=time.perf_counter()-started
    y=np.asarray(capture['audio']);assert np.isfinite(y).all() and np.sqrt(np.mean(y*y))>1e-6
    y*=min(.04/float(np.sqrt(np.mean(y*y))),.95/float(np.max(np.abs(y))))
    folder=OUT/group;folder.mkdir(exist_ok=True);dest=folder/(name+'.wav');sf.write(dest,y,model.sr,subtype='PCM_24')
    record=dict(label=label,group=group,test_name=name,path=str(dest),sha256=sha(dest),
     source_path=row['path'],source_sha256=sha(row['path']),expected_text=row['expected_text'],text_origin=row['text_origin'],
     reference_path=str(reference),reference_sha256=sha(reference),convert_style=style,diffusion_steps=30,
     intelligibility_cfg=.7,similarity_cfg=.7,seed=20261003,source_seconds=len(x)/sr,output_seconds=len(y)/model.sr,
     offline_file_seconds=elapsed,peak_cuda_bytes=torch.cuda.max_memory_allocated(),board_deployed=False,causal_streaming=False,
     source_speaker_enrollment=False,audio_uploaded=False)
    if args.checkpoint:record.update(checkpoint=str(args.checkpoint),checkpoint_sha256=sha(args.checkpoint))
    if 'voice' in row:record['same_text_target']='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'
    records.append(record);save(OUT/'conversion_items.json',records)
    print('DONE '+label+' '+str(round(elapsed,2))+'s',flush=True)
 save(OUT/'run_status.json',dict(status='complete',converted=len(records),subjectively_accepted=False))
if __name__=='__main__':main()
