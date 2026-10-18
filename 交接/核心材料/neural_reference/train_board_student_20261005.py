"""Board-budget target student pilot: content + spectral + adversarial losses.

This is a bounded experiment, not target-quality acceptance. Validation/test
speakers never update weights; test audio is not used for checkpoint selection.
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys,json,time,argparse
BASE=Path(__file__).resolve().parent
NATIVE=BASE.parent/'board_support/native_llvc_20261005'
sys.path.insert(0,str(NATIVE))
from prepare_small_geometry import build_small,export,stream
import torch,numpy as np,soundfile as sf
import torch.nn as nn
import torch.nn.functional as F
import torchaudio.functional as AF
from transformers import HubertModel
from scipy.signal import resample_poly
from math import gcd
CORPUS=BASE.parent/'board_budget_20261005/student_corpus'
OUT=BASE.parent/'board_budget_20261005/small96_training'
OUT.mkdir(parents=True,exist_ok=True)

class PeriodDiscriminator(nn.Module):
    def __init__(self,period):
        super().__init__();self.period=period
        widths=[1,16,32,64,128]
        self.layers=nn.ModuleList([nn.utils.weight_norm(nn.Conv2d(widths[i],widths[i+1],(5,1),(3,1),padding=(2,0))) for i in range(4)])
        self.last=nn.utils.weight_norm(nn.Conv2d(128,1,(3,1),padding=(1,0)))
    def forward(self,x):
        b,c,n=x.shape
        if n%self.period:x=F.pad(x,(0,self.period-n%self.period),mode='reflect')
        x=x.reshape(b,c,-1,self.period);features=[]
        for layer in self.layers:x=F.leaky_relu(layer(x),.1);features.append(x)
        x=self.last(x);return x.flatten(1),features

class Objective:
    def __init__(self,device):
        self.windows={n:torch.hann_window(n,device=device) for n in [256,512,1024]}
        self.fb={n:AF.melscale_fbanks(n//2+1,30,7800,80,16000,norm='slaney',mel_scale='slaney').to(device) for n in self.windows}
    def loss(self,x,y):
        total=0
        for n,window in self.windows.items():
            a=torch.stft(x,n_fft=n,hop_length=160,window=window,return_complex=True).abs().clamp_min(1e-6)
            b=torch.stft(y,n_fft=n,hop_length=160,window=window,return_complex=True).abs().clamp_min(1e-6)
            mel_a=(a.transpose(1,2).square()@self.fb[n]).clamp_min(1e-8).log()
            mel_b=(b.transpose(1,2).square()@self.fb[n]).clamp_min(1e-8).log()
            total+=F.l1_loss(mel_a,mel_b)+.5*F.l1_loss(a.log(),b.log())+.5*(a-b).norm()/b.norm().clamp_min(1e-6)
        return total/len(self.windows)

def read(path):
    x,sr=sf.read(path,dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
    if sr!=16000:x=resample_poly(x,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
    return x

def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--steps',type=int,default=2400)
    parser.add_argument('--resume');parser.add_argument('--outname',default='small96_training')
    parser.add_argument('--speaker-loss',action='store_true');args=parser.parse_args()
    assert args.outname in ['small96_training','small96_identity_training']
    OUT=BASE.parent/'board_budget_20261005'/args.outname;OUT.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(20261005);rng=np.random.default_rng(20261005);torch.set_num_threads(4)
    device='cuda';assert torch.cuda.is_available()
    doc=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'));assert doc['complete']
    rows=doc['files'];train_rows=[r for r in rows if r['split']=='train']
    assert not({r['speaker'] for r in train_rows}&{r['speaker'] for r in rows if r['split']!='train'})
    data=[]
    for row in train_rows:
        x=read(row['path']);y=read(row['teacher_path'])
        # Codec tokenization changes only the final partial20ms frame count.
        # End trim/pad is recorded; no time warp or oracle text alignment.
        if abs(len(y)-len(x))>1600:raise ValueError('teacher duration differs by >100ms: '+row['filename'])
        y=np.pad(y,(0,max(0,len(x)-len(y))))[:len(x)]
        data.append((torch.tensor(x,device=device),torch.tensor(y,device=device)))
    model,cfg,selection=build_small(96)
    if args.resume:model.load_state_dict(torch.load(args.resume,map_location='cpu',weights_only=True)['model'],strict=True)
    model=model.to(device).eval()
    content=HubertModel.from_pretrained(str(BASE/'RVC/assets/hubert_base'),local_files_only=True).to(device).eval()
    content.encoder.layers=nn.ModuleList(content.encoder.layers[:9])
    for p in content.parameters():p.requires_grad_(False)
    discs=nn.ModuleList([PeriodDiscriminator(p) for p in [2,3,5]]).to(device)
    objective=Objective(device)
    speaker=None;reference=None
    if args.speaker_loss:
        from differentiable_speaker_20261005 import FrozenSpeaker
        speaker=FrozenSpeaker().to(device).eval()
        with torch.no_grad():
            reference=speaker.embedding(torch.tensor(read('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav'),device=device))
    go=torch.optim.AdamW(model.parameters(),lr=1e-4 if args.resume else 2e-4,betas=(.8,.99),weight_decay=0)
    do=torch.optim.AdamW(discs.parameters(),lr=1e-4,betas=(.8,.99),weight_decay=0)
    gs=torch.amp.GradScaler('cuda',enabled=False);ds=torch.amp.GradScaler('cuda',enabled=False)
    start=time.perf_counter();history=[];length=208*154;warm=8192
    print('TRAIN_READY',len(data),sum(p.numel() for p in model.parameters()),flush=True)
    for step in range(args.steps):
        xs=[];ys=[]
        for _ in range(2):
            x,y=data[int(rng.integers(len(data)))];offset=int(rng.integers(max(1,len(x)-length+1)))
            xx=x[offset:offset+length];yy=y[offset:offset+length]
            xx=F.pad(xx,(0,max(0,length-len(xx))));yy=F.pad(yy,(0,max(0,length-len(yy))))
            xs.append(xx*float(np.exp(rng.uniform(np.log(.35),np.log(1.35)))));ys.append(yy)
        source=torch.stack(xs);target=torch.stack(ys)
        with torch.autocast('cuda',enabled=False):pred=model(source[:,None])[:,0]
        pred=pred.float();assert torch.isfinite(pred).all()
        fake=pred[:,warm:];real=target[:,warm:];speech=source[:,warm:]
        adversarial=step>=400
        if adversarial:
            for p in discs.parameters():p.requires_grad_(True)
            do.zero_grad(set_to_none=True)
            with torch.autocast('cuda',enabled=False):
                dl=0
                for disc in discs:
                    dr,_=disc(real[:,None]);df,_=disc(fake.detach()[:,None]);dl+=((dr.float()-1)**2).mean()+df.float().square().mean()
            ds.scale(dl).backward();ds.unscale_(do);torch.nn.utils.clip_grad_norm_(discs.parameters(),5);ds.step(do);ds.update()
        for p in discs.parameters():p.requires_grad_(False)
        go.zero_grad(set_to_none=True);spectral=objective.loss(fake,real)
        # The frozen ContentVec/HuBERT features constrain spoken content, while
        # target teacher spectra/discriminators constrain tone and naturalness.
        with torch.autocast('cuda',enabled=False):
            with torch.no_grad():ref=content(F.layer_norm(speech,speech.shape[-1:])).last_hidden_state
            features=content(F.layer_norm(fake,fake.shape[-1:])).last_hidden_state
            cl=F.l1_loss(features.float(),ref.float());gl=torch.tensor(0.,device=device);fm=torch.tensor(0.,device=device)
            if adversarial:
                for disc in discs:
                    score,maps=disc(fake[:,None]);gl+=((score.float()-1)**2).mean()
                    with torch.no_grad():_,truth=disc(real[:,None])
                    fm+=sum(F.l1_loss(a.float(),b.float()) for a,b in zip(maps,truth))/len(maps)
        identity=torch.tensor(0.,device=device)
        if speaker is not None:identity=1-(speaker.embedding(fake)*reference).sum(dim=-1).mean()
        loss=5*spectral+(6 if args.resume else 2)*cl+3*identity+(.5*gl+2*fm if adversarial else 0)
        assert torch.isfinite(loss)
        gs.scale(loss).backward();gs.unscale_(go);grad=torch.nn.utils.clip_grad_norm_(model.parameters(),5.)
        assert torch.isfinite(grad);gs.step(go);gs.update()
        if step%50==0 or step==args.steps-1:
            row=dict(step=step+1,loss=float(loss.detach()),spectral=float(spectral.detach()),content=float(cl.detach()),
                     adversarial=float(gl.detach()),feature_matching=float(fm.detach()),identity=float(identity.detach()),seconds=time.perf_counter()-start,
                     rms=float(fake.detach().square().mean().sqrt()),peak=float(fake.detach().abs().max()))
            history.append(row);print('STEP',json.dumps(row),flush=True)
            (OUT/'training_status.json').write_text(json.dumps(dict(history=history,complete=False),indent=2),encoding='utf-8')
        if (step+1)%400==0 or step==args.steps-1:
            checkpoint=OUT/('checkpoint_step'+str(step+1)+'.pt')
            torch.save(dict(model={k:v.detach().cpu() for k,v in model.state_dict().items()},config=cfg,steps=step+1,
                            selection=selection,source_enrollment=False,target_quality_accepted=False),checkpoint)
    # Fixed final checkpoint, no test-set search; save actual stream outputs.
    model=model.cpu().float().eval();export(model,OUT/'small96_trained.f32')
    outputs=[]
    for row in [r for r in rows if r['split']!='train']:
        x=read(row['path']);y=stream(model,x);path=OUT/(row['filename'][:-4]+'_student.wav')
        sf.write(path,y,16000,subtype='FLOAT');outputs.append(dict(row,student_path=str(path),rms=float(np.sqrt(np.mean(y*y))),peak=float(np.max(np.abs(y))),human_acceptance=False))
    report=dict(history=history,complete=True,steps=args.steps,config=cfg,parameters=sum(p.numel() for p in model.parameters()),
                training_speakers=sorted({r['speaker'] for r in train_rows}),heldout_outputs=outputs,
                max_cuda_allocated=torch.cuda.max_memory_allocated(),source_enrollment=False,teacher_waveform_time_warp=False,
                target_track9_used_for_training=False,speech_quality_accepted=False,board_live_verified=False,
                resume_path=args.resume,auxiliary_speaker_loss_used=args.speaker_loss,
                wespeaker_no_longer_independent_evaluator=args.speaker_loss,
                previous_test_speakers_now_diagnostic_only=bool(args.resume),
                content_network='Frozen existing ContentVec/HuBERT first9layers, source feature loss; offline training only',
                waveform_delay_and_pronunciation_not_automatically_accepted=True)
    (OUT/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('TRAINING_AND_HELDOUT_STREAM_DONE',flush=True)
if __name__=='__main__':main()
