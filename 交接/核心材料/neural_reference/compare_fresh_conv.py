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

# fresh reference conv with copied weights
ref = nn.Conv1d(1,512,48,stride=16,padding=0,bias=False)
with torch.no_grad():
    ref.weight.copy_(net.in_conv[0].weight)
imp = torch.zeros(1,1,240); imp[0,0,0]=1.0
with torch.inference_mode():
    y_net = net.in_conv[0](imp).numpy().reshape(13,512)
    y_ref = ref(imp).numpy().reshape(13,512)
print("net frame0 nonzero:", (y_net[0]!=0).sum())
print("ref frame0 nonzero:", (y_ref[0]!=0).sum())
print("net vs ref maxdiff:", np.abs(y_net-y_ref).max())
# inspect the module type and any forward override
print("type:", type(net.in_conv[0]))
print("weight shape:", tuple(net.in_conv[0].weight.shape))
