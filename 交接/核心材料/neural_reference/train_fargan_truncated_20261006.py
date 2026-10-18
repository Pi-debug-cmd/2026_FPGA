"""Fixed240-step causal mapper fine-tune through frozen FARGAN surrogate.
Native int8 vocoder renders validation; no test selection or source enrollment.
"""
from run_rvc_pilot import settings
settings()
from fargan_feature_mapper_20261006 import FeatureMapper,normalize_pitch,export_mapper
from differentiable_fargan_20261006 import FrozenFargan
from differentiable_speaker_20261005 import FrozenSpeaker
from differentiable_chinese_ctc_20261005 import FrozenChineseCTC
from run_sensevoice_pinyin_validation_20261004 import load_frontend
from train_board_student_20261005 import read,Objective
from pathlib import Path
import torch,torch.nn.functional as F,numpy as np,json,time,subprocess,soundfile as sf,hashlib
BASE=Path(__file__).resolve().parent;budget=BASE.parent/'board_budget_20261005';native=BASE.parent/'board_support/native_llvc_20261005'
OUT=budget/'fargan_mapper_truncated';OUT.mkdir(exist_ok=True)
torch.set_num_threads(4);torch.manual_seed(20261006+53);rng=np.random.default_rng(20261006+53);device='cuda'
manifest=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'))
parent=budget/'fargan_mapper_v1/checkpoint_step1200.pt';checkpoint=torch.load(parent,map_location='cpu',weights_only=False)
model=FeatureMapper(checkpoint['mean'],checkpoint['std']);model.load_state_dict(checkpoint['model'],strict=True);model=model.cuda()
data=[];anchors=[]
for row in [r for r in manifest['files'] if r['split']=='train']:
    x=normalize_pitch(np.fromfile(row['source_features'],dtype='float32').reshape(-1,20))
    y=np.fromfile(row['teacher_features'],dtype='float32').reshape(-1,20);y=np.pad(y,((0,max(0,len(x)-len(y))),(0,0)),mode='edge')[:len(x)].copy()
    y[:,0]=x[:,0];y[:,19]=x[:,19]
    waves=[]
    for name in ['path','teacher_path']:
        w=read(row[name]);w=np.pad(w,(0,max(0,len(x)*160-len(w))))[:len(x)*160];waves.append(torch.tensor(w,device=device))
    data.append((torch.tensor(x,device=device),torch.tensor(y,device=device),*waves))
for row in manifest['target_training']:
    raw=np.fromfile(row['features'],dtype='float32').reshape(-1,20);x=normalize_pitch(raw);y=raw.copy();y[:,18]=x[:,18]
    w=read(row['path']);w=np.pad(w,(0,max(0,len(x)*160-len(w))))[:len(x)*160]
    anchors.append((torch.tensor(x,device=device),torch.tensor(y,device=device),torch.tensor(w,device=device)))
vocoder=FrozenFargan(truncate_frames=8).cuda().eval();speaker=FrozenSpeaker().cuda().eval();content=FrozenChineseCTC().cuda().eval();frontend=load_frontend().cuda().eval()
with torch.no_grad():reference=speaker.embedding(torch.tensor(read('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav'),device=device))
objective=Objective(device);ctc=torch.nn.CTCLoss(blank=0,reduction='mean',zero_infinity=False)
optimizer=torch.optim.AdamW(model.parameters(),lr=.0001,weight_decay=.0001)
frames=140;warm=16;steps=240;history=[];start=time.monotonic()
def logits(w):
    w=w/w.abs().amax(-1,keepdim=True).detach().clamp_min(1e-7)
    f,l=frontend(w,torch.full((len(w),),w.shape[-1],dtype=torch.int64));_,p,n=content(f,l);return p,n
def content_loss(fake,source):
    with torch.no_grad():
        lp,n=logits(source);last=0;ids=[]
        for k in lp[:int(n[0]),0].argmax(-1).tolist():
            if k and k!=last:ids.append(k)
            last=k
    if not ids:return fake.sum()*0
    pred,pn=logits(fake)
    return ctc(pred,torch.tensor(ids,device=device),pn.cpu().long(),torch.tensor([len(ids)]))
def normalized(w):return w*(.06/w.square().mean(-1,keepdim=True).sqrt().detach().clamp_min(.001))
print('FARGAN_PERCEPTUAL_READY',steps,flush=True)
for step in range(steps):
    x,y,source,teacher=data[int(rng.integers(len(data)))];at=int(rng.integers(max(1,len(x)-frames+1)))
    xx=x[at:at+frames][None];yy=y[at:at+frames][None];src=source[at*160:(at+frames)*160][None];truth=teacher[at*160:(at+frames)*160][None]
    if step%5==4:
        x,y,w=anchors[int(rng.integers(len(anchors)))];at=int(rng.integers(max(1,len(x)-frames+1)))
        xx=x[at:at+frames][None];yy=y[at:at+frames][None];src=w[at*160:(at+frames)*160][None];truth=src
    prediction,_=model(xx);a=prediction[:,warm:];b=yy[:,warm:]
    feature=F.smooth_l1_loss((a[...,1:18]-b[...,1:18])/model.std[1:18],torch.zeros_like(a[...,1:18]))
    voiced=(xx[:,warm:,19]>.05).float();pitch=(((a[...,18]-b[...,18])**2)*voiced).sum()/voiced.sum().clamp_min(1)
    wave=vocoder(prediction)[:,warm*160:];truth=truth[:,warm*160:];src=src[:,warm*160:]
    spectral=objective.loss(normalized(wave),normalized(truth))
    identity=1-(speaker.embedding(wave)*reference).sum(-1).mean()
    cl=content_loss(wave,src) if step%4==0 else wave.sum()*0
    loss=feature+2*pitch+2*spectral+2*identity+2*cl
    assert torch.isfinite(loss);optimizer.zero_grad(set_to_none=True);loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),1);assert torch.isfinite(grad);optimizer.step()
    for group in optimizer.param_groups:group['lr']=.0001*(.2+.8*.5*(1+np.cos(np.pi*(step+1)/steps)))
    if step%10==0 or step==steps-1:
        r=dict(step=step+1,seconds=time.monotonic()-start,loss=float(loss.detach()),spectral=float(spectral.detach()),feature=float(feature.detach()),pitch=float(pitch.detach()),identity=float(identity.detach()),ctc=float(cl.detach()),grad=float(grad),gpu_peak_bytes=torch.cuda.max_memory_allocated());history.append(r);print('PERCEPTUAL',json.dumps(r),flush=True)
        (OUT/'training_status.json').write_text(json.dumps(dict(complete=False,history=history),indent=2),encoding='utf-8')
model=model.cpu().eval();torch.save(dict(model=model.state_dict(),steps=steps,mean=checkpoint['mean'],std=checkpoint['std']),OUT/'checkpoint_step240.pt')
meta=export_mapper(model,OUT/'fargan_mapper_truncated.f32');outputs=[]
for row in [r for r in manifest['files'] if r['split']=='validation']:
    raw=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20);x=normalize_pitch(raw)
    with torch.inference_mode():y,_=model(torch.tensor(x)[None]);y=y[0].numpy()
    features=OUT/(Path(row['filename']).stem+'.converted.f32');y.astype('float32').tofile(features);pcm=OUT/(Path(row['filename']).stem+'.pcm')
    subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(features),str(pcm),str(OUT/(Path(row['filename']).stem+'.synthesis.json'))],check=True)
    w=np.fromfile(pcm,dtype='<i2').astype('float32')/32768;path=OUT/(Path(row['filename']).stem+'_student.wav');sf.write(path,w,16000,subtype='FLOAT');outputs.append(dict(row,student_path=str(path)))
report=dict(complete=True,heldout_outputs=outputs,history=history,steps=steps,causal_mapper=True,source_enrollment=False,raw_waveform_mix=False,recognizer_used_as_loss=True,auxiliary_speaker_loss_used=True,utmos_used_as_loss=False,vocoder_pretrained_official=True,vocoder_finetuned=False,target_track9_used=False,test_audio_used=False,quality_accepted=False,board_live_deployed=False,mapper_arrays=meta,parent_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),mapper_sha256=hashlib.sha256((OUT/'fargan_mapper_truncated.f32').read_bytes()).hexdigest(),training_gradient_truncation_frames=8,training_vocoder_surrogate_not_bit_exact=True,validation_vocoder='actual quantized native C')
(OUT/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('FARGAN_PERCEPTUAL_DONE',flush=True)
