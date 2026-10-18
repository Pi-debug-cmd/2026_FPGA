"""Fine-tune reduced model: recover clean conversion then identity, stage3 recipe."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, ast, json, zipfile, time, argparse
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
CORPUS=BUD/"full_train_corpus_16k"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, torch.nn as nn, math
import torch.nn.functional as F
import numpy as np, auraloss, librosa, soundfile as sf
from transformers import HubertModel
from train_board_student_20261005 import read

def build_net(config_path):
    wheel=NR/'dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as z:
        text=z.read('speechbrain/lobes/models/transformer/Transformer.py').decode()
    cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='PositionalEncoding')
    ns=dict(torch=torch,nn=nn,math=math,__name__='r')
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'w','exec'),ns)
    t=ast.parse((NR/'LLVC/model.py').read_text())
    t.body=[n for n in t.body if not (isinstance(n,ast.ImportFrom) and n.module=='speechbrain.lobes.models.transformer.Transformer')]
    nspace=dict(PositionalEncoding=ns['PositionalEncoding'],__name__='llvc_n')
    exec(compile(t,str(NR/'LLVC/model.py'),'exec'),nspace)
    cfg=json.loads(Path(config_path).read_text())
    return nspace['Net'](**cfg['model_params']).eval()

m=json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
train=[(np.fromfile(e["src"],dtype="<f4"),np.fromfile(e["tch"],dtype="<f4")) for e in m["train"]]
anchors=[np.fromfile(a["path"],dtype="<f4") for a in m["anchors"]]
FIXED=BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--p1",type=int,default=1200)
    ap.add_argument("--p2",type=int,default=1400)
    ap.add_argument("--out",default="reduced_student")
    args=ap.parse_args()
    OUT=BUD/args.out; OUT.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(1234); rng=np.random.default_rng(9012); device="cuda"
    net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json').to(device)
    init=torch.load(BUD/'reduced_init/reduced_init.pt',map_location='cpu',weights_only=True)['model']
    net.load_state_dict(init,strict=True)
    hub=HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"),local_files_only=True).to(device).eval()
    for p in hub.parameters(): p.requires_grad_(False)
    mr=auraloss.freq.MultiResolutionSTFTLoss(scale="mel",sample_rate=16000,device=device,
        fft_sizes=[1024,2048,512],hop_sizes=[120,240,50],
        win_lengths=[600,1200,240],n_bins=80).to(device)
    from differentiable_speaker_20261005 import FrozenSpeaker
    spk=FrozenSpeaker().to(device).eval()
    tgt=read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
    te=spk.embedding(torch.tensor(tgt,device=device))
    SEG=16000
    def fe(w): return hub.feature_extractor(w)
    def fixed_out():
        net.eval()
        with torch.no_grad(): o=net(torch.tensor(read(str(FIXED)),device=device)[None,None])[0,0].cpu().numpy()
        net.train(); return o
    def metrics(o):
        fl=float(np.median(librosa.feature.spectral_flatness(y=o,n_fft=1024,hop_length=160)))
        co=float(F.cosine_similarity(spk.embedding(torch.tensor(o,device=device)),te).item())
        return fl,co
    def sample_conv():
        xs=[];ys=[]
        for _ in range(2):
            x,y=train[int(rng.integers(len(train)))]
            at=int(rng.integers(max(1,len(x)-SEG+1)))
            xs.append(np.pad(x[at:at+SEG],(0,SEG-min(SEG,len(x)-at))))
            ys.append(np.pad(y[at:at+SEG],(0,SEG-min(SEG,len(y)-at))))
        return torch.tensor(np.stack(xs),device=device),torch.tensor(np.stack(ys),device=device)
    def sample_anchor():
        xs=[]
        for _ in range(2):
            a=anchors[int(rng.integers(len(anchors)))]
            at=int(rng.integers(max(1,len(a)-SEG+1)))
            xs.append(np.pad(a[at:at+SEG],(0,SEG-min(SEG,len(a)-at))))
        return torch.tensor(np.stack(xs),device=device)

    def run_phase(phase, steps, lr_mg, lr_oc):
        for p in net.convnet_pre.parameters(): p.requires_grad_(False)
        for p in net.in_conv.parameters(): p.requires_grad_(False)
        for p in net.out_conv.parameters(): p.requires_grad_(phase==2)
        mg=[p for p in net.mask_gen.parameters() if p.requires_grad]
        groups=[{"params":mg,"lr":lr_mg}]
        if phase==2: groups.append({"params":net.out_conv.parameters(),"lr":lr_oc})
        opt=torch.optim.AdamW(groups,betas=(.8,.999),eps=1e-9)
        for step in range(steps):
            if step%2==0:
                source,teacher=sample_conv()
                pred=net(source[:,None])[:,0].float()
                content=F.mse_loss(fe(pred),fe(teacher)); mel=mr(pred[:,None],teacher[:,None])
                e=spk.embedding(pred)
                idl=1-F.cosine_similarity(e,te.expand(e.shape[0],-1),dim=-1).mean()
                loss=100000*content+10*mel+3*idl
            else:
                source=sample_anchor()
                pred=net(source[:,None])[:,0].float()
                mel=mr(pred[:,None],source[:,None])
                e=spk.embedding(pred)
                idl=1-F.cosine_similarity(e,te.expand(e.shape[0],-1),dim=-1).mean()
                loss=10*mel+3*idl
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
            if (step+1)%200==0 or step==steps-1:
                o=fixed_out(); fl,co=metrics(o)
                print("PH%d step%d flat=%.5f cos=%.3f"%(phase,step+1,fl,co),flush=True)
                if (step+1)%400==0 or step==steps-1:
                    sf.write(OUT/("p%d_fixed_step%d.wav"%(phase,step+1)),o,16000)
                    torch.save(dict(model=net.state_dict(),step=step+1,flat=fl,cos=co),
                               OUT/("p%d_checkpoint_step%d.pt"%(phase,step+1)))
    t0=time.perf_counter()
    run_phase(1,args.p1,1.5e-4,0)
    run_phase(2,args.p2,5e-5,2e-5)
    o=fixed_out(); fl,co=metrics(o)
    sf.write(OUT/"final_fixed.wav",o,16000)
    torch.save(dict(model=net.state_dict(),flat=fl,cos=co),OUT/"final.pt")
    print("FINAL flat=%.5f cos=%.3f sec=%.0f"%(fl,co,time.perf_counter()-t0),flush=True)
    print("DONE",flush=True)

if __name__=="__main__":
    main()
