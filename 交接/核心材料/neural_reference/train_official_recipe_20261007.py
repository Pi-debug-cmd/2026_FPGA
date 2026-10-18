"""Official-recipe target adaptation of full LLVC.

Faithful to LLVC train.py loss balance: fairseq-style HuBERT CNN feature
MSE (weight 100000, dominant content anchor) + multires mel (weight 10).
No GAN initially; grad clip 1.0. This keeps the clean G_5000 structure while
the mel loss moves timbre to the target. The prior failure used weak content
(1-2) + strong identity (3), which distorted the model.
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json, time, argparse
import numpy as np, torch
import torch.nn as nn
import torch.nn.functional as F
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
CORPUS = BUD/"full_train_corpus_16k"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import Objective, read
from transformers import HubertModel

OFFICIAL = NR/"llvc_pretrained_audit/G_500000.pth"
FIXED = BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"

m = json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
train=[]
for e in m["train"]:
    train.append((np.fromfile(e["src"],dtype="<f4"),np.fromfile(e["tch"],dtype="<f4")))
val=[]
for e in m["validation"]:
    val.append((e["stem"],np.fromfile(e["src"],dtype="<f4"),np.fromfile(e["tch"],dtype="<f4")))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--steps",type=int,default=3000)
    ap.add_argument("--out",default="official_recipe_student")
    ap.add_argument("--lr",type=float,default=1e-4)
    ap.add_argument("--content_w",type=float,default=100000)
    args=ap.parse_args()
    OUT=BUD/args.out; OUT.mkdir(parents=True,exist_ok=True)
    torch.manual_seed(20261007); rng=np.random.default_rng(20261007)
    device="cuda"

    net,cfg=load_model(False)
    net.load_state_dict(torch.load(OFFICIAL,map_location="cpu",weights_only=True)["model"],strict=True)
    net=net.to(device).train()
    print("params",sum(p.numel() for p in net.parameters()),flush=True)

    hub=HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"),local_files_only=True).to(device).eval()
    for p in hub.parameters(): p.requires_grad_(False)
    objective=Objective(device)
    opt=torch.optim.AdamW(net.parameters(),lr=args.lr,betas=(.8,.999),eps=1e-9)
    SEG=32000; start=time.perf_counter(); hist=[]
    def fe(w): return hub.feature_extractor(w)

    def fixed_out():
        net.eval()
        with torch.no_grad():
            o=net(torch.tensor(read(str(FIXED)),device=device)[None,None])[0,0].cpu().numpy()
        net.train(); return o
    def flat_of(y):
        return float(np.median(__import__("librosa").feature.spectral_flatness(y=y,n_fft=1024,hop_length=160)))

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
        mel=objective.loss(pred,teacher)
        loss=args.content_w*content+10*mel
        opt.zero_grad(); loss.backward()
        gn=torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
        if step%50==0 or step==args.steps-1:
            rec=dict(step=step+1,loss=float(loss),content=float(content),mel=float(mel),
                     cw=float(args.content_w*content),gn=float(gn),sec=time.perf_counter()-start)
            hist.append(rec); print("STEP",json.dumps(rec),flush=True)
            (OUT/"training_status.json").write_text(json.dumps(dict(hist=hist)))
        if (step+1)%400==0 or step==args.steps-1:
            o=fixed_out()
            import soundfile as sf
            sf.write(OUT/("fixed_sentence_step"+str(step+1)+".wav"),o,16000)
            print("CHECK step%d flat=%.5f"%(step+1,flat_of(o)),flush=True)
    print("OFFICIAL_RECIPE_DONE",flush=True)

if __name__=="__main__":
    main()
