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

B = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav")
bx = read(str(B)); L=16
front = torch.zeros(2*L); shifted = torch.from_numpy(bx[L:L+208].copy())
block = torch.cat((front, shifted)).reshape(1,1,-1)
tdir = BASE/"deploy_runtime"/"test"
def dumpCF(t, name):
    t.permute(0,2,1).contiguous().numpy().reshape(-1).astype(np.float32).tofile(tdir/name)
with torch.inference_mode():
    enc_buf, dec_buf, out_buf = net.init_buffers(1, "cpu")
    pre = net.convnet_pre.init_ctx_buf(1,"cpu")
    cnv, pre = net.convnet_pre(block, pre)
    cn = block + cnv
    x = net.in_conv(cn)
    e, enc_buf = net.mask_gen.encoder(x, enc_buf)
    label = torch.zeros(1,1)
    l = net.label_embedding(label); l = l.unsqueeze(2)*e
    em = net.mask_gen.proj_e2d_e(e)
    tm = net.mask_gen.proj_e2d_l(l)
    m, dec_buf = net.mask_gen.decoder(tm, em, dec_buf)
    m = net.mask_gen.proj_d2e(m)
    m = l + m
    outin = torch.cat((out_buf, e*m), dim=-1)
dumpCF(l, "q_l.bin"); dumpCF(em, "q_mem.bin"); dumpCF(tm, "q_tgt.bin"); dumpCF(outin, "q_outin.bin")
print("wrote quantized decoder intermediates")
