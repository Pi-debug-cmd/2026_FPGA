from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, numpy as np, torch
BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"; OUT = BUD/"full_target_student"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import read
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

# replicate LLVCAudioStream block loop
enc, dec, outb = net.init_buffers(1, "cpu")
pre = net.convnet_pre.init_ctx_buf(1,"cpu")
front = torch.zeros(32)
pending = np.empty(0, dtype=np.float32)
nb = 0
pending = np.concatenate([pending, bx])
while len(pending) >= CHUNK+L:
    shifted = torch.from_numpy(pending[L:L+CHUNK].copy())
    block = torch.cat((front, shifted)).reshape(1,1,-1)
    nb += 1
    if nb == 22:
        # dump block 22 encoder state (after blocks 0-21), frame-major [510,512]
        enc.permute(0,2,1).contiguous().numpy().reshape(-1).astype(np.float32).tofile(tdir/"p22_encstate.bin")
        # dump block 22 stages
        with torch.inference_mode():
            cnv, pre2 = net.convnet_pre(block, pre)
            cn = block + cnv
            cn.numpy().reshape(-1).astype(np.float32).tofile(tdir/"p22_cn.bin")
            x = net.in_conv(cn)
            dumpCF(x, "p22_inconv.bin")
            # manually run encoder layer by layer on a COPY, dump e after each
            enc_d = enc.clone()
            xd = x.clone()
            encmod = net.mask_gen.encoder
            for li in range(8):
                s0 = encmod.buf_indices[li]; s1 = s0 + encmod.buf_lengths[li]
                dcc_in = torch.cat((enc_d[...,s0:s1], xd), dim=-1)
                enc_d[...,s0:s1] = dcc_in[...,-encmod.buf_lengths[li]:]
                xd = xd + encmod.dcc_layers[li](dcc_in)
                dumpCF(xd, "p22_dcc_%d.bin"%li)
            e = xd
            dumpCF(e, "p22_dcc.bin")
            label = torch.zeros(1,1)
            l = net.label_embedding(label); l = l.unsqueeze(2)*e
            dumpCF(l, "p22_l.bin")
            em = net.mask_gen.proj_e2d_e(e)
            tm = net.mask_gen.proj_e2d_l(l)
            dumpCF(em, "p22_mem.bin"); dumpCF(tm, "p22_tgt.bin")
    with torch.inference_mode():
        speech, enc, dec, outb, pre = net(block, enc, dec, outb, pre, pad=False)
    front = shifted[-32:].clone()
    pending = pending[CHUNK:].copy()
print("processed blocks", nb)
