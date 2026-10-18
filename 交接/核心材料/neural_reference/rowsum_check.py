from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()

W = net.in_conv[0].weight.detach().numpy()
print("weight shape", W.shape)
# row sums over k (axis=2)
rowsum = W.reshape(512,48).sum(axis=1)
print("rowsum first 5:", rowsum[:5])
print("rowsum all equal?", np.abs(rowsum-rowsum[0]).max())
c1 = torch.ones(1,1,240)
with torch.inference_mode():
    y = net.in_conv[0](c1).numpy().reshape(13,512)
print("conv frame0 first 5:", y[0,:5])
print("conv vs rowsum maxdiff:", np.abs(y[0]-rowsum).max())
