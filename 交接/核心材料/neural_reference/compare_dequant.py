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
# C's quantized input
cq = np.fromfile(t/"enc3_qin.bin", dtype=np.uint8).reshape(13,512)
xq = torch.from_numpy(cq).view(torch.int8)
# activation scale from the dense input
rawin = np.fromfile(t/"enc3_before.bin", dtype=np.float32).reshape(13,512)
rt = torch.from_numpy(rawin)
sx = rt.abs().amax()/127.0
print("python sx", float(sx))

conv = net.mask_gen.encoder.dcc_layers[3].layers[3]
wq, sw = Q.quantize_per_channel_w(conv.weight)
yq = torch.matmul(xq.to(torch.int32), wq.t().to(torch.int32))
y = yq.float() * (float(sx)*sw.squeeze(1)) + conv.bias
# [13,512]

# C pwout
cp = np.fromfile(t/"dbg_dcc3_pwout.bin", dtype=np.float32).reshape(13,512)
d = np.abs(y.numpy()-cp)
print("pwout maxdiff", float(d.max()))
# compare sw
csw = np.fromfile(t/"enc3_sw.bin", dtype=np.float32) if (t/"enc3_sw.bin").exists() else None
print("sw shape", sw.shape, "bias first", float(conv.bias[0]))
bad = np.argwhere(d>0.001)
for fr,j in bad[:10]:
    print("frame",fr,"ch",j,"py",round(float(y[fr,j]),5),"C",round(float(cp[fr,j]),5))
