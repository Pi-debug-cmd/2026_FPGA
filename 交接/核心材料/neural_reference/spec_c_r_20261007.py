"""Spectrogram comparison: C vs R full input, plus per-segment flatness."""
import numpy as np, librosa
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
D=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime")
c=np.fromfile(D/"out_pc_red.bin",dtype="<f4")
r=np.fromfile(D/"dmp_x.bin",dtype="<f4") if (D/"dmp_x.bin").exists() else None
# load R from the compare script output if present; else recompute
import sys
sys.path.insert(0,r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference")
from run_rvc_pilot import settings; settings()
from train_reduced_20261007 import build_net
from llvc_online_stream import LLVCAudioStream
import torch
BUD=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005")
NR=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference")
net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
x=np.fromfile(D/"test/input.bin",dtype="<f4")
st=LLVCAudioStream(net); p=st.feed(x); p+=st.finish(); r=np.concatenate(p)
n=min(len(c),len(r))
fig,ax=plt.subplots(3,1,figsize=(14,9),sharex=True)
for a,(nm,w) in zip(ax,[("input",x),("PyTorch ref",r[:n]),("C",c[:n])]):
    S=librosa.amplitude_to_db(np.abs(librosa.stft(w,n_fft=1024,hop_length=160)),ref=0.5)
    a.imshow(S,aspect="auto",origin="lower",cmap="magma",extent=[0,len(w)/16000,0,8000],vmin=-80,vmax=0)
    a.set_title(nm); a.set_ylabel("Hz")
plt.tight_layout(); plt.savefig(r"D:\总进度\C_vs_R_频谱_20261007.png",dpi=110)
print("saved")
# per-segment flatness
for i in range(0,n,8000):
    if i+8000>n: break
    cf=np.median(librosa.feature.spectral_flatness(y=c[i:i+8000],n_fft=1024,hop_length=160))
    rf=np.median(librosa.feature.spectral_flatness(y=r[i:i+8000],n_fft=1024,hop_length=160))
    print("%.2fs C flat %.4f R flat %.4f"%(i/16000,cf,rf))
