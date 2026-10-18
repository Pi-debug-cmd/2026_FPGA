from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
import quant_sim_20261006 as Q

net, _ = load_model(False)
ck = torch.load(OUT/"checkpoint_step3000.pt", map_location="cpu", weights_only=True)
net.load_state_dict(ck["model"], strict=True); net.eval()
for i in range(8):
    cell = net.mask_gen.encoder.dcc_layers[i].layers[3]
    net.mask_gen.encoder.dcc_layers[i].layers[3] = Q.QuantizedDense(cell)
layer = net.mask_gen.decoder.tf_dec_layers[0]
layer.self_attn = Q.QuantizedMHA(layer.self_attn)
layer.multihead_attn = Q.QuantizedMHA(layer.multihead_attn)
layer.linear1 = Q.QuantizedDense(layer.linear1)
layer.linear2 = Q.QuantizedDense(layer.linear2)

bx = np.fromfile(BASE/"deploy_runtime"/"test"/"input.bin", dtype=np.float32)
L=16; CHUNK=208
tdir = BASE/"deploy_runtime"/"test"
def dumpCF(t, name):
    t.permute(0,2,1).contiguous().numpy().reshape(-1).astype(np.float32).tofile(tdir/name)

enc, dec, outb = net.init_buffers(1, "cpu")
pre = net.convnet_pre.init_ctx_buf(1,"cpu")
front = torch.zeros(32)
pending = np.concatenate([np.empty(0, dtype=np.float32), bx])
nb = 0
while len(pending) >= CHUNK+L:
    shifted = torch.from_numpy(pending[L:L+CHUNK].copy())
    block = torch.cat((front, shifted)).reshape(1,1,-1)
    nb += 1
    with torch.inference_mode():
        # full forward but capture out_conv input
        cnv, pre = net.convnet_pre(block, pre)
        cn = block + cnv
        x = net.in_conv(cn)
        lab = torch.zeros(1,1)
        l = net.label_embedding(lab)
        m, enc, dec = net.mask_gen(x, l, enc, dec)
        x2 = x * m
        x3 = torch.cat((outb, x2), dim=-1)
        outb = x3[..., -net.out_buf_len:]
        if nb == 22:
            dumpCF(x3, "q22_outconv_in.bin")
            y = net.out_conv(x3)
            y.numpy().reshape(-1).astype(np.float32).tofile(tdir/"q22_outconv_out.bin")
            print("dumped outconv in/out")
    front = shifted[-32:].clone()
    pending = pending[CHUNK:].copy()
    if nb == 22: break
