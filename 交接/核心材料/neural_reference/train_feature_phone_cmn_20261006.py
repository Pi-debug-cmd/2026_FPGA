from run_rvc_pilot import settings
settings()
from fargan_feature_phone_cmn_20261006 import FeaturePhoneCMN,collapse
from pathlib import Path
import torch,numpy as np,json,time,hashlib

base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';out=budget/'fargan_phone_cmn';out.mkdir(exist_ok=True)
manifest=json.loads((budget/'fargan_phone_guidance/manifest.json').read_text(encoding='utf-8'));assert manifest['complete']
torch.set_num_threads(4);torch.manual_seed(20261006+251);rng=np.random.default_rng(20261006+251)
data=[];raws=[]
for row in manifest['files']:
    with np.load(row['posterior_path']) as d:truth=d['body_posteriors'].astype('float32')
    for path in [row['source_features']]+([row['teacher_features']] if row['kind']=='paired' else []):
        f=np.fromfile(path,dtype='float32').reshape(-1,20);n=min(len(f)//6,len(truth));f=f[:n*6]
        data.append((torch.tensor(f,device='cuda'),truth[:n]));raws.append(f)
all_raw=np.concatenate(raws);mean=all_raw.mean(0);std=np.maximum(all_raw.std(0),.1)
model=FeaturePhoneCMN(mean,std,manifest['body_classes']).cuda();optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.001)
ctc=torch.nn.CTCLoss(blank=0,reduction='mean',zero_infinity=False)
blocks=48;steps=10000;history=[];begin=time.monotonic();print('PHONE_CMN_READY',len(data),steps,flush=True)
for step in range(steps):
    xs=[];targets=[];lengths=[];target_lengths=[]
    for _ in range(16):
        f,y=data[int(rng.integers(len(data)))];at=int(rng.integers(max(1,len(y)-blocks+1)))
        truth=y[at:at+blocks];ids=collapse(truth.argmax(-1));n=len(truth)
        x=f[at*6:(at+n)*6].clone()
        # Constant channel variation discourages memorization of source voice.
        offsets=torch.randn(17,device='cuda')*model.std[1:18]*.2
        x[:,1:18]+=offsets
        x[:,0]+=float(rng.uniform(-2,1))
        if n<blocks:
            x=torch.nn.functional.pad(x,(0,0,0,6*(blocks-n)));x[n*6:,0]=-12;x[n*6:,19]=-.5
        xs.append(x);targets+=ids;target_lengths.append(len(ids));lengths.append(n)
    logits=model(torch.stack(xs));lp=logits.log_softmax(-1).transpose(0,1).contiguous()
    loss=ctc(lp,torch.tensor(targets,dtype=torch.int64,device='cuda'),torch.tensor(lengths,dtype=torch.int64),torch.tensor(target_lengths,dtype=torch.int64))
    assert torch.isfinite(loss);optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step()
    for g in optimizer.param_groups:g['lr']=.001*(.15+.85*.5*(1+np.cos(np.pi*(step+1)/steps)))
    if step%500==0 or step==steps-1:
        r=dict(step=step+1,seconds=time.monotonic()-begin,loss=float(loss.detach()));history.append(r);print('PHONE_CMN',json.dumps(r),flush=True)
        (out/'training_status.json').write_text(json.dumps(dict(complete=False,history=history),indent=2),encoding='utf-8')
checkpoint=out/'feature_phone_ctc_step10000.pt';torch.save(dict(model=model.cpu().eval().state_dict(),mean=mean.tolist(),std=std.tolist(),classes=manifest['body_classes'],steps=steps),checkpoint)
report=dict(complete=True,steps=steps,history=history,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),offline_only=True,not_deployed=True,
            source_pinyin_posterior_guidance=True,asr_no_longer_independent_after_guidance=True,test_audio_used=False,validation_audio_used=False,source_enrollment=False,
            frame_emission_alignment_not_prescribed=True,feature_channel_offset_augmentation=True)
(out/'training_decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('PHONE_CMN_DONE',flush=True)
