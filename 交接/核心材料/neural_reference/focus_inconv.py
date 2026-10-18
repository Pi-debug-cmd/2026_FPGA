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

t = BASE/"deploy_runtime"/"test"
cn = np.fromfile(t/"dbg_cn.bin", dtype=np.float32)
x = torch.from_numpy(cn).reshape(1,1,-1)
with torch.inference_mode():
    y = net.in_conv(x).numpy().reshape(13,512)

w = net.in_conv[0].weight.detach().numpy().reshape(512,48)
manual = np.zeros((13,512), dtype=np.float32)
for tt in range(13):
    seg = cn[tt*16:tt*16+48]
    manual[tt] = w @ seg
manual = np.maximum(manual, 0)
print("net.in_conv vs manual maxdiff:", np.abs(y-manual).max())
print("y frame0 first 10:", y[0,:10])
print("manual frame0 first 10:", manual[0,:10])
# Is the conv padding the input? check conv's padding
print("conv padding:", net.in_conv[0].padding, "stride:", net.in_conv[0].stride,
      "kernel:", net.in_conv[0].kernel_size)
