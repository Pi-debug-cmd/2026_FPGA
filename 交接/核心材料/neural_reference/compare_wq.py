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

# Save fresh wq for layer 3 BEFORE replacement
orig = net.mask_gen.encoder.dcc_layers[3].layers[3]
fresh_wq, fresh_sw = Q.quantize_per_channel_w(orig.weight)
fresh_bias = orig.bias.detach().clone()

# Now replace as in ref_block3
for i in range(8):
    cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
    net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)

qd = net.mask_gen.encoder.dcc_layers[3].layers[3]
print("wq maxdiff", float((qd.wq - fresh_wq).abs().max()))
print("sw maxdiff", float((qd.sw - fresh_sw.squeeze(1)).abs().max()))
print("bias maxdiff", float((qd.bias - fresh_bias).abs().max()))
