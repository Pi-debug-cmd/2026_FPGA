"""Overfit test: can the LLVC cleanly reproduce a handful of teacher pairs?"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json
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
import soundfile as sf

OFFICIAL = NR/"llvc_pretrained_audit/G_500000.pth"
m = json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
# fixed 8 pairs, use full length (not random 2s)
pairs=[]
for e in m["train"][:4]:
    pairs.append((np.fromfile(e["src"],dtype="<f4"),np.fromfile(e["tch"],dtype="<f4")))

net,cfg=load_model(False)
net.load_state_dict(torch.load(OFFICIAL,map_location="cpu",weights_only=True)["model"],strict=True)
net=net.to("cuda").train()
hub=HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"),local_files_only=True).to("cuda").eval()
for p in hub.parameters(): p.requires_grad_(False)
objective=Objective("cuda")
opt=torch.optim.AdamW(net.parameters(),lr=5e-5,betas=(.8,.999),eps=1e-9)
def fe(w): return hub.feature_extractor(w)
def flat_of(y):
    return float(np.median(__import__("librosa").feature.spectral_flatness(y=y,n_fft=1024,hop_length=160)))

# pad each pair to 2s (32000), divisible by 16
N=32000
batch_x=[]; batch_y=[]
for x,y in pairs:
    # take the middle 2s
    c=min(len(x),len(y))//2
    sx=x[c:c+N]; sy=y[c:c+N]
    if len(sx)<N: sx=np.pad(sx,(0,N-len(sx)))
    if len(sy)<N: sy=np.pad(sy,(0,N-len(sy)))
    batch_x.append(sx); batch_y.append(sy)
source=torch.tensor(np.stack(batch_x),device="cuda")
teacher=torch.tensor(np.stack(batch_y),device="cuda")
print("N",N,"batch",tuple(source.shape),flush=True)

for step in range(2000):
    pred=net(source[:,None])[:,0].float()
    content=F.mse_loss(fe(pred),fe(teacher))
    mel=objective.loss(pred,teacher)
    wave=F.l1_loss(pred,teacher)
    loss=100000*content+10*mel+5*wave
    opt.zero_grad(); loss.backward()
    torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
    if step%100==0 or step==1999:
        print("step %d mel=%.3f content=%.6f wave=%.4f"%(step,mel,content,wave),flush=True)
# final: save first pair output
net.eval()
with torch.no_grad():
    o=net(source[0,None,None])[0,0].cpu().numpy()
sf.write(r"D:\总进度\overfit_test_20261007.wav",o,16000)
print("final flat",flat_of(o),"teacher flat",flat_of(teacher[0].cpu().numpy()),flush=True)
