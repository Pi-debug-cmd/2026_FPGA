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
print("cn dtype", cn.dtype, "contiguous", cn.flags['C_CONTIGUOUS'])
# Variant A: from_numpy
xA = torch.from_numpy(cn).reshape(1,1,-1)
# Variant B: clone float tensor
xB = torch.tensor(cn, dtype=torch.float32).reshape(1,1,-1)
with torch.inference_mode():
    yA = net.in_conv[0](xA).numpy().reshape(13,512)
    yB = net.in_conv[0](xB).numpy().reshape(13,512)
w = net.in_conv[0].weight.detach().numpy().reshape(512,48)
yMan = np.zeros((13,512), dtype=np.float32)
for tt in range(13): yMan[tt] = w @ cn[tt*16:tt*16+48]
print("A vs manual:", np.abs(yA-yMan).max())
print("B vs manual:", np.abs(yB-yMan).max())
print("A vs B:", np.abs(yA-yB).max())
