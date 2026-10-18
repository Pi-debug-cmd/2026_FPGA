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
c_in = np.fromfile(t/"dbg_outin.bin", dtype=np.float32).reshape(17,512)
x = torch.from_numpy(c_in).permute(1,0).unsqueeze(0)
with torch.inference_mode():
    y = net.out_conv(x).squeeze().numpy()
    lin = net.out_conv[0](x).squeeze().numpy()
print("Python outconv on C outin RMS", float(np.sqrt(np.mean(y**2))))
cout = np.fromfile(t/"cout.bin", dtype=np.float32)[22*208:23*208]
print("C output RMS", float(np.sqrt(np.mean(cout**2))))
print("maxdiff", float(np.abs(y-cout).max()))
print("pre-tanh RMS", float(np.sqrt(np.mean(lin**2))), "max", float(np.abs(lin).max()))
