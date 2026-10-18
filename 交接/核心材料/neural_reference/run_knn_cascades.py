from pathlib import Path
from types import SimpleNamespace
import time
import run_knn_controls as knn
import torch,numpy as np,soundfile as sf,torchaudio
OUT=knn.OUT;BASE=knn.BASE;read=knn.read;save=knn.save;sha=knn.sha
def common(row):
 return {k:v for k,v in row.items() if k in ['test_name','source_path','source_sha256','expected_text','text_origin',
  'source_seconds','same_text_target','target_pool_sha256','source_speaker_enrollment','board_deployed','causal_streaming','audio_uploaded']}
def main():
 sources=read(OUT/'conversion_items.json')
 review=Path('D:/总进度/目标人物分析/音色与自然度复查');personal=Path('D:/总进度/目标人物分析/SeedVC人物微调')
 baseline=[r for r in read(review/'seed_neural_items.json') if r['group']=='seed_personal300_cfg03']
 baseline += [r for r in read(personal/'personal_cfg0.3_steps30_items.json') if r['test_name'] in ['fleurs_test_row3_id1852','BAC009S0004W0121']]
 old={r['source_sha256']:r for r in baseline}
 model=knn.load_model();poolstate=torch.load(OUT/'fixed_target_unit_pool.pt',map_location='cpu',weights_only=True)
 assert sha(OUT/'fixed_target_unit_pool.pt')==read(OUT/'pool_manifest.json')['pool_sha256']
 pool=poolstate['features'].to('cuda');records=[]
 for row in sources:
  first=old[row['source_sha256']];assert sha(first['path'])==first['sha256']
  x,sr=sf.read(first['path'],dtype='float32');wave=torchaudio.functional.resample(torch.from_numpy(x).unsqueeze(0),sr,16000)
  wave*=.04/max(float(wave.square().mean().sqrt()),1e-8);started=time.perf_counter()
  query=model.get_features(wave,vad_trigger_level=0);y=model.match(query,pool,topk=4,tgt_loudness_db=None).numpy()
  assert np.isfinite(y).all();y*=min(.04/float(np.sqrt(np.mean(y*y))),.95/float(np.max(np.abs(y))))
  folder=OUT/'seed_then_knn';folder.mkdir(exist_ok=True);dest=folder/(row['test_name']+'.wav');sf.write(dest,y,16000,subtype='PCM_24')
  r=dict(common(row),label='seed_then_knn_'+row['test_name'],group='seed_then_knn',path=str(dest),sha256=sha(dest),
   intermediate_path=first['path'],intermediate_sha256=first['sha256'],
   second_stage_seconds=time.perf_counter()-started,output_seconds=len(y)/16000)
  records.append(r);save(OUT/'cascade_items.json',records);print('SEED THEN KNN '+row['test_name'],flush=True)
 del model,pool,poolstate;torch.cuda.empty_cache()
 import personalize_seed_teacher as teacher
 teacher.pinned_loaders();import inference
 ckpt=next(r for r in read(teacher.OUT/'training_run.json')['checkpoints'] if r['step']==300)
 assert sha(ckpt['path'])==ckpt['sha256']
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,auto_f0_adjust=False,
  semi_tone_shift=0,checkpoint=ckpt['path'],config=str(teacher.OUT/'personal_strong_config.yml'),fp16=True)
 loaded=inference.load_models(SimpleNamespace(**kwargs));inference.load_models=lambda _:loaded
 ref=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
 for row in sources:
  assert sha(row['path'])==row['sha256'];folder=OUT/'knn_then_seed';folder.mkdir(exist_ok=True)
  torch.manual_seed(20261003);started=time.perf_counter()
  inference.main(SimpleNamespace(**kwargs,source=row['path'],target=str(ref),output=str(folder)))
  stem=Path(row['path']).stem;dest=folder/f'vc_{stem}_{ref.stem}_1.0_30_0.3.wav'
  x,sr=sf.read(dest);assert np.isfinite(x).all()
  r=dict(common(row),label='knn_then_seed_'+row['test_name'],group='knn_then_seed',path=str(dest),sha256=sha(dest),
   intermediate_path=row['path'],intermediate_sha256=row['sha256'],second_stage_seconds=time.perf_counter()-started,
   output_seconds=len(x)/sr,final_checkpoint=ckpt)
  records.append(r);save(OUT/'cascade_items.json',records);print('KNN THEN SEED '+row['test_name'],flush=True)
 print('KNN CASCADES COMPLETE',flush=True)
if __name__=='__main__':main()
