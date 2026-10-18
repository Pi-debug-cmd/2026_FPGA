"""Controlled reduced-student v3 experiment: 2-second segments, same board architecture and losses."""
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
from build_reduced_bias_20261009 import build_net_bias as build_net

m=json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
train=[(np.fromfile(e["src"],dtype="<f4"),np.fromfile(e["tch"],dtype="<f4")) for e in m["train"]]
anchors=[np.fromfile(a["path"],dtype="<f4") for a in m["anchors"]]
FIXED=BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--steps",type=int,default=800)
    ap.add_argument("--idw",type=float,default=8.0)
    ap.add_argument("--out",default="reduced_student_bias_content_v1")
    args=ap.parse_args()
    OUT=BUD/args.out; OUT.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(1234); rng=np.random.default_rng(31337); device="cuda"
    net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json').to(device)
    start=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)['model']
    missing,unexpected=net.load_state_dict(start,strict=False)
    assert missing==["timbre_bias"] and not unexpected,(missing,unexpected)
    hub=HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"),local_files_only=True).to(device).eval()
    hub.encoder.layers=nn.ModuleList(hub.encoder.layers[:9])
    for p in hub.parameters(): p.requires_grad_(False)
    mr=auraloss.freq.MultiResolutionSTFTLoss(scale="mel",sample_rate=16000,device=device,
        fft_sizes=[1024,2048,512],hop_sizes=[120,240,50],
        win_lengths=[600,1200,240],n_bins=80).to(device)
    from differentiable_speaker_20261005 import FrozenSpeaker
    spk=FrozenSpeaker().to(device).eval()
    tgt=read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
    te=spk.embedding(torch.tensor(tgt,device=device))
    SEG=32000
    def fe(w): return hub(F.layer_norm(w,w.shape[-1:])).last_hidden_state
    def fixed_out():
        net.eval()
        with torch.no_grad(): o=net(torch.tensor(read(str(FIXED)),device=device)[None,None])[0,0].cpu().numpy()
        net.train(); return o
    def metrics(o):
        fl=float(np.median(librosa.feature.spectral_flatness(y=o,n_fft=1024,hop_length=160)))
        co=float(F.cosine_similarity(spk.embedding(torch.tensor(o,device=device)),te).item())
        return fl,co
    for p in net.convnet_pre.parameters(): p.requires_grad_(False)
    for p in net.in_conv.parameters(): p.requires_grad_(False)
    mg=[p for p in net.mask_gen.parameters()]; oc=[p for p in net.out_conv.parameters()]
    opt=torch.optim.AdamW([{"params":mg,"lr":4e-5},{"params":oc,"lr":1.5e-5},{"params":[net.timbre_bias],"lr":2e-4}],betas=(.8,.999),eps=1e-9)
    for step in range(args.steps):
        if step%2==0:
            xs=[];ys=[]
            for _ in range(1):
                x,y=train[int(rng.integers(len(train)))]
                at=int(rng.integers(max(1,len(x)-SEG+1)))
                xs.append(np.pad(x[at:at+SEG],(0,SEG-min(SEG,len(x)-at))))
                ys.append(np.pad(y[at:at+SEG],(0,SEG-min(SEG,len(y)-at))))
            source=torch.tensor(np.stack(xs),device=device); teacher=torch.tensor(np.stack(ys),device=device)
            pred=net(source[:,None])[:,0].float()
            with torch.no_grad(): source_content=fe(source)
            content=F.l1_loss(fe(pred),source_content); mel=mr(pred[:,None],teacher[:,None])
            e=spk.embedding(pred)
            idl=1-F.cosine_similarity(e,te.expand(e.shape[0],-1),dim=-1).mean()
            loss=40*content+10*mel+args.idw*idl
            if step==0: print("PAIR_LOSSES",float(content),float(40*content),float(mel),float(10*mel),float(idl),float(args.idw*idl),flush=True)
        else:
            xs=[]
            for _ in range(1):
                a=anchors[int(rng.integers(len(anchors)))]
                at=int(rng.integers(max(1,len(a)-SEG+1)))
                xs.append(np.pad(a[at:at+SEG],(0,SEG-min(SEG,len(a)-at))))
            source=torch.tensor(np.stack(xs),device=device)
            pred=net(source[:,None])[:,0].float()
            mel=mr(pred[:,None],source[:,None])
            e=spk.embedding(pred)
            idl=1-F.cosine_similarity(e,te.expand(e.shape[0],-1),dim=-1).mean()
            loss=10*mel+args.idw*idl
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
        if (step+1)%200==0 or step==args.steps-1:
            o=fixed_out(); fl,co=metrics(o)
            print("step%d flat=%.5f cos=%.3f"%(step+1,fl,co),flush=True)
            if (step+1)%400==0 or step==args.steps-1:
                sf.write(OUT/("fixed_step%d.wav"%(step+1)),o,16000)
                torch.save(dict(model=net.state_dict(),step=step+1,flat=fl,cos=co),
                           OUT/("checkpoint_step%d.pt"%(step+1)))
    o=fixed_out(); fl,co=metrics(o)
    sf.write(OUT/"final_fixed.wav",o,16000)
    torch.save(dict(model=net.state_dict(),flat=fl,cos=co),OUT/"final.pt")
    print("FINAL flat=%.5f cos=%.3f bias_max=%.6f"%(fl,co,float(net.timbre_bias.detach().abs().max())),flush=True); print("DONE",flush=True)

if __name__=="__main__":
    main()





