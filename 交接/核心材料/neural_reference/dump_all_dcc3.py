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
for i in range(8):
    cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
    net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)

bx = np.fromfile(BASE/"deploy_runtime"/"test"/"input.bin", dtype=np.float32)
L=16; CHUNK=208
tdir = BASE/"deploy_runtime"/"test"/"allref"
import os
os.makedirs(tdir, exist_ok=True)
def dumpCF(t, name):
    t.permute(0,2,1).contiguous().numpy().reshape(-1).astype(np.float32).tofile(name)

enc, dec, outb = net.init_buffers(1, "cpu")
pre = net.convnet_pre.init_ctx_buf(1,"cpu")
front = torch.zeros(32)
pending = np.concatenate([np.empty(0, dtype=np.float32), bx])
nb = 0
while len(pending) >= CHUNK+L:
    shifted = torch.from_numpy(pending[L:L+CHUNK].copy())
    block = torch.cat((front, shifted)).reshape(1,1,-1)
    with torch.inference_mode():
        # manually to get e after DCC3
        cnv, pre = net.convnet_pre(block, pre)
        cn = block + cnv
        x = net.in_conv(cn)
        encmod = net.mask_gen.encoder
        for li in range(8):
            s0 = encmod.buf_indices[li]; s1 = s0 + encmod.buf_lengths[li]
            dcc_in = torch.cat((enc[...,s0:s1], x), dim=-1)
            enc[...,s0:s1] = dcc_in[...,-encmod.buf_lengths[li]:]
            x = x + encmod.dcc_layers[li](dcc_in)
            if li == 3:
                dumpCF(x, os.path.join(tdir, "all_dcc3_%d.bin"%nb))
    front = shifted[-32:].clone()
    pending = pending[CHUNK:].copy()
    nb += 1
print("done", nb)
