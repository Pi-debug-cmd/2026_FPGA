from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
import torch.nn as nn
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()

# fresh conv with same weights
fresh = nn.Conv1d(1,512,48,stride=16,bias=False)
with torch.no_grad(): fresh.weight.copy_(net.in_conv[0].weight)

c1 = torch.ones(1,1,240)
with torch.inference_mode():
    yn = net.in_conv[0](c1).numpy().reshape(13,512)
    yf = fresh(c1).numpy().reshape(13,512)
print("const1 net vs fresh maxdiff:", np.abs(yn-yf).max())
print("net frame0 first 3:", yn[0,:3], "fresh:", yf[0,:3])
