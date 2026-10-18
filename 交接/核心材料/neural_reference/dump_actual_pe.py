from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch, math
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
dec = net.mask_gen.decoder
x = torch.zeros(1,26,256)
pe = dec.pos_enc(x).numpy().reshape(26,256)
# C-style PE
cpe = np.zeros((26,256), dtype=np.float32)
for t in range(26):
    for i in range(0,256,2):
        arg = t*math.exp(math.log(10000)*(-i)/256)
        cpe[t,i]=math.sin(arg); cpe[t,i+1]=math.cos(arg)
print("speechbrain PE vs C PE maxdiff:", np.abs(pe-cpe).max())
print("sb frame1 first 6:", pe[1,:6])
print("C  frame1 first 6:", cpe[1,:6])
