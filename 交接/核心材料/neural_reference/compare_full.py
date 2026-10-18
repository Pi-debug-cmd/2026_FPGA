from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR))
from load_llvc_audit_model import load_model
import quant_sim_20261006 as Q

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
for p in net.parameters(): p.requires_grad_(False)

t = BASE/"deploy_runtime"/"test"
# Compare dense inputs
c_before = np.fromfile(t/"enc3_before.bin", dtype=np.float32).reshape(13,512)
r_densein = np.fromfile(t/"ref_dcc3_densein.bin", dtype=np.float32).reshape(13,512)
print("C enc3_before vs ref_dcc3_densein maxdiff", float(np.abs(c_before-r_densein).max()))

# Now run the QuantizedDense on the C's before
qd = Q.QuantizedDense(net.mask_gen.encoder.dcc_layers[3].layers[3])
x = torch.from_numpy(c_before).permute(1,0).unsqueeze(0)  # [1,512,13]
y = qd(x).squeeze(0).permute(1,0).numpy()  # [13,512]

c_pwout = np.fromfile(t/"dbg_dcc3_pwout.bin", dtype=np.float32).reshape(13,512)
print("QuantizedDense(C before) vs C pwout maxdiff", float(np.abs(y-c_pwout).max()))

r_pwout = np.fromfile(t/"ref_dcc3_pwout.bin", dtype=np.float32).reshape(13,512)
print("QuantizedDense(C before) vs ref_pwout maxdiff", float(np.abs(y-r_pwout).max()))
