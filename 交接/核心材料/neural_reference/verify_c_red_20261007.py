"""Verify C PC-reference reduced output: flatness, cos, and correlation vs PyTorch."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, numpy as np, librosa
from train_board_student_20261005 import read

c_out=np.fromfile(BASE/"deploy_runtime/out_pc_red.bin",dtype="<f4")
print("C out len %d rms %.4f"%(len(c_out),np.sqrt((c_out**2).mean())))
print("C flat %.5f"%float(np.median(librosa.feature.spectral_flatness(
    y=c_out,n_fft=1024,hop_length=160))))
from differentiable_speaker_20261005 import FrozenSpeaker
import torch.nn.functional as F
spk=FrozenSpeaker().to("cuda").eval()
tgt=read(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")
te=spk.embedding(torch.tensor(tgt,device="cuda"))
print("C cos %.4f"%float(F.cosine_similarity(
    spk.embedding(torch.tensor(c_out,device="cuda")),te).item()))
