"""Expanded20-speaker paired training. Fixed5000 endpoint, native C eval later.
Feature adversary is offline only, never part of board inference.
"""
from run_rvc_pilot import settings
settings()
from fargan_mapper_v8_20261006 import MapperV8,ConditionalFeatureDisc,pitch_aware_features
from fargan_feature_mapper_20261006 import export_mapper
from pathlib import Path
import torch,torch.nn.functional as F,numpy as np,json,time,subprocess,hashlib,soundfile as sf
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005';out=budget/'fargan_mapper_expanded_v8';out.mkdir(exist_ok=True)
corpus=json.loads((budget/'fargan_corpus_expanded/manifest.json').read_text(encoding='utf-8'));assert corpus['complete']
torch.set_num_threads(4);torch.manual_seed(20261006+87);rng=np.random.default_rng(20261006+87);device='cuda';data=[];anchors=[];inputs=[];truths=[]
for row in [r for r in corpus['files'] if r['split']=='train']:
    raw=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20);x=pitch_aware_features(raw)
    y=np.fromfile(row['teacher_features'],dtype='float32').reshape(-1,20);y=np.pad(y,((0,max(0,len(x)-len(y))),(0,0)),mode='edge')[:len(x)].copy();y[:,0]=x[:,0]
    data.append((torch.tensor(x,device=device),torch.tensor(y,device=device)));inputs.append(x);truths.append(y)
for row in corpus['target_training']:
    y=np.fromfile(row['features'],dtype='float32').reshape(-1,20);x=pitch_aware_features(y);anchors.append((torch.tensor(x,device=device),torch.tensor(y,device=device)));inputs.append(x);truths.append(y)
mean=np.concatenate(inputs).mean(0);std=np.maximum(np.concatenate(inputs).std(0),.1);target_mean=torch.tensor(np.concatenate(truths).mean(0)[1:20],device=device);target_std=torch.tensor(np.maximum(np.concatenate(truths).std(0)[1:20],.1),device=device)
model=MapperV8(mean,std).to(device);disc=ConditionalFeatureDisc().to(device);go=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001);do=torch.optim.AdamW(disc.parameters(),lr=.0002,weight_decay=.0001)
length=200;warm=32;steps=5000;history=[];start=time.monotonic();print('EXPANDED_V8_READY',len(data),sum(p.numel() for p in model.parameters()),steps,flush=True)
def crop(x,y):
    at=int(rng.integers(max(1,len(x)-length+1)));return x[at:at+length],y[at:at+length]
for step in range(steps):
    xs=[];ys=[]
    for i in range(16):
        pair=data[int(rng.integers(len(data)))] if i<13 else anchors[int(rng.integers(len(anchors)))];x,y=crop(*pair);x=x.clone();y=y.clone();gain=float(rng.uniform(-3,2));x[:,0]+=gain;y[:,0]=x[:,0];xs.append(x);ys.append(y)
    x=torch.stack(xs);y=torch.stack(ys);pred,_=model(x);a=pred[:,warm:];b=y[:,warm:];condition=(x[:,warm:,1:]-model.mean[1:])/model.std[1:]
    real=(b[...,1:20]-target_mean)/target_std;fake=(a[...,1:20]-target_mean)/target_std;adversarial=step>=1000
    if adversarial:
        for p in disc.parameters():p.requires_grad_(True)
        do.zero_grad(set_to_none=True);rs,_=disc(condition,real);fs,_=disc(condition,fake.detach());dl=((rs-1)**2).mean()+fs.square().mean();dl.backward();torch.nn.utils.clip_grad_norm_(disc.parameters(),5);do.step()
    for p in disc.parameters():p.requires_grad_(False)
    active=(x[:,warm:,0]>-7).float()*.8+.2
    spectral=(F.smooth_l1_loss((a[...,1:18]-b[...,1:18])/model.std[1:18],torch.zeros_like(a[...,1:18]),reduction='none').mean(-1)*active).mean()
    voiced=(x[:,warm:,19]>.05).float();pitch=(((a[...,18]-b[...,18])**2)*voiced).sum()/voiced.sum().clamp_min(1)
    periodicity=((a[...,19]-b[...,19])**2*active).mean()
    temporal=(((a[:,1:,1:18]-a[:,:-1,1:18])-(b[:,1:,1:18]-b[:,:-1,1:18]))/model.std[1:18]).abs().mean()
    adv=a.sum()*0;fm=adv
    if adversarial:
        score,maps=disc(condition,fake);adv=((score-1)**2).mean()
        with torch.no_grad():_,truth=disc(condition,real)
        fm=sum(F.l1_loss(u,v) for u,v in zip(maps,truth))/len(maps)
    loss=2*spectral+2*pitch+2*periodicity+.15*temporal+(.05*adv+.2*fm if adversarial else 0)
    assert torch.isfinite(loss);go.zero_grad(set_to_none=True);loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),1);assert torch.isfinite(grad);go.step()
    for group in go.param_groups:group['lr']=.001*(.15+.85*.5*(1+np.cos(np.pi*(step+1)/steps)))
    if step%100==0 or step==steps-1:
        r=dict(step=step+1,seconds=time.monotonic()-start,loss=float(loss.detach()),spectral=float(spectral.detach()),pitch=float(pitch.detach()),periodicity=float(periodicity.detach()),adversarial=float(adv.detach()),feature_matching=float(fm.detach()));history.append(r);print('EXPANDED_V8',json.dumps(r),flush=True);(out/'training_status.json').write_text(json.dumps(dict(complete=False,history=history),indent=2),encoding='utf-8')
model=model.cpu().eval();torch.save(dict(model=model.state_dict(),steps=steps,mean=mean.tolist(),std=std.tolist()),out/'checkpoint_step5000.pt');meta=export_mapper(model,out/'fargan_mapper_expanded_v8.f32')
outputs=[]
for row in [r for r in corpus['files'] if r['split']=='validation']:
    raw=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20);x=pitch_aware_features(raw)
    with torch.inference_mode():y,_=model(torch.tensor(x)[None]);y=y[0].numpy()
    stem=Path(row['filename']).stem;features=out/(stem+'.converted.f32');pcm=out/(stem+'.pcm');y.astype('float32').tofile(features)
    subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(features),str(pcm),str(out/(stem+'.synthesis.json'))],check=True)
    wave=np.fromfile(pcm,dtype='<i2').astype('float32')/32768;path=out/(stem+'_student.wav');sf.write(path,wave,16000,subtype='FLOAT');outputs.append(dict(row,student_path=str(path)))
report=dict(complete=True,heldout_outputs=outputs,history=history,steps=steps,training_speakers=corpus['expanded_train_speakers'],training_seconds=corpus['expanded_train_seconds'],parameters=sum(p.numel() for p in model.parameters()),mapper_arrays=meta,mapper_sha256=hashlib.sha256((out/'fargan_mapper_expanded_v8.f32').read_bytes()).hexdigest(),causal=True,source_enrollment=False,raw_waveform_mix=False,target_pitch_from_first_frame=True,periodicity_learned=True,recognizer_used_as_loss=False,auxiliary_speaker_loss_used=False,feature_adversary_used_offline=True,test_audio_used=False,target_track9_used=False,quality_accepted=False,board_live_deployed=False,actual_int8_c_validation=True,board_throughput_verified=False)
(out/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('EXPANDED_V8_DONE',flush=True)
