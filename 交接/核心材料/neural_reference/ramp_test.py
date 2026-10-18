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

# Ramp test: input[i] = i
ramp = np.arange(240, dtype=np.float32)
x = torch.tensor(ramp).reshape(1,1,-1)
with torch.inference_mode():
    y = net.in_conv[0](x).numpy().reshape(13,512)
w = net.in_conv[0].weight.detach().numpy().reshape(512,48)
yMan = np.zeros((13,512), dtype=np.float32)
for tt in range(13):
    yMan[tt] = w @ ramp[tt*16:tt*16+48]
print("ramp: net vs manual maxdiff:", np.abs(y-yMan).max())
# Constant input test: all = 1
c1 = np.ones(240, dtype=np.float32)
x1 = torch.tensor(c1).reshape(1,1,-1)
with torch.inference_mode():
    y1 = net.in_conv[0](x1).numpy().reshape(13,512)
y1m = np.zeros((13,512), dtype=np.float32)
for tt in range(13):
    y1m[tt] = w @ c1[tt*16:tt*16+48]
print("const1: net vs manual maxdiff:", np.abs(y1-y1m).max())
print("const1 net frame0 first 3:", y1[0,:3], "manual:", y1m[0,:3])
