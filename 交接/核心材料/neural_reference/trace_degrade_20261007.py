"""Trace how fast quality degrades after 0,1,10,50,100,200,400 optimizer steps."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json
import numpy as np, torch
import torch.nn.functional as F
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import Objective, read
from differentiable_speaker_20261005 import FrozenSpeaker
from transformers import HubertModel
import torch.nn as nn

CORPUS = BUD/"full_train_corpus_16k"
OFFICIAL = NR/"llvc_pretrained_audit/G_500000.pth"
FIXED = BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"
TARGET_REF = Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")

m = json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
train=[]
for e in m["train"]:
    train.append((np.fromfile(e["src"],dtype="<f4"),np.fromfile(e["tch"],dtype="<f4")))
anchors=[torch.tensor(np.fromfile(e["path"],dtype="<f4"),device="cuda") for e in m["anchors"]]

net,cfg = load_model(False)
net.load_state_dict(torch.load(OFFICIAL,map_location="cpu",weights_only=True)["model"],strict=True)
net=net.to("cuda")
objective=Objective("cuda")
hub=HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"),local_files_only=True).to("cuda").eval()
hub.encoder.layers=nn.ModuleList(hub.encoder.layers[:9])
for p in hub.parameters(): p.requires_grad_(False)
speaker=FrozenSpeaker().to("cuda").eval()
with torch.no_grad():
    ref_emb=speaker.embedding(torch.tensor(read(str(TARGET_REF)),device="cuda"))
opt=torch.optim.AdamW(net.parameters(),lr=1e-5,betas=(.8,.99))
SEG=32000; rng=np.random.default_rng(1)

def hf(w): return hub(F.layer_norm(w,w.shape[-1:])).last_hidden_state
def fixed_out():
    net.eval()
    with torch.no_grad():
        o=net(torch.tensor(read(str(FIXED)),device="cuda")[None,None])[0,0].cpu().numpy()
    net.train()
    return o
def flat_of(y):
    return float(np.median(__import__("librosa").feature.spectral_flatness(y=y,n_fft=1024,hop_length=160)))

def step():
    xs=[];ys=[]
    for _ in range(2):
        x,y=train[int(rng.integers(len(train)))]
        at=int(rng.integers(max(1,len(x)-SEG+1)))
        seg=min(SEG,len(x)-at)
        xx=np.pad(x[at:at+seg],(0,SEG-seg)); yy=np.pad(y[at:at+seg],(0,SEG-seg))
        xs.append(torch.tensor(xx,device="cuda")); ys.append(torch.tensor(yy,device="cuda"))
    source=torch.stack(xs); teacher=torch.stack(ys)
    anc=anchors[int(rng.integers(len(anchors)))]
    at=int(rng.integers(max(1,len(anc)-SEG+1)))
    seg=min(SEG,len(anc)-at); aclip=F.pad(anc[at:at+seg],(0,SEG-seg))
    batch=torch.cat([source,aclip[None]])
    pred=net(batch[:,None])[:,0].float()
    fake=pred[:2]; af=pred[2:3]
    spectral=objective.loss(fake,teacher)
    wave=(fake-teacher).abs().mean()/teacher.abs().mean().clamp_min(1e-3)
    with torch.no_grad(): sh=hf(source)
    content=F.l1_loss(hf(fake),sh)
    ident=1-(speaker.embedding(fake)*ref_emb).sum(dim=-1).mean()
    am=objective.loss(af,aclip[None]); aw=(af-aclip[None]).abs().mean()/aclip.abs().mean().clamp_min(1e-3)
    loss=5*spectral+3*wave+1*content+1*ident+1*am+1*aw
    opt.zero_grad(); loss.backward(); gn=torch.nn.utils.clip_grad_norm_(net.parameters(),5); opt.step()
    return float(loss),float(gn)

checks=[0,1,10,50,100,200,400]
ci=0
o=fixed_out(); print("step 0 flat=%.5f rms=%.4f"%(flat_of(o),np.sqrt((o**2).mean())),flush=True)
for s in range(1,401):
    l,gn=step()
    if s in checks:
        o=fixed_out(); print("step %d flat=%.5f rms=%.4f loss=%.2f grad=%.2f"%(s,flat_of(o),np.sqrt((o**2).mean()),l,gn),flush=True)
