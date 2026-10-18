"""Close 2x2 control: old/new acoustic model, with/without same 0.2 correction."""
from pathlib import Path
from types import SimpleNamespace
import torch,numpy as np,soundfile as sf,torchaudio
from scipy.fft import dct,idct
from scipy.interpolate import interp1d
import run_knn_controls as knn
import personalize_seed_teacher as personal
BASE=personal.BASE;AC=Path('D:/总进度/目标人物分析/声学生成改进_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/局部音色包络校正')
OUT=Path('D:/总进度/目标人物分析/模型与校正组合对照_2026-10-04');OUT.mkdir(exist_ok=True)
read=knn.read;save=knn.save;sha=knn.sha
def feedback():
 d=read(AC/'decision.json');d.update(status='human_rejected_acoustic_training_no_gain',hearing_result='rejected',
  human_feedback='还是有，为什么不加音色矫正，之前有加吗，没有改进',human_feedback_date='2026-10-04',
  subjective_acceptance=False,candidate_promoted=False,next_step='Complete controlled 2x2 old/new model x off/same0.2 correction; no stronger sweep.')
 save(AC/'decision.json',d);save(OUT/'human_feedback.json',dict(date='2026-10-04',feedback=d['human_feedback'],
  raw1000_rejected=True,prior0_2_relative_gain_retained=True,subjective_acceptance=False))
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 heading='## 最新：追加训练未改善，补齐模型与校正组合（2026-10-04）'
 if heading not in s:
  t=heading+'\n\n用户明确反馈“还是有，为什么不加音色矫正，之前有加吗，没有改进”。累计1000步、不加校正的转换拒绝，不进入部署。解释：较早有改善的0.2及其0.3对照加过校正；上一轮原300与新1000两段都没有加，为隔离训练变化。原0.2的相对改善仍保留，但也未通过自然度验收。现在补齐同四输入的2×2：旧300不加/加0.2、新1000不加/加同一0.2，既有12文件固定保留，仅生成新1000+0.2四条。目标库Track5—8/40ms平滑/校正方法不变，不增加强度或反复训练。电脑组合检查中，无需上电或补录。自动分数不能确认鼻音改善，原声重建接近不算转换通过。此条覆盖上一轮待无校正新模型试听状态。\n\n'
  s=s.replace('## 最新：原声重建接近，',t+'## 最新：原声重建接近，',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');heading='## Latest: raw1000 rejected; close old/new x correction-off/on control — 2026-10-04'
 if heading not in s:
  first,rest=s.split('\n',1);s=first+'\n\n'+heading+'\n\nHuman: '+d['human_feedback']+'. Raw1000 not accepted. Prior0.2 relative improvement remains but unnatural. Earlier strength0.2/0.3 audition used correction; previous raw300/raw1000 audition omitted it on both sides to isolate training. Close2x2 with four new1000+same0.2 outputs and12 immutable existing controls. No new strength/training sweep, source registration or hardware action. PC combination screen in progress, no acceptance.\n'+rest;p.write_text(s,encoding='utf-8')
def main():
 feedback();print('RAW1000 REJECTION SAVED',flush=True)
 retrieval=knn.load_model();pool_file=knn.OUT/'fixed_target_unit_pool.pt'
 assert sha(pool_file)==read(knn.OUT/'pool_manifest.json')['pool_sha256']
 pool=torch.load(pool_file,map_location='cpu',weights_only=True);pool_gpu=pool['features'].to('cuda')
 rows=[r for r in read(AC/'conversion_items.json') if r['group']=='acoustic_total1000'];assert len(rows)==4
 personal.pinned_loaders();import inference
 ckpt=rows[0]['checkpoint'];assert sha(ckpt['path'])==ckpt['sha256']
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,auto_f0_adjust=False,
  semi_tone_shift=0,checkpoint=ckpt['path'],config=str(AC/'acoustic_control.yml'),fp16=True)
 loaded=inference.load_models(SimpleNamespace(**kwargs));vocoder=loaded[3];mel=loaded[5]
 target_mels=[]
 with torch.no_grad():
  for r in pool['references']:
   assert sha(r['path'])==r['sha256']
   x,sr=sf.read(r['path'],dtype='float32');x=x.mean(axis=1)
   wave=torchaudio.functional.resample(torch.from_numpy(x).unsqueeze(0),sr,22050)
   wave*=.04/max(float(wave.square().mean().sqrt()),1e-8)
   m=mel(wave.to('cuda')).squeeze().cpu().numpy();mt=(np.arange(m.shape[1])*256+128)/22050
   ft=(np.arange(r['feature_frames'])*320+199.5)/16000
   target_mels.append(interp1d(mt,m,axis=1,bounds_error=False,fill_value=(m[:,0],m[:,-1]))(ft).T)
 target_mels=np.concatenate(target_mels,axis=0).astype('float32');assert len(target_mels)==len(pool['features'])
 capture={}
 def captured(m):capture['mel']=m.detach().cpu().numpy()[0].copy();return vocoder(m)
 wrapped=(*loaded[:3],captured,*loaded[4:]);inference.load_models=lambda _:wrapped
 records=[];reproductions=[];alpha=1-np.exp(-256/22050/.04)
 for row in rows:
  for key,hkey in [('path','sha256'),('source_path','source_sha256'),('prepared_source_path','prepared_source_sha256')]:assert sha(row[key])==row[hkey]
  source=Path(row['prepared_source_path']);ref=Path(row['reference_path']);folder=OUT/'raw1000_reproduction';folder.mkdir(exist_ok=True)
  torch.manual_seed(20261003);capture.clear()
  inference.main(SimpleNamespace(**kwargs,source=str(source),target=str(ref),output=str(folder)))
  dest=folder/f'vc_{source.stem}_{ref.stem}_1.0_30_0.3.wav';y,ysr=sf.read(dest,dtype='float32');z,zsr=sf.read(row['path'],dtype='float32')
  assert ysr==zsr and y.shape==z.shape;error=float(np.max(np.abs(y-z)));assert error==0,error
  reproductions.append(dict(test_name=row['test_name'],max_sample_error=error,previous_path=row['path'],previous_sha256=row['sha256']))
  base=capture['mel'];query_wave=torchaudio.functional.resample(torch.from_numpy(y).unsqueeze(0),ysr,16000)
  query_wave*=.04/max(float(query_wave.square().mean().sqrt()),1e-8);q=retrieval.get_features(query_wave,vad_trigger_level=0)
  best=knn.fast_cosine_dist(q,pool_gpu,device='cuda').topk(k=4,largest=False,dim=-1)
  matched=target_mels[best.indices.cpu().numpy()].mean(axis=1).T
  qt=(np.arange(matched.shape[1])*320+199.5)/16000;bt=(np.arange(base.shape[1])*256+128)/22050
  desired=interp1d(qt,matched,axis=1,bounds_error=False,fill_value=(matched[:,0],matched[:,-1]))(bt)
  a=dct(base,axis=0,norm='ortho');b=dct(desired,axis=0,norm='ortho');delta=np.zeros_like(a);delta[1:17]=b[1:17]-a[1:17]
  residual=idct(delta,axis=0,norm='ortho').astype('float32')
  residual*=np.minimum(1.,.8/np.maximum(np.max(np.abs(residual),axis=0,keepdims=True),1e-8))
  projected=dct(residual,axis=0,norm='ortho');assert np.max(np.abs(projected[0]))<2e-5 and np.max(np.abs(projected[17:]))<2e-5
  filtered=np.empty_like(residual);state=np.zeros(residual.shape[0],dtype='float32')
  for t in range(residual.shape[1]):state+=alpha*(residual[:,t]-state);filtered[:,t]=state
  with torch.no_grad():output=vocoder(torch.from_numpy(base+.2*filtered).unsqueeze(0).to('cuda')).squeeze().cpu().numpy()
  assert np.isfinite(output).all() and np.sqrt(np.mean(output*output))>1e-6
  output*=min(.04/float(np.sqrt(np.mean(output*output))),.95/float(np.max(np.abs(output))))
  folder=OUT/'acoustic1000_smoothed0.2';folder.mkdir(exist_ok=True);dest=folder/(row['test_name']+'.wav');sf.write(dest,output,22050,subtype='PCM_24')
  record=dict(row,label='acoustic1000_smoothed0.2_'+row['test_name'],group='acoustic1000_smoothed0.2',path=str(dest),sha256=sha(dest),
   amount=.2,cepstral_correction_applied=True,causal_envelope_ema_seconds=.04,cepstral_indices=[1,16],
   residual_log_mel_clip=.8,topk=4,target_pool_sha256=sha(pool_file),causal_streaming=False,
   envelope_filter_uses_future_frames=False,content_features_have_full_utterance_context=True,
   human_feedback=None,subjective_acceptance=False,parent_raw_path=row['path'],parent_raw_sha256=row['sha256'])
  records.append(record);save(OUT/'conversion_items.json',records)
  np.savez_compressed(OUT/(row['test_name']+'_mel_diagnostics.npz'),baseline_mel=base,retrieved_mel=desired,
   bounded_residual=residual,smoothed_residual=filtered,nearest_indices=best.indices.cpu().numpy())
  save(OUT/'baseline_reproductions.json',reproductions);print('CORRECTED1000',row['test_name'],flush=True)
 save(OUT/'generation_manifest.json',dict(status='complete',new_corrected_conversions=4,raw_reproductions=4,script_sha256=sha(__file__),
  same_old_correction_recipe=True,amount=.2,ema_seconds=.04,pool_tracks=[5,6,7,8],pool_sha256=sha(pool_file),
  residual_recomputed_from_new_raw_model=True,track9_in_target_pool=False,training_performed=False,
  source_enrollment=False,board_deployed=False,causal_streaming=False,subjective_acceptance=False))
 print('COMBINATION CONTROLS COMPLETE',flush=True)
if __name__=='__main__':main()
