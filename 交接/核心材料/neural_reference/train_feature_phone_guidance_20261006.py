from run_rvc_pilot import settings
settings()
from fargan_feature_phone_model_20261006 import FeaturePhoneNet,posterior_loss
from pathlib import Path
import torch,numpy as np,json,time,hashlib

base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';out=budget/'fargan_phone_guidance'
manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'));assert manifest['complete']
torch.set_num_threads(4);torch.manual_seed(20261006+191);rng=np.random.default_rng(20261006+191)
data=[];raws=[]
for row in manifest['files']:
    with np.load(row['posterior_path']) as d:truth=d['body_posteriors'].astype('float32')
    for path in [row['source_features']]+([row['teacher_features']] if row['kind']=='paired' else []):
        f=np.fromfile(path,dtype='float32').reshape(-1,20);n=min(len(f)//6,len(truth));f=f[:n*6]
        data.append((torch.tensor(f,device='cuda'),torch.tensor(truth[:n],device='cuda')));raws.append(f[:,1:18])
all_raw=np.concatenate(raws);mean=all_raw.mean(0);std=np.maximum(all_raw.std(0),.1)
model=FeaturePhoneNet(mean,std,manifest['body_classes']).cuda();optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0003)
blocks=48;steps=3000;history=[];begin=time.monotonic();print('FEATURE_PHONE_READY',len(data),manifest['body_classes'],steps,flush=True)
for step in range(steps):
    xs=[];ys=[];masks=[]
    for _ in range(16):
        f,y=data[int(rng.integers(len(data)))];at=int(rng.integers(max(1,len(y)-blocks+1)));x=f[at*6:(at+blocks)*6];truth=y[at:at+blocks]
        n=len(truth);mask=torch.zeros(blocks,device='cuda');mask[:n]=1
        if n<blocks:
            x=torch.nn.functional.pad(x,(0,0,0,6*(blocks-n)));truth=torch.nn.functional.pad(truth,(0,0,0,blocks-n));truth[n:,0]=1
        xs.append(x);ys.append(truth);masks.append(mask)
    x,y,mask=torch.stack(xs),torch.stack(ys),torch.stack(masks)
    logits=model(x);loss=posterior_loss(logits,y,mask);assert torch.isfinite(loss)
    optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step()
    for g in optimizer.param_groups:g['lr']=.001*(.2+.8*.5*(1+np.cos(np.pi*(step+1)/steps)))
    if step%200==0 or step==steps-1:
        positive=(1-y[...,0]>.4)&(mask>0)
        accuracy=float((logits.argmax(-1)[positive]==y.argmax(-1)[positive]).float().mean()) if positive.any() else None
        r=dict(step=step+1,seconds=time.monotonic()-begin,loss=float(loss.detach()),positive_body_accuracy_training=accuracy);history.append(r);print('FEATURE_PHONE',json.dumps(r),flush=True)
        (out/'phone_training_status.json').write_text(json.dumps(dict(complete=False,history=history),indent=2),encoding='utf-8')
checkpoint=out/'feature_phone_step3000.pt';torch.save(dict(model=model.cpu().eval().state_dict(),mean=mean.tolist(),std=std.tolist(),classes=manifest['body_classes'],steps=steps),checkpoint)
report=dict(complete=True,steps=steps,history=history,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),offline_only=True,not_deployed=True,
            auxiliary_uses_bidirectional_context=True,does_not_add_future_context_to_deployed_mapper=True,
            source_pinyin_posterior_guidance=True,asr_no_longer_independent_after_guidance=True,test_audio_used=False,validation_audio_used=False,source_enrollment=False)
(out/'phone_training_decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('FEATURE_PHONE_DONE',flush=True)
