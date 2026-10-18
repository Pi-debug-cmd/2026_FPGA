"""Comprehensive evaluation of best frozen checkpoint on held-out sources."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json
import numpy as np, torch
import torch.nn.functional as F
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
CORPUS = BUD/"full_train_corpus_16k"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
import librosa, soundfile as sf

CKPT = BUD/"frozen_mask_student/checkpoint_step1600.pt"
m = json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
net,cfg=load_model(False)
net.load_state_dict(torch.load(CKPT,map_location="cpu",weights_only=True)["model"],strict=True)
net=net.to("cuda").eval()

def flat_of(y):
    return float(np.median(librosa.feature.spectral_flatness(y=y,n_fft=1024,hop_length=160)))

# evaluate on validation (held-out) sources
rows=[]
for e in m["validation"]:
    src=np.fromfile(e["src"],dtype="<f4"); tch=np.fromfile(e["tch"],dtype="<f4")
    with torch.no_grad():
        o=net(torch.tensor(src,device="cuda")[None,None])[0,0].cpu().numpy()
    rows.append(dict(stem=e["stem"],flat=flat_of(o),tch_flat=flat_of(tch),
                     src_flat=flat_of(src),rms=float(np.sqrt(np.mean(o**2)))))
print("held-out validation:")
for r in rows:
    print("  %s flat=%.4f tch=%.4f src=%.4f rms=%.3f"%(r["stem"],r["flat"],r["tch_flat"],r["src_flat"],r["rms"]))
print("mean student flat %.4f, mean teacher flat %.4f"%(np.mean([r["flat"] for r in rows]),np.mean([r["tch_flat"] for r in rows])))

# identity cos via frozen speaker
sys.path.insert(0,str(NR))
from differentiable_speaker_20261005 import FrozenSpeaker
spk=FrozenSpeaker()
def emb(y):
    return spk.embedding(torch.tensor(y))
target=read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
te=emb(target)
coses=[]
for e in m["validation"]:
    src=np.fromfile(e["src"],dtype="<f4")
    with torch.no_grad():
        o=net(torch.tensor(src,device="cuda")[None,None])[0,0].cpu().numpy()
    cos=float(F.cosine_similarity(emb(o),te).item())
    coses.append(cos)
print("held-out target cos: mean %.3f, range %.3f-%.3f"%(np.mean(coses),min(coses),max(coses)))
# f0
f0s=[]
for e in m["validation"]:
    src=np.fromfile(e["src"],dtype="<f4")
    with torch.no_grad():
        o=net(torch.tensor(src,device="cuda")[None,None])[0,0].cpu().numpy()
    f,_,_=librosa.pyin(o,fmin=60,fmax=500,sr=16000); f=f[~np.isnan(f)]
    f0s.append(np.median(f))
print("held-out f0 median %.1f (target ~200)"%np.mean(f0s))
