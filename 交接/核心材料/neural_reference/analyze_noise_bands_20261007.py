"""Analyze residual noise frequency content in the best student vs teacher."""
import numpy as np, librosa, json
from pathlib import Path
BUD = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005")
best = BUD/"official_multires_student/fixed_sentence_step1600.wav"
teacher = Path(r"D:\总进度\全尺寸学生试听_2026-10-06\3_教师CV3转换.wav")
target = Path(r"D:\总进度\全尺寸学生试听_2026-10-06\1_目标人物原声.wav")
def band_energy(p):
    y,sr=librosa.load(p,sr=16000)
    S=np.abs(librosa.stft(y,n_fft=1024,hop_length=160))
    freqs=librosa.fft_frequencies(sr=16000,n_fft=1024)
    bands=[(0,500),(500,1000),(1000,2000),(2000,4000),(4000,8000)]
    out=[]
    total=S.sum()
    for lo,hi in bands:
        m=(freqs>=lo)&(freqs<hi)
        out.append(S[m].sum()/total)
    return out
for name,p in [("target",target),("teacher",teacher),("student",best)]:
    print(name, ["%.4f"%v for v in band_energy(p)])
