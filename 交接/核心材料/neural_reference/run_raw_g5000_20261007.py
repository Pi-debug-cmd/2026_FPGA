"""Run raw official G_5000 (no fine-tune) on the fixed input, save + analyze."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json
import numpy as np
import torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
import soundfile as sf

B = Path(str(BUD)+r"\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
OUT = Path(r"D:\总进度\raw_G5000_test_20261007"); OUT.mkdir(parents=True, exist_ok=True)

net, cfg = load_model(True)  # load official G_5000
net = net.to("cuda").eval()
bx = read(str(B))
with torch.no_grad():
    raw = net(torch.tensor(bx, device="cuda")[None,None])[0,0].cpu().numpy()
sf.write(OUT/"raw_G5000_output.wav", raw, 16000)
print("raw out len", len(raw), "rms", float(np.sqrt((raw**2).mean())),
      "peak", float(np.abs(raw).max()))
# also load the teacher CV3 and student and compare simple metrics
import librosa
def qmet(p):
    y,_=librosa.load(p,sr=16000)
    flat=np.median(librosa.feature.spectral_flatness(y=y,n_fft=1024,hop_length=160))
    n=len(y)//208
    fr=np.array([np.sqrt((y[i*208:(i+1)*208]**2).mean()+1e-10) for i in range(n)])
    d=np.abs(np.diff(fr))/(fr[:-1]+1e-6)
    return flat, float(np.median(d)), float(np.percentile(d,90))
print("raw G5000  flat/jump/jump90", qmet(str(OUT/"raw_G5000_output.wav")))
print("teacher C ", qmet(r"D:\总进度\全尺寸学生试听_2026-10-06\3_教师CV3转换.wav"))
print("student D ", qmet(r"D:\总进度\全尺寸学生试听_2026-10-06\4_全尺寸学生转换.wav"))
print("target A  ", qmet(r"D:\总进度\全尺寸学生试听_2026-10-06\1_目标人物原声.wav"))
