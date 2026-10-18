import numpy as np, librosa
D=r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime"
cf=np.fromfile(D+r"\out_float_full.bin",dtype="<f4")
ci=np.fromfile(D+r"\out_pc_red.bin",dtype="<f4")
# R reference via streaming
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, torch
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
from train_reduced_20261007 import build_net
from llvc_online_stream import LLVCAudioStream
net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
x=np.fromfile(D+r"/test/input.bin",dtype="<f4")
st=LLVCAudioStream(net); p=st.feed(x); p+=st.finish(); r=np.concatenate(p)
def stats(name,c,r):
    n=min(len(c),len(r)); c=c[:n]; r=r[:n]
    flat=np.median(librosa.feature.spectral_flatness(y=c,n_fft=1024,hop_length=160))
    print("%-14s corr %.4f flat %.4f rms %.4f"%(name,np.corrcoef(c,r)[0,1],flat,np.sqrt((c**2).mean())))
stats("C float",cf,r)
stats("C int8",ci,r)
print("R flat %.4f rms %.4f"%(np.median(librosa.feature.spectral_flatness(y=r,n_fft=1024,hop_length=160)),np.sqrt((r**2).mean())))
