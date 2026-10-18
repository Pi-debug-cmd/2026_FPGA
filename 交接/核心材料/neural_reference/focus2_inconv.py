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
    raw = net.in_conv[0](x).numpy().reshape(13,512)
w = net.in_conv[0].weight.detach().numpy().reshape(512,48)
manual = np.zeros((13,512), dtype=np.float32)
for tt in range(13):
    seg = cn[tt*16:tt*16+48]
    manual[tt] = w @ seg
print("raw vs manual maxdiff:", np.abs(raw-manual).max())
print("raw frame0 first 8:", raw[0,:8])
print("manual frame0 first 8:", manual[0,:8])
print("raw frame12 first 5:", raw[12,:5])
print("manual frame12 first 5:", manual[12,:5])
# Where does manual frame0 nonzero come from? input cn[0:48]
print("cn[0:48] nonzero count:", (cn[0:48]!=0).sum(), "maxabs", np.abs(cn[0:48]).max())
print("raw frame0 nonzero count:", (raw[0]!=0).sum())
