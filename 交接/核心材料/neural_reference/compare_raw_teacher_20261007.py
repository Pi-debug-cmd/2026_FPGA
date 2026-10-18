"""Compare raw G5000 output vs teacher C: waveform correlation, target cosine, f0."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys
import numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"
sys.path.insert(0, str(NR))
from train_board_student_20261005 import read
from differentiable_speaker_20261005 import FrozenSpeaker
import librosa

TARGET_REF = Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
raw_p = r"D:\总进度\raw_G5000_test_20261007\raw_G5000_output.wav"
C_p   = r"D:\总进度\全尺寸学生试听_2026-10-06\3_教师CV3转换.wav"
A_p   = r"D:\总进度\全尺寸学生试听_2026-10-06\1_目标人物原声.wav"

sp = FrozenSpeaker().to("cuda").eval()
with torch.no_grad():
    ref = sp.embedding(torch.tensor(read(str(TARGET_REF)),device="cuda"))
def cos(p):
    x=torch.tensor(read(p),device="cuda")
    with torch.no_grad(): return float((sp.embedding(x[None])*ref).sum())
def f0(p):
    y,_=librosa.load(p,sr=16000)
    f,_,_=librosa.pyin(y,fmin=60,fmax=500,sr=16000); f=f[~np.isnan(f)]
    return float(np.median(f)),float(np.percentile(f,10)),float(np.percentile(f,90))

raw_y,_=librosa.load(raw_p,sr=16000); C_y,_=librosa.load(C_p,sr=16000)
n=min(len(raw_y),len(C_y))
corr=float(np.corrcoef(raw_y[:n],C_y[:n])[0,1])
print("raw vs C waveform corr:", round(corr,4))
for name,p in [("raw G5000",raw_p),("teacher C",C_p),("target A",A_p)]:
    print(name, "cos=%.3f"%cos(p), "f0/p10/p90=", tuple(round(v,1) for v in f0(p)))
