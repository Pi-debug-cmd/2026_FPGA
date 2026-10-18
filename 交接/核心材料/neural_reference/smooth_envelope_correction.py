"""Test temporal regularization of the phone-local residual, not another CFM grid."""
from pathlib import Path
import sys,json,hashlib
import torch,numpy as np,soundfile as sf
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;ROOT=BASE/'Seed-VC';OUT=Path('D:/总进度/目标人物分析/局部音色包络校正')
sys.path.insert(0,str(ROOT))
from modules.bigvgan.bigvgan import BigVGAN
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 manifest=read(ROOT/'checkpoints/pinned/strong_manifest.json')
 asset=next(r for r in manifest if r['repository']=='nvidia/bigvgan_v2_22khz_80band_256x')
 for f in asset['files']:assert sha(f['path'])==f['sha256']
 vocoder=BigVGAN.from_pretrained(asset['local'],use_cuda_kernel=False);vocoder.remove_weight_norm();vocoder=vocoder.to('cuda').eval()
 torch.set_num_threads(4)
 rows=[r for r in read(OUT/'conversion_items.json') if r['amount']==.25]
 records=[];roughness=[];alpha=1-np.exp(-256/22050/.04)
 for row in rows:
  d=np.load(OUT/(row['test_name']+'_mel_diagnostics.npz'));base=d['baseline_mel'];residual=d['bounded_residual']
  filtered=np.empty_like(residual);state=np.zeros(residual.shape[0],dtype='float32')
  for t in range(residual.shape[1]):
   state+=alpha*(residual[:,t]-state);filtered[:,t]=state
  raw_diff=float(np.sqrt(np.mean(np.diff(residual,axis=1)**2)));smooth_diff=float(np.sqrt(np.mean(np.diff(filtered,axis=1)**2)))
  roughness.append(dict(test_name=row['test_name'],residual_frame_difference_rms_before=raw_diff,
   residual_frame_difference_rms_after=smooth_diff,ratio=smooth_diff/raw_diff,causal_ema_seconds=.04))
  corrected=base+.2*filtered
  with torch.no_grad():y=vocoder(torch.from_numpy(corrected).unsqueeze(0).to('cuda')).squeeze().cpu().numpy()
  assert np.isfinite(y).all() and np.sqrt(np.mean(y*y))>1e-6
  y*=min(.04/float(np.sqrt(np.mean(y*y))),.95/float(np.max(np.abs(y))))
  folder=OUT/'smoothed_envelope_0.2';folder.mkdir(exist_ok=True);dest=folder/(row['test_name']+'.wav')
  sf.write(dest,y,22050,subtype='PCM_24')
  records.append(dict(row,label='smoothed_envelope_0.2_'+row['test_name'],group='smoothed_envelope_0.2',
   path=str(dest),sha256=sha(dest),amount=.2,causal_envelope_ema_seconds=.04,
   causal_streaming=False,envelope_filter_uses_future_frames=False,
   content_features_have_full_utterance_context=True,subjective_acceptance=False))
 save(OUT/'smoothed_items.json',records);save(OUT/'temporal_residual_diagnostics.json',roughness)
 print('SMOOTH ENVELOPE COMPLETE',flush=True)
if __name__=='__main__':main()
