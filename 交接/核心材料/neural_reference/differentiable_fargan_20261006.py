"""Frozen FARGAN training surrogate. Final outputs must use quantized native C.

Deterministic float activations, frozen official weights; not bit-exact int8 C.
Only training runs on PC. No recognition/TTS or reference waveform in runtime.
"""
from pathlib import Path
import sys, torch
import torchaudio.functional as AF
BASE=Path(__file__).resolve().parent
ROOT=BASE/'Opus_FARGAN_reference/opus-main/dnn'
sys.path.insert(0,str(ROOT/'torch/fargan'))
import fargan

class FrozenFargan(torch.nn.Module):
    def __init__(self,truncate_frames=0):
        super().__init__()
        checkpoint=torch.load(ROOT/'models/fargan_sq1Ab_adv_50.pth',map_location='cpu',weights_only=False)
        self.model=fargan.FARGAN(*checkpoint['model_args'],**checkpoint['model_kwargs'])
        self.model.load_state_dict(checkpoint['state_dict'],strict=True)
        self.model.eval()
        for p in self.model.parameters():p.requires_grad_(False)
        # Official training always adds random activation noise, even in eval.
        # Disable it explicitly for a reproducible, smooth training surrogate.
        fargan.n=lambda x:x.clamp(-1,1)
        self.truncate_frames=truncate_frames
    def forward(self,features):
        count=features.shape[1]
        # Five copies preload the conditioner; two zero PCM frames warm GRUs.
        # One extra final frame permits exact output length after 80-sample trim.
        padded=torch.cat([features[:,:1].expand(-1,5,-1),features,features[:,-1:].expand(-1,2,-1)],dim=1)
        period=torch.round(256/torch.pow(2,padded[...,18]+1.5)).clamp(32,255).long()
        if not self.truncate_frames:
            signal,_=self.model(padded,period,count+1,pre=features.new_zeros((features.shape[0],320)))
        else:
            # Preserve the entire forward signal/state, but stop long unstable
            # autoregressive gradients every80ms. This is training only.
            batch=features.shape[0];prev=features.new_zeros((batch,256));exc=prev.clone()
            states=tuple(features.new_zeros((batch,n)) for n in [160,128,128,164])
            cond=self.model.cond_net(padded,period);pieces=[]
            for n in range(1,count+3):
                if (n-1)%self.truncate_frames==0:
                    prev=prev.detach();exc=exc.detach();states=tuple(s.detach() for s in states)
                for k in range(4):
                    block,exc,prev,states=self.model.sig_net(cond[:,n,k*80:(k+1)*80],prev,exc,period[:,3+n],states)
                    if n<2:exc=torch.cat([exc[:,:-40],torch.zeros_like(block)],dim=1)
                    else:pieces.append(block)
            signal=torch.cat(pieces,dim=1)
        # Native continuation sets the de-emphasis memory to zero after warmup.
        signal=AF.lfilter(signal,signal.new_tensor([1.,-.85]),signal.new_tensor([1.,0.]),clamp=False)
        return signal[:,80:80+count*160]

if __name__=='__main__':
    from run_rvc_pilot import settings
    settings()
    import numpy as np,json,time,subprocess,soundfile as sf
    torch.set_num_threads(4)
    budget=BASE.parent/'board_budget_20261005';native=BASE.parent/'board_support/native_llvc_20261005'
    out=budget/'fargan_proxy_verification';out.mkdir(exist_ok=True)
    manifest=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'))
    row=next(r for r in manifest['files'] if r['split']=='validation')
    feat=np.fromfile(row['teacher_features'],dtype='float32').reshape(-1,20)[:160].copy()
    model=FrozenFargan().cuda();x=torch.tensor(feat,device='cuda')[None].requires_grad_(True)
    start=time.monotonic();y=model(x);loss=y.square().mean();loss.backward()
    assert torch.isfinite(y).all() and torch.isfinite(x.grad).all() and x.grad[...,1:18].abs().max()>0
    actual=y.detach().cpu().numpy()[0];sf.write(out/'proxy.wav',actual,16000,subtype='FLOAT')
    f=out/'features.f32';feat.tofile(f)
    for kind in ['fp32','int8']:
        exe=native/('fargan_probe_fp32_host.exe' if kind=='fp32' else 'fargan_probe_host.exe')
        subprocess.run([str(exe),'--synthesis',str(f),str(out/(kind+'.pcm')),str(out/(kind+'.json'))],check=True)
    report=dict(complete=True,finite_waveform=True,finite_feature_gradient=True,gradient_max=float(x.grad.abs().max()),seconds=time.monotonic()-start,gpu_peak_bytes=torch.cuda.max_memory_allocated(),int8_bit_exact_claim=False,frozen_weights=True,quality_accepted=False)
    for kind in ['fp32','int8']:
        gold=np.fromfile(out/(kind+'.pcm'),dtype='<i2').astype('float32')/32768
        report[kind]=dict(nrmse=float(np.linalg.norm(actual-gold)/max(np.linalg.norm(gold),1e-9)),rms_proxy=float(np.sqrt(np.mean(actual**2))),rms_c=float(np.sqrt(np.mean(gold**2))))
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
