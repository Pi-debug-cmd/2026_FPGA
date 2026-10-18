"""Fixed4000-step V8 fine-tune, explicitly supervising pitch/voicing dynamics.
Same FMAP008 architecture and native runtime budget. No test or Track9 use.
No ASR/identity/perceptual gradients, no feature discriminator in this control.
"""
from run_rvc_pilot import settings
settings()
from fargan_mapper_v8_20261006 import MapperV8,pitch_aware_features
from fargan_feature_mapper_20261006 import export_mapper
from pathlib import Path
import torch,torch.nn.functional as F,numpy as np,json,time,subprocess,soundfile as sf,hashlib

base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005'
out=budget/'fargan_v8_dynamics';out.mkdir(exist_ok=True)
corpus=json.loads((budget/'fargan_corpus_expanded/manifest.json').read_text(encoding='utf-8'))
parent=budget/'fargan_mapper_expanded_v8/checkpoint_step5000.pt'
cp=torch.load(parent,map_location='cpu',weights_only=False)
model=MapperV8(cp['mean'],cp['std']);model.load_state_dict(cp['model']);model=model.cuda()
torch.set_num_threads(4);torch.manual_seed(20261006+139);rng=np.random.default_rng(20261006+139)
data=[];anchors=[]
for row in [r for r in corpus['files'] if r['split']=='train']:
    raw=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20)
    x=pitch_aware_features(raw);y=np.fromfile(row['teacher_features'],dtype='float32').reshape(-1,20)
    y=np.pad(y,((0,max(0,len(x)-len(y))),(0,0)),mode='edge')[:len(x)].copy();y[:,0]=x[:,0]
    data.append((torch.tensor(x,device='cuda'),torch.tensor(y,device='cuda')))
for row in corpus['target_training']:
    y=np.fromfile(row['features'],dtype='float32').reshape(-1,20);x=pitch_aware_features(y)
    anchors.append((torch.tensor(x,device='cuda'),torch.tensor(y,device='cuda')))
length=400;warm=16;steps=4000;history=[];start=time.monotonic()
optimizer=torch.optim.AdamW(model.parameters(),lr=.0002,weight_decay=.0001)

def crop(pair):
    x,y=pair;at=int(rng.integers(max(1,len(x)-length+1)));x=x[at:at+length].clone();y=y[at:at+length].clone()
    n=len(x);mask=torch.zeros(length,device='cuda');mask[:n]=1
    if n<length:
        x=F.pad(x,(0,0,0,length-n));y=F.pad(y,(0,0,0,length-n));x[n:,0]=-12;y[n:,0]=-12;x[n:,19]=y[n:,19]=-.5
    gain=float(rng.uniform(-3,2));x[:n,0]+=gain;y[:n,0]=x[:n,0]
    return x,y,mask

def average(values,mask): return (values*mask).sum()/mask.sum().clamp_min(1)
print('DYNAMICS_READY',len(data),steps,flush=True)
for step in range(steps):
    cropped=[crop(data[int(rng.integers(len(data)))] if i<13 else anchors[int(rng.integers(len(anchors)))]) for i in range(16)]
    x,y,mask=(torch.stack([r[i] for r in cropped]) for i in range(3))
    prediction,_=model(x);a=prediction[:,warm:];b=y[:,warm:];m=mask[:,warm:]
    active=m*((x[:,warm:,0]>-7).float()*.8+.2)
    spectral=average(F.smooth_l1_loss((a[...,1:18]-b[...,1:18])/model.std[1:18],torch.zeros_like(a[...,1:18]),reduction='none').mean(-1),active)
    voiced=m*(x[:,warm:,0]>-7).float()*(b[...,19]>.1).float()
    pitch=average((a[...,18]-b[...,18]).square(),voiced)
    periodicity=average((a[...,19]-b[...,19]).square(),active)
    pairs=active[:,1:]*active[:,:-1]
    temporal=average((((a[:,1:,1:18]-a[:,:-1,1:18])-(b[:,1:,1:18]-b[:,:-1,1:18]))/model.std[1:18]).abs().mean(-1),pairs)
    voiced_pairs=voiced[:,1:]*voiced[:,:-1]
    da=a[:,1:,18]-a[:,:-1,18];db=b[:,1:,18]-b[:,:-1,18]
    pitch_delta=average((da-db).square(),voiced_pairs)
    pitch_accel=average(((da[:,1:]-da[:,:-1])-(db[:,1:]-db[:,:-1])).square(),voiced_pairs[:,1:]*voiced_pairs[:,:-1])
    voice_delta=average(((a[:,1:,19]-a[:,:-1,19])-(b[:,1:,19]-b[:,:-1,19])).square(),pairs)
    loss=3*spectral+3*pitch+3*periodicity+temporal+8*pitch_delta+4*pitch_accel+3*voice_delta
    assert torch.isfinite(loss);optimizer.zero_grad(set_to_none=True);loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),1);assert torch.isfinite(grad);optimizer.step()
    for group in optimizer.param_groups:group['lr']=.0002*(.15+.85*.5*(1+np.cos(np.pi*(step+1)/steps)))
    if step%200==0 or step==steps-1:
        r=dict(step=step+1,seconds=time.monotonic()-start,loss=float(loss.detach()),spectral=float(spectral.detach()),pitch=float(pitch.detach()),periodicity=float(periodicity.detach()),pitch_delta=float(pitch_delta.detach()),pitch_accel=float(pitch_accel.detach()),voice_delta=float(voice_delta.detach()),temporal=float(temporal.detach()))
        history.append(r);print('DYNAMICS',json.dumps(r),flush=True)
        (out/'training_status.json').write_text(json.dumps(dict(complete=False,history=history),indent=2),encoding='utf-8')
model=model.cpu().eval();torch.save(dict(model=model.state_dict(),steps=steps,mean=cp['mean'],std=cp['std']),out/'checkpoint_step4000.pt')
weight=out/'fargan_v8_dynamics.f32';meta=export_mapper(model,weight);outputs=[]
for row in [r for r in corpus['files'] if r['split']=='validation']:
    raw=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20);x=pitch_aware_features(raw)
    with torch.inference_mode():y,_=model(torch.tensor(x)[None]);y=y[0].numpy()
    stem=Path(row['filename']).stem;features=out/(stem+'.converted.f32');pcm=out/(stem+'.pcm');y.astype('float32').tofile(features)
    subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(features),str(pcm),str(out/(stem+'.synthesis.json'))],check=True)
    wave=np.fromfile(pcm,dtype='<i2').astype('float32')/32768;path=out/(stem+'_student.wav');sf.write(path,wave,16000,subtype='FLOAT');outputs.append(dict(row,student_path=str(path)))
report=dict(complete=True,heldout_outputs=outputs,history=history,steps=steps,parameters=sum(p.numel() for p in model.parameters()),mapper_arrays=meta,mapper_sha256=hashlib.sha256(weight.read_bytes()).hexdigest(),parent_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),causal=True,source_enrollment=False,raw_waveform_mix=False,recognizer_used_as_loss=False,auxiliary_speaker_loss_used=False,feature_adversary_used_offline=False,test_audio_used=False,target_track9_used=False,quality_accepted=False,board_live_deployed=False,training_frames=length,warmup_frames=warm,actual_int8_c_validation=True)
(out/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('DYNAMICS_DONE',flush=True)
