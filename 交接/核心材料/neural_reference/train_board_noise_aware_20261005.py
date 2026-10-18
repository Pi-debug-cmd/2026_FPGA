"""Same 173456-parameter board geometry; balanced low-SNR robustness and content repair.

Only prior training speakers update weights. Synthetic non-speech has zero
target; held-out audio remains diagnostic. No user audio or source enrollment.
"""
from train_board_student_20261005 import BASE,CORPUS,build_small,export,stream,read,Objective,PeriodDiscriminator
from pathlib import Path
import json,time,hashlib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import soundfile as sf
from transformers import HubertModel
from differentiable_speaker_20261005 import FrozenSpeaker

OUT=BASE.parent/'board_budget_20261005/small96_noise_aware'
PARENT=BASE.parent/'board_budget_20261005/small96_noise_refinement/checkpoint_step1200.pt'
STEPS=1200

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(20261005+11);rng=np.random.default_rng(20261005+11);torch.set_num_threads(4)
    device='cuda';assert torch.cuda.is_available()
    doc=json.loads((CORPUS/'paired_manifest.json').read_text(encoding='utf-8'));assert doc['complete']
    rows=doc['files'];training=[r for r in rows if r['split']=='train']
    assert not ({r['speaker'] for r in training}&{r['speaker'] for r in rows if r['split']!='train'})
    data=[]
    for row in training:
        x=read(row['path']);y=read(row['teacher_path'])
        assert abs(len(x)-len(y))<=1600
        y=np.pad(y,(0,max(0,len(x)-len(y))))[:len(x)]
        data.append((torch.tensor(x,device=device),torch.tensor(y,device=device)))
    model,cfg,selection=build_small(96)
    parent=torch.load(PARENT,map_location='cpu',weights_only=True)
    model.load_state_dict(parent['model'],strict=True);model=model.to(device).eval()
    assert sum(p.numel() for p in model.parameters())==173456
    content=HubertModel.from_pretrained(str(BASE/'RVC/assets/hubert_base'),local_files_only=True).to(device).eval()
    content.encoder.layers=nn.ModuleList(content.encoder.layers[:9])
    for p in content.parameters():p.requires_grad_(False)
    speaker=FrozenSpeaker().to(device).eval()
    with torch.no_grad():reference=speaker.embedding(torch.tensor(read('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav'),device=device))
    objective=Objective(device)
    discs=nn.ModuleList([PeriodDiscriminator(p) for p in [2,3,5]]).to(device)
    go=torch.optim.AdamW(model.parameters(),lr=5e-5,betas=(.8,.99),weight_decay=0)
    do=torch.optim.AdamW(discs.parameters(),lr=1e-4,betas=(.8,.99),weight_decay=0)
    length=208*154;warm=8192;timeline=torch.arange(length,device=device)/16000
    def noise(rms,kind):
        if kind==0:x=torch.zeros(length,device=device)
        elif kind==1:x=torch.randn(length,device=device)
        elif kind==2:
            z=torch.randn(length//int(rng.choice([4,8,16,32]))+1,device=device)
            x=F.interpolate(z[None,None],size=length,mode='linear',align_corners=False)[0,0]
        elif kind==3:
            hz=float(rng.choice([50,60,16000/208]));phase=float(rng.uniform(0,6.283))
            x=sum((1/k)*torch.sin(2*torch.pi*hz*k*timeline+phase) for k in range(1,5))
        else:
            z=torch.randn(length//16+1,device=device)
            color=F.interpolate(z[None,None],size=length,mode='linear',align_corners=False)[0,0]
            color=color/color.square().mean().sqrt().clamp_min(1e-9)
            x=.55*color+.2*torch.randn(length,device=device)+.3*torch.sin(2*torch.pi*float(rng.choice([50,60,16000/208]))*timeline)+float(rng.uniform(-.3,.3))
        return x*(rms/x.square().mean().sqrt().clamp_min(1e-9))
    history=[];start=time.perf_counter()
    print('ROBUST_TRAIN_READY',len(data),STEPS,flush=True)
    for step in range(STEPS):
        x,y=data[int(rng.integers(len(data)))];offset=int(rng.integers(max(1,len(x)-length+1)))
        xx=F.pad(x[offset:offset+length],(0,max(0,length-len(x[offset:offset+length]))))
        yy=F.pad(y[offset:offset+length],(0,max(0,length-len(y[offset:offset+length]))))
        desired_rms=float(np.exp(rng.uniform(np.log(.003),np.log(.10))))
        level=xx.square().mean().sqrt().clamp_min(.0001)
        normalized=(xx*(desired_rms/level)).clamp(-.95,.95)
        snr_db=float(rng.uniform(8,30));noise_level=float(normalized.square().mean().sqrt())/10**(snr_db/20)
        noisy=(normalized+noise(noise_level,int(rng.integers(1,5)))).clamp(-1,32767/32768)
        quiet_kind=step%5;quiet_rms=float(np.exp(rng.uniform(np.log(.00005),np.log(.02))))
        source=torch.stack([normalized,noisy,noise(quiet_rms,quiet_kind)])
        target=torch.stack([yy,yy]);spoken_clean=torch.stack([xx,xx])[:,warm:]
        prediction=model(source[:,None])[:,0].float();assert torch.isfinite(prediction).all()
        fake=prediction[:2,warm:];quiet=prediction[2,warm:];real=target[:,warm:]
        adversarial=step>=400
        if adversarial:
            for p in discs.parameters():p.requires_grad_(True)
            do.zero_grad(set_to_none=True);dl=0
            for disc in discs:
                a,_=disc(real[:,None]);b,_=disc(fake.detach()[:,None]);dl+=((a-1)**2).mean()+b.square().mean()
            dl.backward();torch.nn.utils.clip_grad_norm_(discs.parameters(),5);do.step()
        for p in discs.parameters():p.requires_grad_(False)
        go.zero_grad(set_to_none=True)
        spectral=objective.loss(fake,real)
        with torch.no_grad():ref=content(F.layer_norm(spoken_clean,spoken_clean.shape[-1:])).last_hidden_state
        features=content(F.layer_norm(fake,fake.shape[-1:])).last_hidden_state
        cl=F.l1_loss(features,ref)
        identity=1-(speaker.embedding(fake)*reference).sum(dim=-1).mean()
        quiet_loss=quiet.abs().mean()/.005+quiet.square().mean()/.0001
        gl=torch.tensor(0.,device=device);fm=torch.tensor(0.,device=device)
        if adversarial:
            for disc in discs:
                score,maps=disc(fake[:,None]);gl+=((score-1)**2).mean()
                with torch.no_grad():_,truth=disc(real[:,None])
                fm+=sum(F.l1_loss(a,b) for a,b in zip(maps,truth))/len(maps)
        consistency=F.l1_loss(fake[1],fake[0].detach())
        loss=5*spectral+12*cl+.75*identity+6*quiet_loss+2*consistency+(.15*gl+.5*fm if adversarial else 0)
        assert torch.isfinite(loss);loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),5.)
        assert torch.isfinite(grad);go.step()
        if step%49==0 or step==STEPS-1:
            row=dict(step=step+1,loss=float(loss.detach()),spectral=float(spectral.detach()),content=float(cl.detach()),
                     identity=float(identity.detach()),consistency=float(consistency.detach()),snr_db=snr_db,speech_input_rms=float(normalized.square().mean().sqrt()),quiet_loss=float(quiet_loss.detach()),quiet_kind=quiet_kind,
                     quiet_input_rms=float(source[2].square().mean().sqrt()),quiet_output_rms=float(quiet.detach().square().mean().sqrt()),
                     speech_output_rms=float(fake.detach().square().mean().sqrt()),speech_peak=float(fake.detach().abs().max()),seconds=time.perf_counter()-start)
            history.append(row);print('STEP',json.dumps(row),flush=True)
            (OUT/'training_status.json').write_text(json.dumps(dict(history=history,complete=False),indent=2),encoding='utf-8')
        if (step+1)%400==0:
            torch.save(dict(model={k:v.detach().cpu() for k,v in model.state_dict().items()},config=cfg,steps=step+1,
                       total_after_structural_initialization_steps=9200+step+1,selection=selection,
                       source_enrollment=False,target_quality_accepted=False),OUT/('checkpoint_step'+str(step+1)+'.pt'))
    model=model.cpu().float().eval();export(model,OUT/'small96_noise_aware_step10400.f32')
    outputs=[]
    for row in rows:
        if row['split']=='train':continue
        x=read(row['path']);y=stream(model,x);path=OUT/(row['filename'][:-4]+'_student.wav')
        sf.write(path,y,16000,subtype='FLOAT');outputs.append(dict(row,student_path=str(path),rms=float(np.sqrt(np.mean(y*y))),peak=float(np.max(np.abs(y))),human_acceptance=False))
    report=dict(history=history,complete=True,steps=STEPS,total_after_structural_initialization_steps=10400,
       config=cfg,parameters=sum(p.numel() for p in model.parameters()),heldout_outputs=outputs,
       training_speakers=sorted({r['speaker'] for r in training}),resume_path=str(PARENT),
       parent_checkpoint_sha256=hashlib.sha256(PARENT.read_bytes()).hexdigest(),
       weights_sha256=hashlib.sha256((OUT/'small96_noise_aware_step10400.f32').read_bytes()).hexdigest(),
       source_enrollment=False,target_track9_used_for_training=False,teacher_waveform_time_warp=False,
       auxiliary_speaker_loss_used=True,wespeaker_no_longer_independent_evaluator=True,
       previous_test_speakers_now_diagnostic_only=True,speech_quality_accepted=False,board_live_verified=False,
       silent_target_is_zero=True,quiet_loss='6*(meanabs/0.005+meansquare/0.0001)',content_loss_weight=12,speaker_loss_weight=.75,paired_clean_noisy_consistency_weight=2,
       speech_gain_range=None,speech_desired_rms_range=[.003,.10],speech_augmentation_noise_snr_db=[8,30],
       synthetic_quiet_input_rms_range=[.00005,.02],quiet_kinds=['zero','white','variable_lowpass','50_60_76p9Hz_harmonics','colored_mixture_dc'],
       runtime_noise_gate_added=False,max_cuda_allocated=torch.cuda.max_memory_allocated())
    (OUT/'decision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('ROBUST_TRAIN_AND_DIAGNOSTIC_OUTPUTS_DONE',flush=True)
if __name__=='__main__':main()
