"""Experimental phoneme-local cepstral envelope residual on the preferred V1.
Uses fixed target5-8 only. Not static EQ, pitch shift, source registration, or
an accepted conversion method. Official CFM/vocoder weights remain untouched.
"""
from pathlib import Path
from types import SimpleNamespace
import torch,numpy as np,soundfile as sf,torchaudio
import run_knn_controls as knn
import personalize_seed_teacher as personal
import shutil
from scipy.fft import dct,idct
from scipy.interpolate import interp1d
BASE=personal.BASE;OUT=Path('D:/总进度/目标人物分析/局部音色包络校正');OUT.mkdir(parents=True,exist_ok=True)
read=knn.read;save=knn.save;sha=knn.sha
def main():
 retrieval=knn.load_model();pool_file=knn.OUT/'fixed_target_unit_pool.pt'
 assert sha(pool_file)==read(knn.OUT/'pool_manifest.json')['pool_sha256']
 pool=torch.load(pool_file,map_location='cpu',weights_only=True)
 personal.pinned_loaders();import inference
 ckpt=next(r for r in read(personal.OUT/'training_run.json')['checkpoints'] if r['step']==300)
 assert sha(ckpt['path'])==ckpt['sha256']
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,auto_f0_adjust=False,
  semi_tone_shift=0,checkpoint=ckpt['path'],config=str(personal.OUT/'personal_strong_config.yml'),fp16=True)
 loaded=inference.load_models(SimpleNamespace(**kwargs));vocoder=loaded[3];mel=loaded[5]
 # Same target time points as WavLM receptive-field centers (400/320 samples).
 # Match mel centers after Seed's explicit384-sample padding:128+256*t at22.05k.
 target_mels=[]
 with torch.no_grad():
  for r in pool['references']:
   assert sha(r['path'])==r['sha256']
   x,sr=sf.read(r['path'],dtype='float32');x=x.mean(axis=1)
   wave=torchaudio.functional.resample(torch.from_numpy(x).unsqueeze(0),sr,22050)
   wave*=.04/max(float(wave.square().mean().sqrt()),1e-8)
   m=mel(wave.to('cuda')).squeeze().cpu().numpy()
   mt=(np.arange(m.shape[1])*256+128)/22050
   ft=(np.arange(r['feature_frames'])*320+199.5)/16000
   target_mels.append(interp1d(mt,m,axis=1,bounds_error=False,fill_value=(m[:,0],m[:,-1]))(ft).T)
 target_mels=np.concatenate(target_mels,axis=0).astype('float32');assert len(target_mels)==len(pool['features'])
 pool_gpu=pool['features'].to('cuda');capture={}
 def capture_vocoder(m):
  capture['mel']=m.detach().cpu().numpy()[0].copy()
  return vocoder(m)
 wrapped=(*loaded[:3],capture_vocoder,*loaded[4:]);inference.load_models=lambda _:wrapped
 rows=read(knn.OUT/'conversion_items.json');records=[];reproductions=[]
 ref=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
 review=Path('D:/总进度/目标人物分析/音色与自然度复查')
 old=[r for r in read(review/'seed_neural_items.json') if r['group']=='seed_personal300_cfg03']
 old += [r for r in read(personal.OUT/'personal_cfg0.3_steps30_items.json') if r['test_name'] in ['fleurs_test_row3_id1852','BAC009S0004W0121']]
 baseline={r['source_sha256']:r for r in old}
 for row in rows:
  # Reuse exact prepared PCM used by the historic baseline. One PCM24-LSB
  # from float normalization ordering can propagate through the FP16 model.
  prepared=(review/'inputs' if row['test_name'] in ['zm_010','zf_001'] else personal.OUT/'test_inputs')/(row['test_name']+'.wav')
  folder=OUT/'inputs';folder.mkdir(exist_ok=True);source=folder/(row['test_name']+'.wav')
  shutil.copyfile(prepared,source)
  folder=OUT/'baseline';folder.mkdir(exist_ok=True);torch.manual_seed(20261003);capture.clear()
  inference.main(SimpleNamespace(**kwargs,source=str(source),target=str(ref),output=str(folder)))
  original=folder/f'vc_{source.stem}_{ref.stem}_1.0_30_0.3.wav';y,ysr=sf.read(original,dtype='float32')
  previous=baseline[row['source_sha256']];z,zsr=sf.read(previous['path'],dtype='float32')
  assert ysr==zsr and y.shape==z.shape
  difference=float(np.max(np.abs(y-z)));assert difference<=2/32768
  reproductions.append(dict(test_name=row['test_name'],max_sample_error=difference,previous_path=previous['path']))
  base=capture['mel'];query_wave=torchaudio.functional.resample(torch.from_numpy(y).unsqueeze(0),ysr,16000)
  query_wave*=.04/max(float(query_wave.square().mean().sqrt()),1e-8)
  q=retrieval.get_features(query_wave,vad_trigger_level=0)
  best=knn.fast_cosine_dist(q,pool_gpu,device='cuda').topk(k=4,largest=False,dim=-1)
  matched=target_mels[best.indices.cpu().numpy()].mean(axis=1).T
  qt=(np.arange(matched.shape[1])*320+199.5)/16000;bt=(np.arange(base.shape[1])*256+128)/22050
  desired=interp1d(qt,matched,axis=1,bounds_error=False,fill_value=(matched[:,0],matched[:,-1]))(bt)
  current_c=dct(base,axis=0,norm='ortho');desired_c=dct(desired,axis=0,norm='ortho')
  delta=np.zeros_like(current_c);delta[1:17]=desired_c[1:17]-current_c[1:17]
  residual=idct(delta,axis=0,norm='ortho').astype('float32')
  # Bound local log-mel adjustment; energy coefficient0 and higher cepstra unchanged.
  residual*=np.minimum(1.,.8/np.maximum(np.max(np.abs(residual),axis=0,keepdims=True),1e-8))
  projected=dct(residual,axis=0,norm='ortho')
  assert np.max(np.abs(projected[0]))<2e-5 and np.max(np.abs(projected[17:]))<2e-5
  for amount in [.25,.5]:
   corrected=base+amount*residual
   with torch.no_grad():output=vocoder(torch.from_numpy(corrected).unsqueeze(0).to('cuda')).squeeze().cpu().numpy()
   assert np.isfinite(output).all() and np.sqrt(np.mean(output*output))>1e-6
   output*=min(.04/float(np.sqrt(np.mean(output*output))),.95/float(np.max(np.abs(output))))
   group='retrieved_envelope_'+str(amount);folder=OUT/group;folder.mkdir(exist_ok=True)
   dest=folder/(row['test_name']+'.wav');sf.write(dest,output,22050,subtype='PCM_24')
   record=dict(label=group+'_'+row['test_name'],group=group,test_name=row['test_name'],path=str(dest),sha256=sha(dest),
    source_path=row['source_path'],source_sha256=row['source_sha256'],expected_text=row['expected_text'],text_origin=row['text_origin'],
    checkpoint=ckpt,amount=amount,cepstral_indices=[1,16],residual_log_mel_clip=.8,topk=4,
    target_pool_sha256=sha(pool_file),reference_path=str(ref),source_speaker_enrollment=False,board_deployed=False,
    prepared_source_path=str(prepared),prepared_source_sha256=sha(prepared),
    causal_streaming=False,audio_uploaded=False,subjective_acceptance=False,source_seconds=row['source_seconds'],
    output_seconds=len(output)/22050,source_pitch_shift_applied=False)
   if 'same_text_target' in row:record['same_text_target']=row['same_text_target']
   records.append(record);save(OUT/'conversion_items.json',records)
  np.savez_compressed(OUT/(row['test_name']+'_mel_diagnostics.npz'),baseline_mel=base,retrieved_mel=desired,
   bounded_residual=residual,nearest_indices=best.indices.cpu().numpy())
  save(OUT/'baseline_reproductions.json',reproductions)
 save(OUT/'algorithm_manifest.json',dict(status='complete',conversions=len(records),pool_tracks=[5,6,7,8],
  heldout9_used_for_conditioning=False,checkpoint=ckpt,pretrained_weights_overwritten=False,
  method='V1 generated mel + bounded low-cepstral residual from k4 nearest target units; preserve coefficient0/higher cepstra',
  amounts=[.25,.5],primary_code=str(Path(__file__).resolve()),code_sha256=sha(__file__),
  limitation='Experimental offline correction; no perceptual/causal/board acceptance. Per-frame scalar bounding preserves the low-cepstral subspace.'))
 print('RETRIEVAL ENVELOPE COMPLETE',flush=True)
if __name__=='__main__':main()
