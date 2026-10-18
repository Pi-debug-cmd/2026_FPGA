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

# impulse at position 0, input length 240
imp = torch.zeros(1,1,240); imp[0,0,0]=1.0
with torch.inference_mode():
    y = net.in_conv[0](imp).numpy().reshape(13,512)
w = net.in_conv[0].weight.detach().numpy().reshape(512,48)
# impulse at 0 -> frame0 channel c should equal w[c,0]
print("impulse@0: frame0[c] vs w[c,0] maxdiff:", np.abs(y[0]-w[:,0]).max())
print("frame0 first 5:", y[0,:5], "w[:,0] first 5:", w[:5,0])
# impulse at 16 -> frame1
imp2 = torch.zeros(1,1,240); imp2[0,0,16]=1.0
with torch.inference_mode():
    y2 = net.in_conv[0](imp2).numpy().reshape(13,512)
print("impulse@16: frame1[c] vs w[c,0] maxdiff:", np.abs(y2[1]-w[:,0]).max())
print("frame0 nonzero (should be 0):", (y2[0]!=0).sum())
