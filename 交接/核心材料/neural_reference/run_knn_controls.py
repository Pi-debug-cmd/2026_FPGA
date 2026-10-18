"""Official kNN-VC fixed target unit pool; no source registration or audio upload."""
from pathlib import Path
import os,sys,json,hashlib,time
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;ROOT=BASE/'kNN-VC';ASSETS=BASE/'knn_assets'
OUT=Path('D:/总进度/目标人物分析/kNN语音单位转换');OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
import torch,numpy as np,soundfile as sf,torchaudio
from wavlm.WavLM import WavLM,WavLMConfig
from hifigan.models import Generator
from hifigan.utils import AttrDict
from matcher import KNeighborsVC,fast_cosine_dist
torch.set_num_threads(4)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def load_model():
 manifest=read(ASSETS/'manifest.json');paths={f['name']:f for f in manifest['files']}
 for f in paths.values():assert sha(f['path'])==f['sha256']
 state=torch.load(paths['WavLM-Large.pt']['path'],map_location='cpu',weights_only=True)
 cfg=WavLMConfig(state['cfg']);encoder=WavLM(cfg)
 for k,p in encoder.named_parameters():assert k in state['model'] and state['model'][k].shape==p.shape
 encoder.load_state_dict(state['model'],strict=True);del state
 h=AttrDict(read(ROOT/'hifigan/config_v1_wavlm.json'));vocoder=Generator(h)
 state=torch.load(paths['prematch_g_02500000.pt']['path'],map_location='cpu',weights_only=True)['generator']
 for k,p in vocoder.named_parameters():assert k in state and state[k].shape==p.shape
 vocoder.load_state_dict(state,strict=True);del state
 vocoder.remove_weight_norm();encoder=encoder.to('cuda').eval();vocoder=vocoder.to('cuda').eval()
 model=KNeighborsVC(encoder,vocoder,h,device='cuda')
 save(OUT/'model_load_validation.json',dict(assets=manifest,all_learned_parameters_loaded=True,strict_loading=True,
  encoder_parameters=sum(p.numel() for p in encoder.parameters()),vocoder_parameters=sum(p.numel() for p in vocoder.parameters()),
  source_python_hashes={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*.py')},
  no_source_changes=True,board_deployed=False,audio_uploaded=False))
 return model
def main():
 model=load_model()
 references=[];waves=[];pool_members=[];offset=0
 for n in range(5,9):
  p=Path(f'D:/总进度/目标人物语音/Track {n}.wav');x,sr=sf.read(p,dtype='float32');x=x.mean(axis=1)
  wave=torchaudio.functional.resample(torch.from_numpy(x).unsqueeze(0),sr,16000)
  wave*=.04/max(float(wave.square().mean().sqrt()),1e-8)
  # Retain all speech; VAD trimming disabled to avoid unsupported Windows sox.
  feature=model.get_features(wave,vad_trigger_level=0).cpu()
  waves.append(feature);pool_members.append(dict(track=n,start_frame=offset,end_frame=offset+len(feature)))
  offset+=len(feature);references.append(dict(path=str(p),sha256=sha(p),seconds=len(x)/sr,feature_frames=len(feature)))
 pool=torch.cat(waves,dim=0).to('cuda')
 torch.save(dict(features=pool.cpu(),members=pool_members,references=references,layer=6),OUT/'fixed_target_unit_pool.pt')
 save(OUT/'pool_manifest.json',dict(references=references,total_seconds=sum(r['seconds'] for r in references),
  frames=len(pool),feature_dimension=pool.shape[1],layer=6,pool_sha256=sha(OUT/'fixed_target_unit_pool.pt'),
  track9_included=False,source_registered=False,vad_trim=False,causal_streaming=False))
 rows=read(Path('D:/总进度/目标人物分析/音色与自然度复查/neural_control_manifest.json'))['files']
 rows += [r for r in read(BASE/'public_chinese_validation/validation_manifest.json')['files']
  if r['label'] in ['validation_source_BAC009S0004W0121','validation_source_fleurs_test_row3_id1852']]
 records=[]
 for row in rows:
  name=row.get('voice',row['label'].removeprefix('validation_source_'));assert sha(row['path'])==row['sha256']
  x,sr=sf.read(row['path'],dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
  wave=torchaudio.functional.resample(torch.from_numpy(x).unsqueeze(0),sr,16000)
  wave*=.04/max(float(wave.square().mean().sqrt()),1e-8)
  inp=OUT/'inputs';inp.mkdir(exist_ok=True);source=inp/(name+'.wav');sf.write(source,wave.squeeze().numpy(),16000,subtype='PCM_24')
  torch.cuda.reset_peak_memory_stats();started=time.perf_counter();query=model.get_features(wave,vad_trigger_level=0)
  best=fast_cosine_dist(query,pool,device='cuda').topk(k=4,largest=False,dim=-1)
  # Official match uses exactly this k=4 cosine neighborhood and prematched vocoder.
  # No top-k parameter sweep, output time scaling, pitch/EQ edits, or loudness effects.
  output=model.match(query,pool,topk=4,tgt_loudness_db=None).numpy()
  torch.cuda.synchronize();elapsed=time.perf_counter()-started
  assert np.isfinite(output).all() and np.sqrt(np.mean(output*output))>1e-6
  output*=min(.04/float(np.sqrt(np.mean(output*output))),.95/float(np.max(np.abs(output))))
  dest=OUT/(name+'_knn.wav');sf.write(dest,output,16000,subtype='PCM_24')
  counts={str(r['track']):int(((best.indices>=r['start_frame']) & (best.indices<r['end_frame'])).sum()) for r in pool_members}
  record=dict(label='knn_prematched_k4_'+name,group='knn_prematched_k4',test_name=name,path=str(dest),sha256=sha(dest),
   source_path=row['path'],source_sha256=sha(row['path']),expected_text=row['expected_text'],text_origin=row['text_origin'],
   source_seconds=len(x)/sr,output_seconds=len(output)/16000,offline_file_seconds=elapsed,
   nearest_cosine_distance_mean=float(best.values[:,0].mean()),nearest_cosine_distance_p95=float(best.values[:,0].quantile(.95)),
   top4_unit_counts_by_target_track=counts,topk=4,query_frames=len(query),peak_cuda_bytes=torch.cuda.max_memory_allocated(),
   target_pool_sha256=sha(OUT/'fixed_target_unit_pool.pt'),source_speaker_enrollment=False,board_deployed=False,
   causal_streaming=False,audio_uploaded=False)
  if 'voice' in row:record['same_text_target']='D:/总进度/目标人物分析/素材同文本普通声转换对比/目标人物原声_试听.wav'
  records.append(record);save(OUT/'conversion_items.json',records);print('KNN CONVERT '+name+' '+str(round(elapsed,2))+'s',flush=True)
 save(OUT/'run_status.json',dict(status='complete',converted=len(records),subjectively_accepted=False,board_deployed=False))
 print('KNN CONTROLS COMPLETE',flush=True)
if __name__=='__main__':main()
