from run_rvc_pilot import settings
settings()
from fargan_feature_mapper_20261006 import PitchAwareMapper as FeatureMapper,pitch_aware_features as normalize_pitch,export_mapper
from pathlib import Path
import torch,numpy as np,json,time,subprocess,hashlib,soundfile as sf
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005'
out=budget/'fargan_mapper_pitchaware';out.mkdir(exist_ok=True);corpus=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'));assert corpus['complete']
torch.set_num_threads(4);torch.manual_seed(20261006);rng=np.random.default_rng(20261006);device='cuda'
data=[];all_inputs=[]
for row in [r for r in corpus['files'] if r['split']=='train']:
    raw=np.fromfile(row['source_features'],dtype=np.float32).reshape(-1,20);x=normalize_pitch(raw)
    y=np.fromfile(row['teacher_features'],dtype=np.float32).reshape(-1,20);y=np.pad(y,((0,max(0,len(x)-len(y))),(0,0)),mode='edge')[:len(x)].copy()
    y[:,0]=x[:,0];y[:,19]=x[:,19]
    all_inputs.append(x);data.append((torch.tensor(x,device=device),torch.tensor(y,device=device)))
anchors=[]
for row in corpus['target_training']:
    raw=np.fromfile(row['features'],dtype=np.float32).reshape(-1,20);x=normalize_pitch(raw);anchors.append(torch.tensor(x,device=device));all_inputs.append(x)
pooled=np.concatenate(all_inputs);mean=pooled.mean(axis=0);std=np.maximum(pooled.std(axis=0),.1)
parent=torch.load(budget/'fargan_mapper_v1/checkpoint_step1200.pt',map_location='cpu',weights_only=False)
mean[:20]=np.asarray(parent['mean']);std[:20]=np.asarray(parent['std'])
model=FeatureMapper(mean,std).to(device)
with torch.no_grad():
    state=model.state_dict()
    for name,value in parent['model'].items():
        if name in ['mean','std']:continue
        if name=='pre.weight':state[name][:,:20].copy_(value);state[name][:,20].zero_()
        else:state[name].copy_(value)
optimizer=torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=.0001)
length=160;warm=16;history=[];begin=time.monotonic();steps=3000
def crop(v):
    at=int(rng.integers(max(1,len(v)-length+1)));return v[at:at+length],at
print('FEATURE_MAPPER_READY',sum(p.numel() for p in model.parameters()),steps,flush=True)
for step in range(steps):
    xs=[];ys=[]
    for i in range(16):
        if i<12:
            x,y=data[int(rng.integers(len(data)))];xx,at=crop(x);yy=y[at:at+length]
        else:xx,_=crop(anchors[int(rng.integers(len(anchors)))]);yy=xx[:,:20].clone()
        xx=xx.clone();yy=yy.clone();gain=float(rng.uniform(-3,2));xx[:,0]+=gain;yy[:,0]=xx[:,0]
        xs.append(xx);ys.append(yy)
    x=torch.stack(xs);y=torch.stack(ys);pred,_=model(x);a=pred[:,warm:];b=y[:,warm:]
    active=(x[:,warm:,0]>-7).float()*.8+.2
    spectral=(torch.nn.functional.smooth_l1_loss((a[...,1:18]-b[...,1:18])/model.std[1:18],torch.zeros_like(a[...,1:18]),reduction='none').mean(-1)*active).mean()
    voiced=(x[:,warm:,19]>.05).float();pitch=(((a[...,18]-b[...,18])**2)*voiced).sum()/voiced.sum().clamp_min(1)
    temporal=(((a[:,1:,1:18]-a[:,:-1,1:18])-(b[:,1:,1:18]-b[:,:-1,1:18]))/model.std[1:18]).abs().mean()
    loss=spectral+2*pitch+.1*temporal;assert torch.isfinite(loss)
    optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step()
    for group in optimizer.param_groups:group['lr']=.002*(.1+.9*.5*(1+np.cos(np.pi*(step+1)/steps)))
    if step%100==0 or step==steps-1:
        r=dict(step=step+1,seconds=time.monotonic()-begin,loss=float(loss.detach()),spectral=float(spectral.detach()),pitch=float(pitch.detach()));history.append(r);print('MAPPER',json.dumps(r),flush=True)
        (out/'training_status.json').write_text(json.dumps(dict(complete=False,history=history),indent=2),encoding='utf-8')
model=model.cpu().eval();checkpoint=out/'checkpoint_step3000.pt';torch.save(dict(model=model.state_dict(),steps=steps,mean=mean.tolist(),std=std.tolist()),checkpoint)
meta=export_mapper(model,out/'fargan_mapper_pitchaware.f32');outputs=[]
for row in [r for r in corpus['files'] if r['split']=='validation']:
    raw=np.fromfile(row['source_features'],dtype=np.float32).reshape(-1,20);x=normalize_pitch(raw)
    with torch.inference_mode():y,_=model(torch.tensor(x)[None]);y=y[0].numpy()
    features=out/(Path(row['filename']).stem+'.converted.f32');y.astype('float32').tofile(features);pcm=out/(Path(row['filename']).stem+'.pcm')
    subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(features),str(pcm),str(out/(Path(row['filename']).stem+'.synthesis.json'))],check=True)
    wave=np.fromfile(pcm,dtype='<i2').astype('float32')/32768;path=out/(Path(row['filename']).stem+'_student.wav');sf.write(path,wave,16000,subtype='FLOAT');outputs.append(dict(row,student_path=str(path),converted_features=str(features),quality_accepted=False))
report=dict(complete=True,heldout_outputs=outputs,steps=steps,history=history,parameters=sum(p.numel() for p in model.parameters()),mapper_arrays=meta,mapper_sha256=hashlib.sha256((out/'fargan_mapper_pitchaware.f32').read_bytes()).hexdigest(),causal=True,source_enrollment=False,source_pitch_statistics='rolling151 voiced frames; no future utterance statistics',pitch_normalization_target_hz=193.13304493,source_raw_pitch_retained_as_network_feature=True,raw_waveform_bypass=False,energy_periodicity_from_live_input_features=True,recognizer_used_as_loss=False,auxiliary_speaker_loss_used=False,utmos_used_as_loss=False,vocoder_pretrained_official=True,vocoder_finetuned=False,target_track9_used=False,test_audio_used=False,quality_accepted=False,board_live_deployed=False)
(out/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('FEATURE_MAPPER_DONE',flush=True)
