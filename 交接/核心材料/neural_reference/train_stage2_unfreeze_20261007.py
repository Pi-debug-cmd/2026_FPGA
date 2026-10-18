"""Stage 2: unfreeze out_conv, push identity while keeping clean.
Start from best frozen checkpoint; train mask_gen + out_conv with low LR.
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json, time, argparse, math
import numpy as np, torch
import torch.nn as nn
import torch.nn.functional as F
import auraloss
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
CORPUS = BUD/"full_train_corpus_16k"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
from transformers import HubertModel
import librosa, soundfile as sf

START_CKPT = BUD/"frozen_mask_student/checkpoint_step1600.pt"
FIXED = BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"
m = json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
train=[]
for e in m["train"]:
    train.append((np.fromfile(e["src"],dtype="<f4"),np.fromfile(e["tch"],dtype="<f4")))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--steps",type=int,default=2000)
    ap.add_argument("--out",default="stage2_unfreeze_student")
    args=ap.parse_args()
    OUT=BUD/args.out; OUT.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(1234); rng=np.random.default_rng(5678)
    device="cuda"

    net,cfg=load_model(False)
    net.load_state_dict(torch.load(START_CKPT,map_location="cpu",weights_only=True)["model"],strict=True)
    net=net.to(device).train()
    for p in net.convnet_pre.parameters(): p.requires_grad_(False)
    for p in net.in_conv.parameters(): p.requires_grad_(False)
    # out_conv now trainable
    mg=[p for p in net.mask_gen.parameters()]; oc=[p for p in net.out_conv.parameters()]
    print("mask params",sum(p.numel() for p in mg),"out params",sum(p.numel() for p in oc),flush=True)

    hub=HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"),local_files_only=True).to(device).eval()
    for p in hub.parameters(): p.requires_grad_(False)
    mr=auraloss.freq.MultiResolutionSTFTLoss(
        scale="mel",sample_rate=16000,device=device,
        fft_sizes=[1024,2048,512],hop_sizes=[120,240,50],
        win_lengths=[600,1200,240],n_bins=80).to(device)
    # mask_gen moderate LR, out_conv very low
    opt=torch.optim.AdamW([
        {"params":mg,"lr":5e-5},
        {"params":oc,"lr":1e-5}],betas=(.8,.999),eps=1e-9)
    SEG=16000; start=time.perf_counter(); hist=[]; best=(9,None)
    def fe(w): return hub.feature_extractor(w)
    sys.path.insert(0,str(NR))
    from differentiable_speaker_20261005 import FrozenSpeaker
    spk=FrozenSpeaker()
    target=read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
    te=spk.embedding(torch.tensor(target))
    def fixed_out():
        net.eval()
        with torch.no_grad():
            o=net(torch.tensor(read(str(FIXED)),device=device)[None,None])[0,0].cpu().numpy()
        net.train(); return o
    def flat_of(y):
        return float(np.median(librosa.feature.spectral_flatness(y=y,n_fft=1024,hop_length=160)))
    def cos_of(y):
        return float(F.cosine_similarity(spk.embedding(torch.tensor(y)),te).item())

    for step in range(args.steps):
        xs=[];ys=[]
        for _ in range(2):
            x,y=train[int(rng.integers(len(train)))]
            at=int(rng.integers(max(1,len(x)-SEG+1)))
            seg=min(SEG,len(x)-at)
            xx=np.pad(x[at:at+seg],(0,SEG-seg)); yy=np.pad(y[at:at+seg],(0,SEG-seg))
            xs.append(torch.tensor(xx,device=device)); ys.append(torch.tensor(yy,device=device))
        source=torch.stack(xs); teacher=torch.stack(ys)
        pred=net(source[:,None])[:,0].float()
        content=F.mse_loss(fe(pred),fe(teacher))
        mel=mr(pred[:,None],teacher[:,None])
        loss=100000*content+10*mel
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
        if step%100==0:
            rec=dict(step=step+1,content=float(content),mel=float(mel),sec=time.perf_counter()-start)
            hist.append(rec)
        if (step+1)%400==0 or step==args.steps-1:
            o=fixed_out(); f=flat_of(o); c=cos_of(o)
            sf.write(OUT/("fixed_sentence_step"+str(step+1)+".wav"),o,16000)
            torch.save(dict(model=net.state_dict(),step=step+1,flat=f,cos=c),OUT/("checkpoint_step"+str(step+1)+".pt"))
            print("CHECK step%d flat=%.5f cos=%.3f"%(step+1,f,c),flush=True)
            if f<0.004 and c>best[0]: best=(c,step+1)
    (OUT/"best.json").write_text(json.dumps(dict(best_cos=best[0],best_step=best[1])))
    print("BEST",best,flush=True); print("DONE",flush=True)

if __name__=="__main__":
    main()
