"""Bounded content-feature timing audit on training pairs only. Audio unchanged."""
from train_board_student_20261005 import BASE,CORPUS,read
from transformers import HubertModel
import torch,torch.nn as nn,torch.nn.functional as F
import numpy as np,json,time
torch.set_num_threads(4)
out=BASE.parent/'board_budget_20261005/teacher_content_timing';out.mkdir(exist_ok=True)
model=HubertModel.from_pretrained(str(BASE/'RVC/assets/hubert_base'),local_files_only=True).cuda().eval()
model.encoder.layers=nn.ModuleList(model.encoder.layers[:9])
for p in model.parameters():p.requires_grad_(False)
def features(x):
 with torch.inference_mode():
  wave=torch.tensor(x,device='cuda')[None]
  v=model(F.layer_norm(wave,wave.shape[-1:])).last_hidden_state[0]
  return F.normalize(v,dim=-1).cpu().numpy()
def align(a,b):
 n,m=len(a),len(b);cost=1-a@b.T;dp=np.full((n+1,m+1),np.inf,dtype='float32');trace=np.zeros((n+1,m+1),np.int8);dp[0,0]=0
 for i in range(1,n+1):
  center=i*m/n
  for j in range(max(1,int(center)-9),min(m,int(center)+9)+1):
   options=[dp[i-1,j-1],dp[i-1,j]+.025,dp[i,j-1]+.025]
   k=int(np.argmin(options));dp[i,j]=cost[i-1,j-1]+options[k];trace[i,j]=k
 assert np.isfinite(dp[n,m])
 groups=[[] for _ in range(n)];i,j=n,m
 while i>0 and j>0:
  groups[i-1].append(j-1);k=trace[i,j]
  if k==0:i-=1;j-=1
  elif k==1:i-=1
  else:j-=1
 assert i==j==0
 mapping=np.array([float(np.mean(g)) for g in groups],dtype='float32');assert np.all(np.diff(mapping)>=0)
 raw=np.clip(np.rint(np.linspace(0,m-1,n)),0,m-1).astype(int);aligned=np.clip(np.rint(mapping),0,m-1).astype(int)
 return mapping,cost[np.arange(n),raw],cost[np.arange(n),aligned]
rows=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'))['files'];records=[];begin=time.monotonic()
for row in [r for r in rows if r['split']=='train']:
 x,y=read(row['path']),read(row['teacher_path']);a,b=features(x),features(y);mapping,raw,aligned=align(a,b)
 centers=np.arange(len(a))*.02+.0125;teacher_centers=mapping*.02+.0125;delta=(teacher_centers-centers)*1000
 rms=np.array([np.sqrt(np.mean(x[max(0,int(t*16000)-160):min(len(x),int(t*16000)+160)]**2)) for t in centers]);active=rms>.003
 record=dict(filename=row['filename'],speaker=row['speaker'],split=row['split'],source_path=row['path'],teacher_path=row['teacher_path'],source_sha256=row['sha256'],teacher_sha256=row['teacher_sha256'],source_feature_frames=len(a),teacher_feature_frames=len(b),source_times_seconds=centers.tolist(),teacher_times_seconds=teacher_centers.tolist(),active_shift_percentiles_ms=np.percentile(delta[active],[5,50,95]).tolist(),active_mean_abs_shift_ms=float(np.mean(np.abs(delta[active]))),mean_cosine_cost_unaligned=float(np.mean(raw[active])),mean_cosine_cost_aligned=float(np.mean(aligned[active])),max_time_difference_ms=float(np.max(np.abs(delta))),audio_files_modified=False)
 records.append(record);print('TIMING',row['filename'],round(record['active_mean_abs_shift_ms'],2),round(record['mean_cosine_cost_unaligned'],3),round(record['mean_cosine_cost_aligned'],3),flush=True)
 (out/'status.json').write_text(json.dumps(dict(complete=False,records=records),ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(complete=True,records=records,mean_active_abs_shift_ms=float(np.mean([r['active_mean_abs_shift_ms'] for r in records])),mean_cosine_cost_unaligned=float(np.mean([r['mean_cosine_cost_unaligned'] for r in records])),mean_cosine_cost_aligned=float(np.mean([r['mean_cosine_cost_aligned'] for r in records])),seconds=time.monotonic()-begin,feature_model='existing frozen HuBERT first9 layers',frame_hop_seconds=.02,receptive_field_center_offset_seconds=.0125,band_frames=9,no_validation_or_test_training_pairs=True,audio_files_modified=False,not_proof_of_phoneme_gold_alignment=True,not_identity_or_quality_acceptance=True)
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('TIMING_AUDIT_DONE',report['mean_active_abs_shift_ms'],report['mean_cosine_cost_unaligned'],report['mean_cosine_cost_aligned'],flush=True)
