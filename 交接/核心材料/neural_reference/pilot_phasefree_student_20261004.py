"""Small optimization feasibility test, not production target acceptance.

Two genuine development speakers -> fixed-reference natural TTS targets.
Teacher WAVs remain unchanged. Only detached spectral loss features are indexed
by coarse acoustic landmarks. No phase-vocoder or warped waveform is used.
Tiny data, coarse alignment, no adversarial loss, and bulk/stream differences
are explicit limitations. Four held-out speakers are never optimizer inputs.
"""
from load_llvc_audit_model import load_model, BASE, digest
from prepare_aligned_teacher_pilot_20261004 import read_audio
from llvc_online_stream import LLVCAudioStream
from pathlib import Path
import json, time
import torch, numpy as np, soundfile as sf
import torchaudio.functional as AF

OUT=BASE.parent/'board_budget_20261004/phasefree_student_pilot'
OUT.mkdir(exist_ok=True)
TEACHER=Path('D:/总进度/目标人物分析/固定人物多说话人中文回归_2026-10-04')
ALIGN=Path('D:/总进度/目标人物分析/小模型监督对齐试验_2026-10-04')
torch.set_num_threads(4)

class SpectralObjective:
    def __init__(self,device):
        self.device=device
        self.hop=160
        self.windows={n:torch.hann_window(n,device=device) for n in [512,1024]}
        self.fb={n:AF.melscale_fbanks(n//2+1,50,7600,80,16000,norm='slaney',mel_scale='slaney').to(device) for n in self.windows}

    def features(self,wave,n):
        D=torch.stft(wave,n_fft=n,hop_length=self.hop,window=self.windows[n],return_complex=True)
        return (D.abs().square().T@self.fb[n]).clamp_min(1e-10).log()

    def aligned_targets(self,source,teacher,sk,tk):
        result={}
        with torch.no_grad():
            for n in self.windows:
                teacher_features=self.features(teacher,n)
                source_frames=1+len(source)//self.hop
                times=np.arange(source_frames)*self.hop/16000
                mapped=np.interp(times,sk,tk)*16000/self.hop
                lo=np.floor(mapped).astype('int64')
                lo=np.clip(lo,0,len(teacher_features)-1)
                hi=np.clip(lo+1,0,len(teacher_features)-1)
                fraction=torch.tensor(mapped-np.floor(mapped),device=self.device,dtype=torch.float32)[:,None]
                y=teacher_features[torch.tensor(lo,device=self.device)]*(1-fraction)+teacher_features[torch.tensor(hi,device=self.device)]*fraction
                outside=(times<sk[0])|(times>sk[-1])
                y[torch.tensor(outside,device=self.device)]=np.log(1e-10)
                result[n]=y.detach()
        return result

    def loss(self,wave,target):
        return sum(torch.nn.functional.l1_loss(self.features(wave,n),target[n]) for n in self.windows)/len(self.windows)


def stream(model,wave):
    s=LLVCAudioStream(model);chunks=[]
    for t in range(0,len(wave),256):chunks.extend(s.feed(wave[t:t+256]))
    chunks.extend(s.finish());y=np.concatenate(chunks)
    assert len(y)==len(wave) and np.isfinite(y).all()
    return y


def main():
    torch.manual_seed(20261004);np.random.seed(20261004)
    assert torch.cuda.is_available()
    device=torch.device('cuda');obj=SpectralObjective(device)
    # Feature alignment identity must match actual unmodified spectral features.
    tone=.1*torch.sin(2*torch.pi*220*torch.arange(16000,device=device)/16000)
    identity=obj.aligned_targets(tone,tone,[0,1],[0,1])
    for n in identity:assert torch.allclose(identity[n],obj.features(tone,n),atol=1e-5)
    x=tone.clone().requires_grad_();loss=obj.loss(x, {n:v+.1 for n,v in identity.items()})
    loss.backward();assert torch.isfinite(x.grad).all() and x.grad.abs().max()>0
    rows=json.loads((TEACHER/'evaluation_items.json').read_text(encoding='utf8'))
    landmarks=json.loads((ALIGN/'decision.json').read_text(encoding='utf8'))['cases']
    plan=[r for r in rows if r['source_split']=='development'];held=[r for r in rows if r['source_split']=='heldout_speaker']
    assert len(plan)==2 and len(held)==4 and not ({r['speaker_id'] for r in plan}&{r['speaker_id'] for r in held})
    data=[]
    for row in plan:
        assert digest(row['source_path'])==row['source_sha256'] and digest(row['path'])==row['sha256']
        l=next(z for z in landmarks if z['label']==row['label'])
        source=torch.tensor(read_audio(row['source_path']),device=device)
        teacher=torch.tensor(read_audio(row['path']),device=device)
        # Use natural teacher only. Never read *_aligned_teacher.wav.
        targets=obj.aligned_targets(source,teacher,l['source_knots'],l['teacher_knots'])
        data.append(dict(row=row,source=source,target=targets))
    model,config=load_model();model.to(device).eval()
    before=[]
    with torch.no_grad():
        for d in data:
            y=model(d['source'][None,None])[0,0]
            before.append(float(obj.loss(y,d['target'])))
    optimizer=torch.optim.AdamW(model.parameters(),lr=2e-5,weight_decay=0)
    history=[];start=time.perf_counter();torch.cuda.reset_peak_memory_stats()
    # Fixed steps, no held-out selection or hyperparameter sweep.
    for step in range(20):
        d=data[step%len(data)];optimizer.zero_grad(set_to_none=True)
        y=model(d['source'][None,None])[0,0]
        loss=obj.loss(y,d['target']);assert torch.isfinite(loss)
        loss.backward()
        assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
        norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        optimizer.step()
        history.append(dict(step=step+1,label=d['row']['label'],loss=float(loss.detach()),gradient_norm=float(norm)))
        if step%2==1:print('STEP',step+1,'loss',history[-1]['loss'],flush=True)
    torch.cuda.synchronize()
    after=[]
    with torch.no_grad():
        for d in data:
            y=model(d['source'][None,None])[0,0]
            after.append(float(obj.loss(y,d['target'])))
    path=OUT/'checkpoint_step20.pt'
    torch.save(dict(model={k:v.detach().cpu() for k,v in model.state_dict().items()},
                    steps=20,source_enrollment=False,production_approved=False),path)
    stats=dict(status='finite_phasefree_optimization_pilot_finished',train_loss_before=before,train_loss_after=after,
        history=history,seconds=time.perf_counter()-start,peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
        checkpoint_path=str(path),checkpoint_sha256=digest(path),base_checkpoint_sha256=digest(BASE/'llvc_pretrained_audit/G_500000.pth'),
        training_speakers=[r['speaker_id'] for r in plan],heldout_speakers=[r['speaker_id'] for r in held],
        teacher_wavs_changed=False,phase_vocoder_used=False,teacher_audio_time_warp_used=False,
        loss_only_spectral_index_alignment=True,alignment_coarse_60ms=True,
        target_track9_used_for_training=False,target_reference_sha256=plan[0]['reference_sha256'],
        teacher_text_outputs_not_all_human_accepted=True,no_adversarial_loss=True,
        bulk_training_stream_quality_not_proven=True,training_data_only_two_utterances=True,
        human_target_voice_accepted=False,pronunciation_accepted=False,board_deployed=False,
        quantized_runtime=False,training_does_not_prove_unseen_speaker_generalization=True)
    model.cpu().eval();base,_=load_model();eval_rows=[]
    for row in held:
        assert digest(row['source_path'])==row['source_sha256']
        source=read_audio(row['source_path'])
        baseline=stream(base,source);candidate=stream(model,source)
        candidates=[]
        for label,wave in [('baseline',baseline),('candidate',candidate)]:
            output=OUT/(row['label']+'_'+label+'.wav')
            sf.write(output,wave,16000,subtype='FLOAT')
            candidates.append(dict(kind=label,path=str(output),sha256=digest(output),seconds=len(wave)/16000,
                rms=float(np.sqrt(np.mean(wave*wave))),peak=float(np.max(np.abs(wave))),human_acceptance=False))
        eval_rows.append(dict(row,streaming_outputs=candidates))
        print('HELDOUT_STREAM',row['label'],flush=True)
    stats['heldout_streaming_evaluation']=eval_rows
    for row in plan:assert digest(row['path'])==row['sha256']
    (OUT/'decision.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
    print('PHASEFREE PILOT COMPLETE',flush=True)


if __name__=='__main__':main()
