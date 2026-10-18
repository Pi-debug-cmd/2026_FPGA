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

t = BASE/"deploy_runtime"/"test"
# C's quantized input for M_ENC3 (block4)
cq = np.fromfile(t/"enc3_qin.bin", dtype=np.uint8).reshape(13,512)
xq = torch.from_numpy(cq).view(torch.int8).to(torch.int32)

# Python wq for M_ENC3 (encoder dcc layer 3, pointwise conv = layers[3])
conv = net.mask_gen.encoder.dcc_layers[3].layers[3]
wq, sw = Q.quantize_per_channel_w(conv.weight)
print("wq shape", wq.shape)
yq = torch.matmul(xq, wq.t().to(torch.int32))

# C i32
ci = np.fromfile(t/"enc3_i32.bin", dtype=np.int32).reshape(13,512)
diff = yq.numpy() - ci
print("i32 maxdiff", int(np.abs(diff).max()))
print("n_diff", int(np.sum(diff!=0)))
bad = np.argwhere(diff!=0)
for fr,j in bad[:10]:
    print("frame",fr,"out",j,"python",int(yq[fr,j]),"C",int(ci[fr,j]))
