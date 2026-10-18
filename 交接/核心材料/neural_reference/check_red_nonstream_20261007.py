"""Minimal PyTorch check: non-streaming forward of reduced model on speech."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys
BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
sys.path.insert(0,str(NR)); sys.path.insert(0,str(NR/"LLVC"))
import torch, numpy as np
from train_reduced_20261007 import build_net
from train_board_student_20261005 import read

net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True); net.eval()
# take a 1-second speech segment from the input
x=np.fromfile(BASE/"deploy_runtime/test/input.bin",dtype="<f4")
# find a loud region
seg=x[3500:19500]
with torch.inference_mode():
    o=net(torch.tensor(seg)[None,None])[0,0].numpy()
print("input rms %.4f out rms %.4f out max %.4f"%(np.sqrt((seg**2).mean()),
    np.sqrt((o**2).mean()),np.abs(o).max()))
print("out first 16:",np.round(o[:16],4))
