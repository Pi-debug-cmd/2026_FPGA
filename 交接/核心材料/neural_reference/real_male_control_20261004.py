"""One actual male input with fixed retained model/correction; no new tuning."""
from pathlib import Path
from types import SimpleNamespace
import torch,numpy as np,soundfile as sf,torchaudio
from scipy.fft import dct,idct
from scipy.interpolate import interp1d
import run_knn_controls as knn,personalize_seed_teacher as personal
OUT=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
read=knn.read;save=knn.save;sha=knn.sha
def main():
 row=next(r for r in read(personal.OUT/'personal_cfg0.3_steps30_items.json') if r['test_name']=='fleurs_test_row0_id1906')
 source=personal.OUT/'test_inputs/fleurs_test_row0_id1906.wav';ref=Path(row['reference_path'])
 for key,hkey in [('path','sha256'),('source_path','source_sha256'),('reference_path','reference_sha256')]:assert sha(row[key])==row[hkey]
 assert sha(row['checkpoint']['path'])==row['checkpoint']['sha256']
 retrieval=knn.load_model();pool_file=knn.OUT/'fixed_target_unit_pool.pt';assert sha(pool_file)==read(knn.OUT/'pool_manifest.json')['pool_sha256']
 pool=torch.load(pool_file,map_location='cpu',weights_only=True);pool_gpu=pool['features'].to('cuda')
 personal.pinned_loaders();import inference
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,auto_f0_adjust=False,
  semi_tone_shift=0,checkpoint=row['checkpoint']['path'],config=str(personal.OUT/'personal_strong_config.yml'),fp16=True)
 loaded=inference.load_models(SimpleNamespace(**kwargs));vocoder=loaded[3];mel=loaded[5];target_mels=[]
 with torch.no_grad():
  for r in pool['references']:
   assert sha(r['path'])==r['sha256'];x,sr=sf.read(r['path'],dtype='float32');x=x.mean(axis=1)
   wave=torchaudio.functional.resample(torch.from_numpy(x).unsqueeze(0),sr,22050);wave*=.04/max(float(wave.square().mean().sqrt()),1e-8)
   m=mel(wave.to('cuda')).squeeze().cpu().numpy();mt=(np.arange(m.shape[1])*256+128)/22050;ft=(np.arange(r['feature_frames'])*320+199.5)/16000
   target_mels.append(interp1d(mt,m,axis=1,bounds_error=False,fill_value=(m[:,0],m[:,-1]))(ft).T)
 target_mels=np.concatenate(target_mels).astype('float32');assert len(target_mels)==len(pool['features']);capture={}
 def captured(m):capture['mel']=m.detach().cpu().numpy()[0].copy();return vocoder(m)
 wrapped=(*loaded[:3],captured,*loaded[4:]);inference.load_models=lambda _:wrapped
 folder=OUT/'raw300_reproduction';folder.mkdir(exist_ok=True);torch.manual_seed(20261003)
 inference.main(SimpleNamespace(**kwargs,source=str(source),target=str(ref),output=str(folder)))
 dest=folder/f'vc_{source.stem}_{ref.stem}_1.0_30_0.3.wav';y,sr=sf.read(dest,dtype='float32');z,zsr=sf.read(row['path'],dtype='float32')
 assert sr==zsr and y.shape==z.shape;error=float(np.max(np.abs(y-z)));assert error==0,error
 base=capture['mel'];qw=torchaudio.functional.resample(torch.from_numpy(y).unsqueeze(0),sr,16000);qw*=.04/max(float(qw.square().mean().sqrt()),1e-8)
 q=retrieval.get_features(qw,vad_trigger_level=0);best=knn.fast_cosine_dist(q,pool_gpu,device='cuda').topk(k=4,largest=False,dim=-1)
 matched=target_mels[best.indices.cpu().numpy()].mean(axis=1).T;qt=(np.arange(matched.shape[1])*320+199.5)/16000;bt=(np.arange(base.shape[1])*256+128)/22050
 desired=interp1d(qt,matched,axis=1,bounds_error=False,fill_value=(matched[:,0],matched[:,-1]))(bt)
 delta=np.zeros_like(base);delta[1:17]=dct(desired,axis=0,norm='ortho')[1:17]-dct(base,axis=0,norm='ortho')[1:17]
 residual=idct(delta,axis=0,norm='ortho').astype('float32');residual*=np.minimum(1.,.8/np.maximum(np.max(np.abs(residual),axis=0,keepdims=True),1e-8))
 filtered=np.empty_like(residual);state=np.zeros(80,dtype='float32');alpha=1-np.exp(-256/22050/.04)
 for t in range(residual.shape[1]):state+=alpha*(residual[:,t]-state);filtered[:,t]=state
 with torch.no_grad():output=vocoder(torch.from_numpy(base+.2*filtered).unsqueeze(0).to('cuda')).squeeze().cpu().numpy()
 assert np.isfinite(output).all() and np.sqrt(np.mean(output*output))>1e-6;output*=min(.04/float(np.sqrt(np.mean(output*output))),.95/float(np.max(np.abs(output))))
 dest=OUT/'现有真人男声_固定旧模型与0.2校正.wav';sf.write(dest,output,22050,subtype='PCM_24')
 corrected=dict(row,label='real_input_retained300_smoothed0.2_fleurs_male',group='fixed_real_male_control',
  path=str(dest),sha256=sha(dest),amount=.2,causal_envelope_ema_seconds=.04,source_gender_metadata='male',
  prepared_source_path=str(source),prepared_source_sha256=sha(source),source_speaker_identity_metadata=None,
  target_pool_sha256=sha(pool_file),causal_streaming=False,subjective_acceptance=False,audio_uploaded=False)
 source_row=dict(label='actual_male_input_fleurs1906',group='input_controls',test_name=row['test_name'],
  path=row['source_path'],sha256=row['source_sha256'],expected_text=row['expected_text'],text_origin=row['text_origin'])
 save(OUT/'evaluation_items.json',[source_row,row,corrected])
 save(OUT/'real_input_manifest.json',dict(status='complete',source=source_row,corrected=corrected,
  raw_reproduction_max_sample_error=error,new_corrected_conversions=1,new_training=False,new_parameters_tuned=False,
  source_registration=False,source_used_for_target_training=False,gender_from_dataset_metadata=True,
  source_text_differs_from_prior_synthetic_control=True,no_matched_input_causality_claim=True,
  target9_not_conditioning=True,board_deployed=False,audio_uploaded=False,subjective_acceptance=False,script_sha256=sha(__file__)))
 print('ACTUAL MALE FIXED CONTROL COMPLETE',flush=True)
if __name__=='__main__':main()
